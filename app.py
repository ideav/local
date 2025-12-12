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
from report_compiler import ReportCompiler
from utils import (
    check_db_name, is_api_request, blacklist_extension,
    get_subdir, get_filename, write_log, generate_token,
    xsrf_token, t9n, builtin_value, format_date
)
from permissions import PermissionSystem, PermissionError, get_permission_system
from export_import import ExportImport

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


@app.route('/<db_name>/object/<int:obj_id>')
def view_object(db_name, obj_id):
    """View an object"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    # Get permission system
    perm_sys = get_permission_system(db_name)
    if not perm_sys:
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        obj = db.get_record(db_name, obj_id)
        if not obj:
            return "Object not found", 404

        # Check permission for READ access
        try:
            perm_sys.check_grant(obj_id, obj.get('t', 0), "READ", fatal=True)
        except PermissionError as e:
            return str(e), 403

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

    # Get permission system
    perm_sys = get_permission_system(db_name)
    if not perm_sys:
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        if request.method == 'POST':
            # Handle form submission
            obj = db.get_record(db_name, obj_id)
            if not obj:
                return "Object not found", 404

            # Check permission for WRITE access
            try:
                perm_sys.check_grant(obj_id, obj.get('t', 0), "WRITE", fatal=True)
            except PermissionError as e:
                return str(e), 403

            # Check if metadata (cannot edit)
            if not perm_sys.can_edit_metadata(obj):
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

    try:
        with Database(db_name) as db:
            # Use ReportCompiler to build and execute the report
            compiler = ReportCompiler(db, db_name)

            # Get request parameters for filtering, sorting, etc.
            request_params = {}
            if request.args.get('SELECT'):
                request_params['SELECT'] = request.args.get('SELECT')
            if request.args.get('TOTALS'):
                request_params['TOTALS'] = request.args.get('TOTALS')
            if request.args.get('LIMIT'):
                request_params['LIMIT'] = request.args.get('LIMIT')

            # Add all FR_* and TO_* filter parameters
            for key in request.args:
                if key.startswith('FR_') or key.startswith('TO_'):
                    request_params[key] = request.args.get(key)

            # Compile and execute the report
            report_data = compiler.compile_report(
                report_id,
                execute=True,
                check_grant=False,
                request_params=request_params
            )

            return render_template('report.html',
                                 report=report_data,
                                 results=report_data.get('results', []),
                                 db_name=db_name)

    except Exception as e:
        write_log(f"Report error: {e}", "error", db_name)
        return f"Error generating report: {str(e)}", 500


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


@app.route('/<db_name>/export/bki/<int:obj_id>')
def export_bki(db_name, obj_id):
    """Export object data in BKI format"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    # Get permission system
    perm_sys = get_permission_system(db_name)
    if not perm_sys:
        return redirect(url_for('login_page', db=db_name))

    # Check EXPORT permission
    try:
        if not perm_sys.check_grant(obj_id, obj_id, "EXPORT", fatal=False):
            user = session.get('user_name', '')
            if user not in ('admin', db_name):
                return t9n("[RU]У вас нет прав на выгрузку объектов этого типа[EN]You do not have access to export this type of object"), 403
    except Exception:
        pass

    # Create exporter and export
    exporter = ExportImport(db_name)
    try:
        bki_content = exporter.export_bki(obj_id)

        # Create response with BKI file
        from flask import Response
        response = Response(bki_content, mimetype='application/octet-stream')
        response.headers['Content-Disposition'] = 'attachment; filename=data_export.bki'
        response.headers['Content-Type'] = 'application/force-download'
        response.headers['Content-Transfer-Encoding'] = 'binary'

        return response
    finally:
        exporter.close()


