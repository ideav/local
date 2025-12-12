"""
Utility functions
"""
import re
import hashlib
import time
import os
from datetime import datetime, timedelta
from config import Config


def get_sha(value):
    """Generate SHA1 hash"""
    salt_value = f"{Config.SALT}{value}"
    return hashlib.sha1(salt_value.encode()).hexdigest()


def xsrf_token(token, db_name):
    """Generate XSRF token"""
    salt_value = salt(token, db_name)
    return hashlib.sha1(salt_value.encode()).hexdigest()[:22]


def salt(a, b):
    """Salt function for hashing"""
    return f"{a}{b}{Config.SALT}"


def check_db_name(pattern, db_name):
    """Validate database name against pattern"""
    return bool(re.match(pattern, db_name, re.IGNORECASE))


def is_api_request(request):
    """Check if request is API request"""
    return (
        'JSON' in request.args or 'JSON' in request.form or
        'JSON_DATA' in request.args or 'JSON_DATA' in request.form or
        'JSON_KV' in request.args or 'JSON_KV' in request.form or
        request.path.startswith('/api/')
    )


def blacklist_extension(extension):
    """Check if file extension is blacklisted"""
    return extension.lower() in Config.BLACKLISTED_EXTENSIONS


def get_subdir(record_id):
    """Get subdirectory for file storage"""
    folder_num = record_id // 1000
    sha_part = get_sha(folder_num)[:8]
    return os.path.join(Config.UPLOAD_FOLDER, str(folder_num) + sha_part)


def get_filename(record_id):
    """Get filename for stored file"""
    id_str = f"{record_id:03d}"
    sha_part = get_sha(record_id)[:8]
    return id_str[-3:] + sha_part


