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

# Make t9n() available in all templates
app.jinja_env.globals.update(t9n=t9n)


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

    # Generate XSRF token for session if not exists
    if 'xsrf_token' not in session:
        # Use user token if authenticated, otherwise use remote address
        token = request.cookies.get(db_name) or request.remote_addr or 'guest'
        session['xsrf_token'] = xsrf_token(token, db_name)

    # Validate XSRF token on POST requests (except auth and API endpoints)
    if request.method == 'POST' and not is_api_request(request) and request.path != '/auth':
        if not validate_xsrf():
            return t9n("[RU]Неверный или устаревший токен CSRF<br/>[EN]Invalid or expired CSRF token"), 403


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

        # Check if CSV export is requested
        if 'csv' in request.args:
            return export_objects_csv(db, db_name, obj_id, obj.get('t', 0))

        # Get object children
        children = db.get_records(db_name, {'up': obj_id})

        # Get type information for create form
        # If viewing a type object (up=0), get its requirements for the create form
        type_requirements = []
        if obj['up'] == 0:
            # This is a type definition, get its required fields
            req_query = f"""
                SELECT req.id, req.t, typ.val as type_name
                FROM `{db_name}` req
                LEFT JOIN `{db_name}` typ ON typ.id = req.t AND typ.up = 0
                WHERE req.up = %s AND req.t > 0
                ORDER BY req.ord
            """
            type_requirements = db.execute(req_query, (obj_id,))

        # Check if user can create objects of this type
        # For now, we'll allow creation if the object is a type (up=0)
        can_create = obj['up'] == 0

        return render_template('object.html',
                               obj=obj,
                               children=children,
                               db_name=db_name,
                               can_create=can_create,
                               type_requirements=type_requirements,
                               xsrf_token=generate_token())


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

            # Get reference types for field processing
            from utils import get_reference_types, get_field_base_type
            ref_types = get_reference_types(db, db_name)

            # Handle child field updates
            children = db.get_records(db_name, {'up': obj_id})
            for child in children:
                field_type = child['t']
                form_key = f't{field_type}'

                if form_key in request.form:
                    new_value = request.form.get(form_key, '')

                    # Check if this is a reference field
                    if field_type in ref_types:
                        # For reference fields, the value is the referenced object ID
                        # It's stored in the 't' column, not 'val'
                        if new_value and new_value.isdigit():
                            new_ref_id = int(new_value)
                            if new_ref_id != child['t']:
                                # Update the reference by changing the 't' value
                                query = f"UPDATE `{db_name}` SET t = %s WHERE id = %s"
                                db.execute(query, (new_ref_id, child['id']), commit=True)
                    else:
                        # Regular field - update the value
                        if new_value != child['val']:
                            db.update_val(db_name, child['id'], new_value)

                # Handle boolean fields
                if f'b{field_type}' in request.form:
                    # Checkbox was in the form
                    is_checked = form_key in request.form
                    bool_val = '1' if is_checked else '0'
                    if bool_val != child['val']:
                        db.update_val(db_name, child['id'], bool_val)

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

        # Get reference type mappings
        from utils import get_reference_types, get_field_base_type
        ref_types = get_reference_types(db, db_name)

        # Enrich children with field information
        for child in children:
            # For reference fields, val contains the field type ID, t contains the referenced object ID
            # For regular fields, t contains the field type, val contains the value

            # Determine if this is a metadata field definition (child of type definition)
            parent_rec = db.get_record(db_name, child['up'])
            is_metadata_field = parent_rec and parent_rec.get('up', 0) == 0

            if is_metadata_field:
                # This is a field definition, not an actual field value
                field_type = int(child['val']) if child['val'].isdigit() else child['t']
            else:
                field_type = child['t']

            child['base_type'] = get_field_base_type(db, db_name, field_type)
            child['field_type'] = field_type

            # If this is a reference field, load the reference options
            if field_type in ref_types:
                target_type = ref_types[field_type]
                child['ref_target_type'] = target_type

                # For reference fields, the actual reference is stored in child['t']
                # child['val'] stores the field type ID
                if child['t'] > 0 and child['t'] != field_type:
                    ref_value_id = child['t']
                    child['ref_value_id'] = ref_value_id

                    # Get the referenced object's value to display
                    ref_obj = db.get_record(db_name, ref_value_id)
                    if ref_obj:
                        child['ref_display_val'] = ref_obj.get('val', '')
                else:
                    child['ref_value_id'] = None
                    child['ref_display_val'] = ''

                # Load available reference options (limit to prevent huge lists)
                search_param = request.args.get(f'SEARCH_{field_type}', '')
                if search_param:
                    # Filter by search
                    query = f"""
                        SELECT id, val FROM `{db_name}`
                        WHERE t = %s AND val LIKE %s
                        ORDER BY val
                        LIMIT 50
                    """
                    ref_options = db.execute(query, (target_type, f'%{search_param}%'))
                else:
                    # Load first 50 options
                    query = f"""
                        SELECT id, val FROM `{db_name}`
                        WHERE t = %s
                        ORDER BY val
                        LIMIT 50
                    """
                    ref_options = db.execute(query, (target_type,))

                child['ref_options'] = ref_options or []

        # Get field type name
        type_obj = db.get_record(db_name, obj['t'])
        obj['type_name'] = type_obj.get('val', 'Object') if type_obj else 'Object'

        return render_template('edit_obj.html',
                             obj=obj,
                             children=children,
                             db_name=db_name,
                             session=session)


