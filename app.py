"""
Main Flask application
"""
import os
import re
from flask import Flask, request, session, redirect, url_for, render_template, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from database import Database
from utils import (
    check_db_name, is_api_request, blacklist_extension,
    get_subdir, get_filename, write_log, generate_token,
    xsrf_token, t9n, builtin_value, format_date
)

app = Flask(__name__, template_folder='templates_python')
app.config.from_object(Config)
CORS(app, origins=Config.CORS_ALLOW_ORIGIN,
     allow_headers=Config.CORS_ALLOW_HEADERS,
     methods=Config.CORS_ALLOW_METHODS)


@app.before_request
def before_request():
    """Handle pre-request processing"""
    # Handle OPTIONS requests
    if request.method == 'OPTIONS':
        return '', 200

    # Set up database name from URL
    path_parts = request.path.strip('/').split('/')
    db_name = path_parts[0] if path_parts and path_parts[0] else 'ideav'

    # Handle API requests
    if path_parts and path_parts[0] == 'api':
        if len(path_parts) > 1:
            db_name = path_parts[1]
        else:
            return jsonify({"error": "No DB provided"}), 400

    # Validate database name
    if not check_db_name(Config.DB_MASK, db_name):
        return redirect(url_for('login_page', error='InvalidDB'))

    # Store database name in request context
    request.db_name = db_name

    # Set up session locale
    if 'locale' not in session:
        session['locale'] = request.cookies.get(f'{db_name}_locale',
                                                request.cookies.get('my_locale', 'EN'))


@app.route('/')
@app.route('/<db_name>')
def index(db_name='ideav'):
    """Main index page"""
    if not check_db_name(Config.DB_MASK, db_name):
        return redirect(url_for('login_page', error='InvalidDB'))

    # Check authentication
    token = request.cookies.get(db_name)
    if not token or not verify_token(db_name, token):
        return redirect(url_for('login_page', db=db_name))

    return render_template('main.html', db_name=db_name)


@app.route('/login')
def login_page():
    """Login page"""
    error = request.args.get('error', '')
    db_name = request.args.get('db', 'ideav')
    return render_template('info.html', error=error, db_name=db_name)


@app.route('/<db_name>/object/<int:obj_id>')
def view_object(db_name, obj_id):
    """View an object"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        obj = db.get_record(db_name, obj_id)
        if not obj:
            return "Object not found", 404

        # Get object children
        children = db.get_records(db_name, {'up': obj_id})

        return render_template('object.html',
                             obj=obj,
                             children=children,
                             db_name=db_name)


@app.route('/<db_name>/edit_obj/<int:obj_id>', methods=['GET', 'POST'])
def edit_object(db_name, obj_id):
    """Edit an object"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        if request.method == 'POST':
            # Handle form submission
            obj = db.get_record(db_name, obj_id)
            if not obj:
                return "Object not found", 404

            # Check if metadata (cannot edit)
            if obj['up'] == 0:
                return "Cannot update meta-data", 403

            # Update object value
            new_val = request.form.get(f't{obj["t"]}', '')
            if new_val != obj['val']:
                db.update_val(db_name, obj_id, new_val)

            # Handle file uploads
            for key, file in request.files.items():
                if file and file.filename:
                    t = int(key[1:]) if key.startswith('t') else 0
                    if t > 0:
                        handle_file_upload(db, db_name, obj_id, t, file)

            return redirect(url_for('view_object', db_name=db_name, obj_id=obj_id))

        # GET request - show edit form
        obj = db.get_record(db_name, obj_id)
        if not obj:
            return "Object not found", 404

        # Get object children for editing
        children = db.get_records(db_name, {'up': obj_id})

        return render_template('edit_obj.html',
                             obj=obj,
                             children=children,
                             db_name=db_name)


@app.route('/<db_name>/report/<int:report_id>')
def view_report(db_name, report_id):
    """View a report"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        # Get report definition
        report = db.get_record(db_name, report_id)
        if not report:
            return "Report not found", 404

        # Execute report query (simplified)
        # In full implementation, this would build and execute SQL from report definition
        results = []

        return render_template('report.html',
                             report=report,
                             results=results,
                             db_name=db_name)


@app.route('/<db_name>/upload', methods=['GET', 'POST'])
def upload_file(db_name):
    """Handle file uploads"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400

        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400

        if file:
            # Check file extension
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if blacklist_extension(ext):
                return t9n("[RU]Недопустимый тип файла![EN]Wrong file extension!"), 400

            # Save file
            with Database(db_name) as db:
                # Create upload record
                record_id = db.insert(db_name, 1, 1, Config.FILE, file.filename)

                # Save physical file
                subdir = get_subdir(record_id)
                os.makedirs(subdir, exist_ok=True)

                filename = get_filename(record_id) + '.' + ext
                file.save(os.path.join(subdir, filename))

                return redirect(url_for('index', db_name=db_name))

    return render_template('upload.html', db_name=db_name)


@app.route('/<db_name>/download/<int:file_id>')
def download_file(db_name, file_id):
    """Download a file"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        file_record = db.get_record(db_name, file_id)
        if not file_record:
            return "File not found", 404

        # Get file path
        subdir = get_subdir(file_id)
        filename = file_record['val']
        ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
        physical_filename = get_filename(file_id) + '.' + ext

        return send_from_directory(subdir, physical_filename, as_attachment=True, download_name=filename)


@app.route('/<db_name>/_m_del/<int:obj_id>', methods=['POST'])
def delete_object(db_name, obj_id):
    """Delete an object"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        obj = db.get_record(db_name, obj_id)
        if not obj:
            return "Object not found", 404

        # Check if metadata (cannot delete)
        parent = db.get_record(db_name, obj['up'])
        if parent and parent['up'] == 0:
            return t9n("[RU]Нельзя удалить метаданные[EN]You can't delete metadata"), 403

        # Delete object and its children
        db.delete(db_name, obj_id)

        return redirect(url_for('index', db_name=db_name))


