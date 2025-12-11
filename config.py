"""
Configuration file for the application
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""

    # Database configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'ideav')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'ideav')
    DB_NAME = os.environ.get('DB_NAME', 'ideav')
    DB_CHARSET = 'utf8mb4'

    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset={DB_CHARSET}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ideav')
    SALT = os.environ.get('SALT', 'ideav')

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=360)
    SESSION_COOKIE_NAME = 'ideav'
    SESSION_COOKIE_PATH = '/'

    # Upload configuration
    UPLOAD_FOLDER = 'download'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    LOGS_DIR = 'logs'

    # Application constants
    VAL_LIM = 127
    DEFAULT_LIMIT = 20
    DDLIST_ITEMS = 50
    COOKIES_EXPIRE = 2592000  # 30 days

    # Field type constants
    FIELD_TYPES = {
        1: 'ROOT',
        2: 'HTML',
        3: 'SHORT',
        4: 'USER',
        5: 'GRANT',
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

    BASIC_TYPES = {
        3: 'SHORT',
        8: 'CHARS',
        9: 'DATE',
        13: 'NUMBER',
        14: 'SIGNED',
        11: 'BOOLEAN',
        12: 'MEMO',
        4: 'DATETIME',
        10: 'FILE',
        2: 'HTML',
        7: 'BUTTON',
        6: 'PWD',
        5: 'GRANT',
        15: 'CALCULATABLE',
        16: 'REPORT_COLUMN',
        17: 'PATH'
    }

    # Report constants
    REPORT = 22
    LEVEL = 47
    MASK = 49
    REP_COLS = 28
    REP_JOIN = 44
    REP_HREFS = 95
    REP_URL = 97
    REP_LIMIT = 134
    REP_IFNULL = 113
    REP_WHERE = 262
    REP_ALIAS = 265
    REP_JOIN_ON = 266
    REP_COL_FORMAT = 29
    REP_COL_ALIAS = 58
    REP_COL_FUNC = 63
    REP_COL_TOTAL = 65
    REP_COL_NAME = 100
    REP_COL_FORMULA = 101
    REP_COL_FROM = 102
    REP_COL_TO = 103
    REP_COL_HAV_FR = 105
    REP_COL_HAV_TO = 106
    REP_COL_HIDE = 107
    REP_COL_SORT = 109
    REP_COL_SET = 132

    # User field constants
    USER = 18
    DATABASE = 271
    PHONE = 30
    XSRF = 40
    EMAIL = 41
    ROLE = 42
    ACTIVITY = 124
    PASSWORD = 20
    TOKEN = 125
    SECRET = 130

    # Regex patterns
    DB_MASK = r'^[a-z]\w{1,14}$'
    USER_DB_MASK = r'^[a-z]\w{2,14}$'
    DIR_MASK = r'^[a-z0-9_]+$'
    FILE_MASK = r'^[a-z0-9_.]+$'
    MAIL_MASK = r'.+@.+\..+'
    NOT_NULL_MASK = ':!NULL:'
    ALIAS_MASK = r':ALIAS=(.+):'
    ALIAS_DEF = ':ALIAS='

    # Blacklisted file extensions
    BLACKLISTED_EXTENSIONS = [
        'php', 'cgi', 'pl', 'fcgi', 'fpl', 'phtml', 'shtml',
        'php2', 'php3', 'php4', 'php5', 'asp', 'jsp'
    ]

    # CORS configuration
    CORS_ALLOW_HEADERS = ['X-Authorization', 'x-authorization', 'Content-Type', 'content-type', 'Origin']
    CORS_ALLOW_METHODS = ['POST', 'GET', 'OPTIONS']
    CORS_ALLOW_ORIGIN = '*'