@app.route('/<db_name>/api/ref_search/<int:target_type>')
def ref_search(db_name, target_type):
    """AJAX endpoint for searching reference options"""
    if not verify_auth(db_name):
        return jsonify({"error": "Not authorized"}), 403

    search_term = request.args.get('q', '')

    with Database(db_name) as db:
        if search_term:
            # Search for matching objects
            query = f"""
                SELECT id, val FROM `{db_name}`
                WHERE t = %s AND val LIKE %s
                ORDER BY val
                LIMIT 50
            """
            results = db.execute(query, (target_type, f'%{search_term}%'))
        else:
            # Return first 50 objects
            query = f"""
                SELECT id, val FROM `{db_name}`
                WHERE t = %s
                ORDER BY val
                LIMIT 50
            """
            results = db.execute(query, (target_type,))

        # Format results for autocomplete
        options = []
        if results:
            for row in results:
                options.append({
                    'id': row['id'],
                    'val': row['val']
                })

        return jsonify(options)


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


@app.route('/<db_name>/_m_new/<int:type_id>', methods=['POST'])
def create_object(db_name, type_id):
    """Create a new object"""
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    # Get parent object ID
    up = request.form.get('up', type='int')
    if not up:
        return t9n("[RU]Недопустимые данные: up не задан[EN]Data is invalid: up not provided"), 400

    if up == 0:
        return t9n("[RU]Недопустимые данные: up=0. Установите значение=1 для независимых объектов.[EN]Data is invalid: up=0. Set up=1 for independent objects."), 400

    with Database(db_name) as db:
        # Get type information
        type_obj = db.get_record(db_name, type_id)
        if not type_obj or type_obj['up'] != 0:
            return t9n("[RU]Проверка типа неуспешна[EN]Type check failed"), 400

        base_typ = type_obj['t']

        # Get the value from the form (field name is t{type_id})
        val = request.form.get(f't{type_id}', '').strip()

        # Calculate order for the new object
        ord_val = 1
        if up != 1:
            # Verify parent object exists and is not metadata
            parent = db.get_record(db_name, up)
            if not parent:
                return t9n(f"[RU]Родительский объект {up} не найден.[EN]The parent object {up} not found."), 404
            if parent['up'] == 0:
                return t9n(f"[RU]Родительский объект {up} - метаданные.[EN]The parent object {up} is metadata."), 403

            # Calculate order - get max ord + 1
            query = f"SELECT MAX(ord) as max_ord FROM `{db_name}` WHERE up = %s AND t = %s"
            result = db.execute_one(query, (up, type_id))
            if result and result['max_ord'] is not None:
                ord_val = result['max_ord'] + 1

        # Generate default value if not provided
        if not val:
            # Check basic type from config
            from config import Config
            basic_type_name = Config.BASIC_TYPES.get(base_typ, 'SHORT')

            if basic_type_name == 'NUMBER':
                # Get max numeric value + 1
                query = f"SELECT MAX(CAST(val AS UNSIGNED)) as max_val FROM `{db_name}` WHERE t = %s AND up = %s"
                result = db.execute_one(query, (type_id, up))
                max_val = 0
                if result and result['max_val'] is not None:
                    max_val = result['max_val']

                # Check if there's an empty numeric object we can reuse
                query = f"""
                    SELECT obj.id FROM `{db_name}` obj
                    WHERE obj.t = %s AND obj.val = %s AND obj.up = %s
                    AND NOT EXISTS(SELECT * FROM `{db_name}` reqs WHERE reqs.up = obj.id)
                    LIMIT 1
                """
                result = db.execute_one(query, (type_id, str(max_val), up))
                if result:
                    # Redirect to edit this existing empty object
                    return redirect(url_for('edit_object', db_name=db_name, obj_id=result['id']))

                val = str(max_val + 1)
            elif basic_type_name == 'DATE':
                import time
                val = time.strftime('%d', time.localtime())
            elif basic_type_name == 'DATETIME':
                import time
                val = str(int(time.time()))
            elif basic_type_name == 'SIGNED':
                val = '1'
            else:
                val = str(ord_val)

        # Check uniqueness if required (ord field in type object indicates uniqueness)
        if type_obj.get('ord', 0) == 1:
            query = f"SELECT id FROM `{db_name}` WHERE t = %s AND val = %s AND up = %s LIMIT 1"
            existing = db.execute_one(query, (type_id, val, up))
            if existing:
                return t9n(f"[RU]<b>{val}</b> уже существует! Перейти к <a href='/{db_name}/edit_obj/{existing['id']}'>{val}</a>[EN]<b>{val}</b> already exists. Go to <a href='/{db_name}/edit_obj/{existing['id']}'>{val}</a>"), 409

        # Insert the new object
        new_obj_id = db.insert(db_name, up, ord_val, type_id, val, "Add Object")

        # Handle additional fields (requirements/attributes)
        for key, value in request.form.items():
            if key.startswith('t') and key != f't{type_id}':
                # Extract type ID from field name
                try:
                    t = int(key[1:])
                except ValueError:
                    continue

                if t > 0 and value:
                    # Insert the attribute
                    db.insert(db_name, new_obj_id, 1, t, value, "Insert new req")

        # Handle file uploads
        for key, file in request.files.items():
            if file and file.filename and key.startswith('t'):
                try:
                    t = int(key[1:])
                    if t > 0:
                        handle_file_upload(db, db_name, new_obj_id, t, file)
                except (ValueError, Exception) as e:
                    write_log(f"File upload error: {e}", "error", db_name)

        # Redirect to edit the newly created object
        return redirect(url_for('edit_object', db_name=db_name, obj_id=new_obj_id))


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