def format_date(date_val):
    """Format date value"""
    if not date_val:
        return ''
    if isinstance(date_val, str):
        if date_val == '[TODAY]':
            return datetime.now().strftime('%Y%m%d')
        elif date_val == '[YESTERDAY]':
            return (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        elif date_val == '[TOMORROW]':
            return (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
        elif date_val == '[MONTH_AGO]':
            return (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        elif date_val == '[NOW]':
            return datetime.now().strftime('%Y%m%d%H%M%S')
    return date_val


def builtin_value(value):
    """Replace built-in placeholders with actual values"""
    if isinstance(value, str):
        # Basic replacements that don't need request context
        replacements = {
            '[TODAY]': datetime.now().strftime('%Y%m%d'),
            '[NOW]': datetime.now().strftime('%Y%m%d%H%M%S'),
            '[YESTERDAY]': (datetime.now() - timedelta(days=1)).strftime('%Y%m%d'),
            '[TOMORROW]': (datetime.now() + timedelta(days=1)).strftime('%Y%m%d'),
            '[MONTH_AGO]': (datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
        }

        for placeholder, replacement in replacements.items():
            if value == placeholder:
                return replacement

        # Request-context dependent replacements
        try:
            from flask import request, session

            request_replacements = {
                '[USER]': session.get('user_name', ''),
                '[USER_ID]': str(session.get('user_id', '')),
                '[REMOTE_ADDR]': request.remote_addr or '',
                '[HTTP_USER_AGENT]': request.headers.get('User-Agent', ''),
                '[HTTP_REFERER]': request.headers.get('Referer', ''),
                '[HTTP_HOST]': request.host or ''
            }

            for placeholder, replacement in request_replacements.items():
                if value == placeholder:
                    return replacement
        except RuntimeError:
            # Not in request context (e.g., during testing)
            pass

    return value


def t9n(message, locale='EN'):
    """Simple translation function"""
    # Extract locale-specific text from message
    # Format: [RU]Russian text[EN]English text
    locale_pattern = f'\\[{locale}\\]'
    match = re.search(f'{locale_pattern}(.*?)(?:\\[[A-Z]{{2}}\\]|$)', message, re.DOTALL)

    if match:
        return match.group(1).strip()

    # If no locale found, return original message
    return message


def abn_date2str(val):
    """Convert date to Russian string format"""
    months = {
        '01': 'января', '02': 'февраля', '03': 'марта',
        '04': 'апреля', '05': 'мая', '06': 'июня',
        '07': 'июля', '08': 'августа', '09': 'сентября',
        '10': 'октября', '11': 'ноября', '12': 'декабря'
    }

    if len(val) >= 8:
        day = val[-2:]
        month = val[4:6]
        year = val[0:4]
        return f"{day} {months.get(month, month)} {year} г."
    return val


def abn_translit(text):
    """Transliterate Cyrillic to Latin"""
    text = text.lower()
    text = text.replace('\n', '_').replace('\r', '_').replace(' ', '_')

    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'e', 'ж': 'j', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch',
        'ш': 'sh', 'щ': 'sh', 'ы': 'y', 'э': 'e', 'ю': 'yu',
        'я': 'ya', 'ъ': '', 'ь': ''
    }

    for cyr, lat in translit_map.items():
        text = text.replace(cyr, lat)

    # Remove non-alphanumeric characters except hyphens and underscores
    text = re.sub(r'[^0-9a-z\-_]', '', text)
    return text


def write_log(text, mode, db_name):
    """Write to log file"""
    if not os.path.exists(Config.LOGS_DIR):
        os.makedirs(Config.LOGS_DIR)

    log_file = os.path.join(Config.LOGS_DIR, f"{db_name}_{mode}.txt")
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} {text}\n")


def generate_token():
    """Generate a unique token"""
    return hashlib.md5(str(time.time()).encode()).hexdigest()


def remove_directory(path):
    """Recursively remove directory"""
    if os.path.isdir(path):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                remove_directory(item_path)
            else:
                os.unlink(item_path)
        os.rmdir(path)
    elif os.path.exists(path):
        os.unlink(path)


def get_reference_types(db, table_name):
    """
    Get mapping of field types to their reference target types.

    In IdeaV, a field that references another type has a child record where:
    - The parent (up) is the field type ID
    - The child's type (t) points to the target type
    - The child's value (val) is empty or specific field name

    Returns:
        dict: Mapping of {field_type_id: target_type_id}
    """
    # Query to find reference type mappings
    # A reference field is one where there exists a record with up=field_id and t pointing to another type
    # We look for metadata entries (up=0) that have children with non-zero t values
    query = f"""
        SELECT parent.id as field_type, child.t as target_type
        FROM `{table_name}` parent
        JOIN `{table_name}` child ON child.up = parent.id
        WHERE parent.up = 0
          AND child.t > 0
          AND child.val = ''
          AND child.ord = 0
    """

    results = db.execute(query)
    ref_types = {}
    if results:
        for row in results:
            ref_types[row['field_type']] = row['target_type']

    return ref_types


def get_field_base_type(db, table_name, field_type):
    """
    Get the base type of a field.

    Args:
        db: Database connection
        table_name: Name of the table
        field_type: Field type ID

    Returns:
        str: Base type name (e.g., 'SHORT', 'MEMO', 'REFERENCE', etc.)
    """
    # Base types are the fundamental types in the system (id = t = self-referential)
    base_types = {
        2: 'HTML',
        3: 'SHORT',
        6: 'PWD',
        7: 'BUTTON',
        8: 'CHARS',
        9: 'DATE',
        10: 'FILE',
        11: 'BOOLEAN',
        12: 'MEMO',
        13: 'NUMBER',
        14: 'SIGNED',
        15: 'CALCULATABLE',
        16: 'REPORT_COLUMN',
        17: 'PATH'
    }

    # Get reference types to check if this is a reference field
    ref_types = get_reference_types(db, table_name)

    if field_type in ref_types:
        return 'REFERENCE'
    elif field_type in base_types:
        return base_types[field_type]

    # For custom types, find their base type by looking up the metadata
    query = f"SELECT t FROM `{table_name}` WHERE id = %s AND up = 0"
    result = db.execute_one(query, (field_type,))

    if result and result['t'] in base_types:
        return base_types[result['t']]

    return 'SHORT'  # Default fallback
