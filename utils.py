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


def t9n(message, locale=None):
    """
    Translation function for multilingual support.
    Extracts locale-specific text from message.
    Format: [RU]Russian text[EN]English text

    Args:
        message: String containing [LOCALE]text markers
        locale: Optional locale override (RU or EN). If not provided, uses session/cookie locale.

    Returns:
        Translated string for the current locale
    """
    # Get locale from session/request if not provided
    if locale is None:
        try:
            from flask import session, request
            # Try to get locale from session (set by before_request)
            if 'locale' in session:
                locale = session['locale']
            # Fallback to cookie
            elif request:
                db_name = getattr(request, 'db_name', 'ideav')
                locale = request.cookies.get(f'{db_name}_locale',
                                            request.cookies.get('my_locale', 'EN'))
            else:
                locale = 'EN'
        except (ImportError, RuntimeError):
            # Not in Flask context (e.g., during testing)
            locale = 'EN'

    # Normalize locale to uppercase
    locale = locale.upper() if locale else 'EN'

    # Extract locale-specific text from message
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