@app.route('/<db_name>/object/<int:obj_id>/', methods=['POST'])
def batch_delete_objects(db_name, obj_id):
    """
    Batch delete objects matching current filters.
    This implements the _m_del_select functionality from PHP.
    """
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    # Check if this is a batch delete request
    if '_m_del_select' not in request.form:
        return redirect(url_for('view_object', db_name=db_name, obj_id=obj_id))

    # Get permission system
    perm_sys = get_permission_system(db_name)
    if not perm_sys:
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        # Get the object type
        obj = db.get_record(db_name, obj_id)
        if not obj:
            return "Object not found", 404

        cur_typ = obj.get('t', 0)

        # Check bulk delete permission
        user_name = session.get('user_name', '')
        if not perm_sys.has_delete_grant(cur_typ) and user_name != 'admin' and user_name != db_name:
            return t9n("[RU]У вас нет прав на массовое удаление объектов этого типа[EN]You do not have access to delete this type of object in bulk"), 403

        # Build filter query to get IDs to delete
        # Get all request parameters for filters
        filters = {}
        for key, value in request.form.items():
            if key.startswith('F_') and value:
                # Extract field type from F_<type> format
                field_id = key[2:]
                if field_id.isdigit():
                    filters[int(field_id)] = {'F': value}

        # Query to get filtered objects (excluding those with references)
        # This matches the PHP logic at line 3916-3917
        query = f"""
            SELECT DISTINCT vals.id
            FROM `{db_name}` vals
            LEFT JOIN `{db_name}` refr ON refr.t = vals.id
            WHERE vals.t = %s AND refr.id IS NULL
        """
        params = [cur_typ]

        # Add filter conditions if any
        if filters:
            # Note: For simplicity, we're doing basic filtering here
            # Full filter implementation would use the filters.py module
            for field_id, filter_val in filters.items():
                if 'F' in filter_val:
                    query += f" AND vals.val LIKE %s"
                    params.append(f"%{filter_val['F']}%")

        # Execute and get IDs to delete
        ids_to_delete = db.execute(query, tuple(params))

        if ids_to_delete:
            record_ids = [row['id'] for row in ids_to_delete]
            # Use batch delete
            db.batch_delete(db_name, record_ids)

        # Redirect back to the object view
        return redirect(url_for('view_object', db_name=db_name, obj_id=obj_id))