@app.route('/<db_name>/export/csv/<int:obj_id>')
def export_csv(db_name, obj_id):
    """Export object data in CSV format"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    # Get permission system
    perm_sys = get_permission_system(db_name)
    if not perm_sys:
        return redirect(url_for('login_page', db=db_name))

    # Check EXPORT permission
    try:
        if not perm_sys.check_grant(obj_id, obj_id, "EXPORT", fatal=False):
            user = session.get('user_name', '')
            if user not in ('admin', db_name):
                return t9n("[RU]У вас нет прав на выгрузку объектов этого типа[EN]You do not have access to export this type of object"), 403
    except Exception:
        pass

    # Get object data
    with Database(db_name) as db:
        # Get object type info
        obj_type = db.get_record(db_name, obj_id)
        if not obj_type:
            return "Object type not found", 404

        # Get headers (field names)
        headers = [obj_type.get('val', 'Value')]

        # Get field definitions for this type
        fields_query = f"""
            SELECT req.id, req.val
            FROM `{db_name}` req
            WHERE req.up = %s
            ORDER BY req.ord
        """
        fields = db.execute(fields_query, (obj_id,))
        for field in fields:
            headers.append(field['val'])

        # Get all data rows
        data_rows = []
        objects_query = f"""
            SELECT id, val FROM `{db_name}`
            WHERE t = %s AND up != 0
            ORDER BY ord
        """
        objects = db.execute(objects_query, (obj_id,))

        for obj in objects:
            row = [obj['val']]

            # Get field values for this object
            for field in fields:
                field_query = f"""
                    SELECT val FROM `{db_name}`
                    WHERE up = %s AND t = %s
                """
                field_val = db.execute_one(field_query, (obj['id'], field['id']))
                row.append(field_val['val'] if field_val else '')

            data_rows.append(row)

    # Create exporter and export
    exporter = ExportImport(db_name)
    try:
        csv_content = exporter.export_csv(obj_id, headers, data_rows)

        # Create response with CSV file
        from flask import Response
        response = Response(csv_content, mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=data_export.csv'
        response.headers['Content-Type'] = 'application/force-download'

        return response
    finally:
        exporter.close()


@app.route('/<db_name>/import/bki/<int:obj_id>', methods=['GET', 'POST'])
def import_bki(db_name, obj_id):
    """Import object data from BKI format"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    # Get permission system
    perm_sys = get_permission_system(db_name)
    if not perm_sys:
        return redirect(url_for('login_page', db=db_name))

    if request.method == 'POST':
        # Check EXPORT permission (import uses EXPORT permission in PHP)
        try:
            if not perm_sys.check_grant(obj_id, obj_id, "EXPORT", fatal=False):
                user = session.get('user_name', '')
                if user not in ('admin', db_name):
                    return t9n("[RU]У вас нет прав на загрузку объектов этого типа[EN]You do not have access to import this type of object"), 403
        except Exception:
            pass

        # Check for uploaded file
        if 'bki_file' not in request.files:
            return t9n("[RU]Выберите файл[EN]Please select a file"), 400

        file = request.files['bki_file']
        if file.filename == '':
            return t9n("[RU]Выберите файл[EN]Please select a file"), 400

        # Check file size (4MB limit)
        max_size = 4194304
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Seek back to start

        if file_size > max_size:
            return t9n(f"[RU]Ошибка. Максимальный размер файла: {max_size} Б[EN]The maximum file size is {max_size} B"), 400

        # Read file content
        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            # Try with BOM
            file.seek(0)
            content = file.read().decode('utf-8-sig')

        # Get parent ID from request
        parent_id = int(request.form.get('parent_id', 1))

        # Import data
        importer = ExportImport(db_name)
        try:
            success, message = importer.import_bki(content, parent_id)

            if success:
                return redirect(url_for('view_object', db_name=db_name, obj_id=obj_id))
            else:
                return message, 400
        finally:
            importer.close()

    # GET request - show import form
    return render_template('import_bki.html', db_name=db_name, obj_id=obj_id)