@app.route('/api/<db_name>/objects', methods=['GET', 'POST'])
def api_objects(db_name):
    """API endpoint for objects with filtering support"""
    if request.method == 'GET':
        with Database(db_name) as db:
            limit = request.args.get('limit', Config.DEFAULT_LIMIT, type=int)
            offset = request.args.get('offset', 0, type=int)

            # Check for filters in request or session
            filters = None
            save_filters = request.args.get('save_filters', 'true').lower() == 'true'

            # Parse filters from query parameters
            # Format: filter[field_id][filter_type]=value
            # Example: filter[3][F]=test&filter[13][FR]=0&filter[13][TO]=100
            parsed_filters = {}
            for key, value in request.args.items():
                if key.startswith('filter['):
                    # Extract field_id and filter_type from filter[field_id][filter_type]
                    import re
                    match = re.match(r'filter\[(\d+)\]\[(\w+)\]', key)
                    if match:
                        field_id = int(match.group(1))
                        filter_type = match.group(2)

                        if field_id not in parsed_filters:
                            parsed_filters[field_id] = {}
                        parsed_filters[field_id][filter_type] = value

            # Use parsed filters if provided, otherwise check session
            if parsed_filters:
                filters = parsed_filters
                if save_filters:
                    # Save filters to session
                    session[f'{db_name}_filters'] = filters
            elif f'{db_name}_filters' in session:
                filters = session[f'{db_name}_filters']

            # Clear filters if requested
            if request.args.get('clear_filters') == 'true':
                if f'{db_name}_filters' in session:
                    del session[f'{db_name}_filters']
                filters = None

            # Get objects with optional filtering
            if filters:
                objects = db.get_records_filtered(
                    db_name,
                    filters=filters,
                    limit=limit,
                    offset=offset
                )
            else:
                objects = db.get_records(db_name, limit=limit, offset=offset)

            return jsonify({
                'objects': objects,
                'filters': filters,
                'count': len(objects)
            })

    elif request.method == 'POST':
        data = request.get_json()
        with Database(db_name) as db:
            record_id = db.insert(
                db_name,
                data.get('up', 1),
                data.get('ord', 1),
                data.get('t', 3),
                data.get('val', '')
            )
            return jsonify({'id': record_id}), 201


@app.route('/api/<db_name>/objects/<int:obj_id>', methods=['GET', 'PUT', 'DELETE'])
def api_object(db_name, obj_id):
    """API endpoint for single object"""
    with Database(db_name) as db:
        if request.method == 'GET':
            obj = db.get_record(db_name, obj_id)
            if not obj:
                return jsonify({'error': 'Object not found'}), 404
            return jsonify(obj)

        elif request.method == 'PUT':
            data = request.get_json()
            obj = db.get_record(db_name, obj_id)
            if not obj:
                return jsonify({'error': 'Object not found'}), 404

            if 'val' in data:
                db.update_val(db_name, obj_id, data['val'])

            return jsonify({'id': obj_id, 'success': True})

        elif request.method == 'DELETE':
            obj = db.get_record(db_name, obj_id)
            if not obj:
                return jsonify({'error': 'Object not found'}), 404

            db.delete(db_name, obj_id)
            return jsonify({'success': True})


def verify_auth(db_name):
    """Verify user authentication"""
    token = request.cookies.get(db_name)
    return token and verify_token(db_name, token)


def verify_token(db_name, token):
    """Verify authentication token"""
    try:
        with Database(db_name) as db:
            # Find user with this token
            query = f"""
                SELECT u.id as uid, u.val as username, t.id as tok
                FROM `{db_name}` u
                JOIN `{db_name}` t ON t.up = u.id AND t.t = {Config.TOKEN}
                WHERE u.t = {Config.USER} AND t.val = %s
            """
            result = db.execute_one(query, (token,))
            if result:
                session['user_id'] = result['uid']
                session['user_name'] = result['username']
                return True
    except Exception as e:
        write_log(f"Token verification error: {e}", "error", db_name)

    return False


def handle_file_upload(db, db_name, obj_id, field_type, file):
    """Handle file upload for an object field"""
    if not file or not file.filename:
        return

    # Check file extension
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if blacklist_extension(ext):
        raise ValueError(t9n("[RU]Недопустимый тип файла![EN]Wrong file extension!"))

    # Create or update file record
    existing = db.execute_one(
        f"SELECT id FROM `{db_name}` WHERE up = %s AND t = %s",
        (obj_id, field_type)
    )

    if existing:
        record_id = existing['id']
        db.update_val(db_name, record_id, file.filename)
    else:
        record_id = db.insert(db_name, obj_id, 1, field_type, file.filename)

    # Save physical file
    subdir = get_subdir(record_id)
    os.makedirs(subdir, exist_ok=True)

    filename = get_filename(record_id) + '.' + ext
    file.save(os.path.join(subdir, filename))


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('info.html', error='Page not found'), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return render_template('info.html', error='Internal server error'), 500


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.LOGS_DIR, exist_ok=True)

    # Run application
    app.run(host='0.0.0.0', port=5000, debug=True)