@app.route('/<db_name>/_m_up/<int:obj_id>', methods=['POST'])
def move_up_object(db_name, obj_id):
    """
    Move an object up in the ordering.
    This implements the _m_up functionality from PHP.
    """
    if not verify_auth(db_name):
        return redirect(url_for('login_page', db=db_name))

    # Get permission system
    perm_sys = get_permission_system(db_name)
    if not perm_sys:
        return redirect(url_for('login_page', db=db_name))

    with Database(db_name) as db:
        # Check permission for WRITE access
        try:
            perm_sys.check_grant(obj_id, 0, "WRITE", fatal=True)
        except PermissionError as e:
            return str(e), 403

        # Get current object with its order and find the previous item
        query = f"""
            SELECT obj.t, obj.up, obj.ord, MAX(peers.ord) as new_ord
            FROM `{db_name}` obj
            LEFT JOIN `{db_name}` peers ON peers.up = obj.up
                AND peers.t = obj.t
                AND peers.ord < obj.ord
            WHERE obj.id = %s
        """
        result = db.execute_one(query, (obj_id,))

        if not result:
            return "Object not found", 404

        up = result['up']
        t = result['t']
        current_ord = result['ord']
        new_ord = result.get('new_ord')

        if new_ord:
            # Swap the ord values
            swap_query = f"""
                UPDATE `{db_name}`
                SET ord = CASE
                    WHEN ord = %s THEN %s
                    WHEN ord = %s THEN %s
                END
                WHERE up = %s AND (ord = %s OR ord = %s)
            """
            db.execute(swap_query, (current_ord, new_ord, new_ord, current_ord, up, current_ord, new_ord), commit=True)

        # Redirect back to parent object view
        return redirect(url_for('view_object', db_name=db_name, obj_id=up))


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


def export_objects_csv(db, db_name, obj_id, cur_typ):
    """
    Export filtered objects to CSV format.
    This implements basic CSV export functionality.

    Args:
        db: Database connection
        db_name: Database name
        obj_id: Object ID
        cur_typ: Current type

    Returns:
        Flask response with CSV file
    """
    import csv
    import io
    from flask import make_response

    # Build filter query to get objects to export
    filters = {}
    for key, value in request.args.items():
        if key.startswith('F_') and value:
            field_id = key[2:]
            if field_id.isdigit():
                filters[int(field_id)] = {'F': value}

    # Query to get filtered objects
    query = f"SELECT vals.id, vals.val FROM `{db_name}` vals WHERE vals.t = %s"
    params = [cur_typ]

    # Add filter conditions if any
    if filters:
        for field_id, filter_val in filters.items():
            if 'F' in filter_val:
                query += f" AND vals.val LIKE %s"
                params.append(f"%{filter_val['F']}%")

    query += " ORDER BY vals.id"

    # Execute query
    objects = db.execute(query, tuple(params))

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['ID', 'Value'])

    # Write data rows
    for obj in objects:
        writer.writerow([obj['id'], obj['val']])

    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=data_export_{obj_id}.csv'

    return response


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
        return render_template('login.html', db_name=db_name, error=t9n('[RU]Введите email и пароль[EN]Enter email and password'))
    
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

                    # Generate XSRF token for this session
                    session['xsrf_token'] = xsrf_token(token, db_name)
                    session['user_id'] = result['user_id']

                    response = redirect(f'/{db_name}')
                    response.set_cookie(db_name, token, max_age=31536000, path='/')
                    return response
            
            return render_template('login.html', db_name=db_name, error=t9n('[RU]Неверный email или пароль[EN]Invalid email or password'))
            
    except Exception as e:
        write_log(f'Auth error: {e}', 'error', db_name)
        return render_template('login.html', db_name=db_name, error=t9n('[RU]Ошибка авторизации[EN]Authentication error'))


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


@app.route('/<db_name>/set_locale/<locale>')
def set_locale(db_name, locale):
    """Set language preference"""
    # Validate locale
    if locale not in ['RU', 'EN']:
        locale = 'EN'

    # Store in session
    session['locale'] = locale

    # Redirect back to referrer or home
    referrer = request.referrer
    if referrer and db_name in referrer:
        response = redirect(referrer)
    else:
        response = redirect(url_for('index', db_name=db_name))

    # Set cookie for persistence
    response.set_cookie(f'{db_name}_locale', locale, max_age=31536000, path='/')
    response.set_cookie('my_locale', locale, max_age=31536000, path='/')

    return response