@app.route('/<db_name>/_m_del/<int:obj_id>', methods=['POST'])
def delete_object(db_name, obj_id):
    """Delete an object"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    # Get permission system
    perm_sys = get_permission_system(db_name)
    if not perm_sys:
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        obj = db.get_record(db_name, obj_id)
        if not obj:
            return "Object not found", 404

        # Check permission for WRITE access
        try:
            perm_sys.check_grant(obj_id, obj.get('t', 0), "WRITE", fatal=True)
        except PermissionError as e:
            return str(e), 403

        # Check if metadata (cannot delete)
        parent = db.get_record(db_name, obj['up'])
        if not perm_sys.can_delete_metadata(parent):
            return t9n("[RU]Нельзя удалить метаданные[EN]You can't delete metadata"), 403

        # Delete object and its children
        db.delete(db_name, obj_id)

        return redirect(url_for('index', db_name=db_name))


@app.route('/api/<db_name>/objects', methods=['GET', 'POST'])
def api_objects(db_name):
    """API endpoint for objects"""
    # Get permission system from token in header or cookie
    token = request.headers.get('X-Authorization') or request.cookies.get(db_name)
    if not token:
        return jsonify({'error': 'Authentication required'}), 401

    perm_sys = PermissionSystem(db_name)
    try:
        if not perm_sys.validate_token(token):
            return jsonify({'error': 'Invalid token'}), 401
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403

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

        # Check permission for WRITE access
        try:
            parent_id = data.get('up', 1)
            perm_sys.check_grant(parent_id, data.get('t', 3), "WRITE", fatal=True)
        except PermissionError as e:
            return jsonify({'error': str(e)}), 403

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
    # Get permission system from token in header or cookie
    token = request.headers.get('X-Authorization') or request.cookies.get(db_name)
    if not token:
        return jsonify({'error': 'Authentication required'}), 401

    perm_sys = PermissionSystem(db_name)
    try:
        if not perm_sys.validate_token(token):
            return jsonify({'error': 'Invalid token'}), 401
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403

    with Database(db_name) as db:
        if request.method == 'GET':
            obj = db.get_record(db_name, obj_id)
            if not obj:
                return jsonify({'error': 'Object not found'}), 404

            # Check permission for READ access
            try:
                perm_sys.check_grant(obj_id, obj.get('t', 0), "READ", fatal=True)
            except PermissionError as e:
                return jsonify({'error': str(e)}), 403

            return jsonify(obj)

        elif request.method == 'PUT':
            data = request.get_json()
            obj = db.get_record(db_name, obj_id)
            if not obj:
                return jsonify({'error': 'Object not found'}), 404

            # Check permission for WRITE access
            try:
                perm_sys.check_grant(obj_id, obj.get('t', 0), "WRITE", fatal=True)
            except PermissionError as e:
                return jsonify({'error': str(e)}), 403

            if 'val' in data:
                db.update_val(db_name, obj_id, data['val'])

            return jsonify({'id': obj_id, 'success': True})

        elif request.method == 'DELETE':
            obj = db.get_record(db_name, obj_id)
            if not obj:
                return jsonify({'error': 'Object not found'}), 404

            # Check permission for WRITE access
            try:
                perm_sys.check_grant(obj_id, obj.get('t', 0), "WRITE", fatal=True)
            except PermissionError as e:
                return jsonify({'error': str(e)}), 403

            db.delete(db_name, obj_id)
            return jsonify({'success': True})


def verify_auth(db_name):
    """Verify user authentication"""
    token = request.cookies.get(db_name)
    return token and verify_token(db_name, token)


def verify_token(db_name, token):
    """Verify authentication token and load permissions"""
    try:
        # Use new permission system
        perm_sys = PermissionSystem(db_name)
        if perm_sys.validate_token(token):
            # Store permission system in session
            session['permission_system'] = perm_sys
            session['db_name'] = db_name
            return True
    except PermissionError as e:
        write_log(f"Permission error: {e}", "error", db_name)
        return False
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


@app.route('/auth', methods=['POST'])
def auth():
    """Handle login form"""
    import hashlib
    
    db_name = request.form.get('db', 'ideav')
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not email or not password:
        return render_template('login.html', db_name=db_name, error='Введите email и пароль')
    
    try:
        with Database(db_name) as db:
            # Find user by email (t=31 is Email type, up points to user)
            query = f'''
                SELECT u.id as user_id, p.val as pwd_hash, t.val as token
                FROM {db_name} e
                JOIN {db_name} u ON e.up = u.id AND u.t = {Config.USER}
                LEFT JOIN {db_name} p ON p.up = u.id AND p.t = 20
                LEFT JOIN {db_name} t ON t.up = u.id AND t.t = {Config.TOKEN}
                WHERE e.t = 31 AND LOWER(e.val) = %s
            '''
            result = db.execute_one(query, (email,))
            
            if result:
                # Hash the password with salt
                salt = Config.SALT
                pwd_hash = hashlib.sha1((salt + password).encode()).hexdigest()
                
                if result['pwd_hash'] == pwd_hash:
                    # Login successful
                    token = result['token']
                    if not token:
                        token = generate_token()
                        # Save new token
                        db.execute(
                            f'INSERT INTO {db_name} (t, up, ord, val) VALUES ({Config.TOKEN}, %s, 1, %s)',
                            (result['user_id'], token), commit=True
                        )
                    
                    response = redirect(f'/{db_name}')
                    response.set_cookie(db_name, token, max_age=31536000, path='/')
                    return response
            
            return render_template('login.html', db_name=db_name, error='Неверный email или пароль')
            
    except Exception as e:
        write_log(f'Auth error: {e}', 'error', db_name)
        return render_template('login.html', db_name=db_name, error='Ошибка авторизации')


@app.route('/login')
def login_page():
    """Login page with form"""
    error = request.args.get('error', '')
    db_name = request.args.get('db', 'ideav')
    return render_template('login.html', error=error, db_name=db_name)


@app.route('/<db_name>/logout')
def logout(db_name):
    """Logout user"""
    session.clear()
    response = redirect(url_for('login_page', db=db_name))
    response.delete_cookie(db_name)
    return response
