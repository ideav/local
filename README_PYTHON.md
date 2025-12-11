# IdeaV - Local (Python Version)

This is a Python/Flask rewrite of the IdeaV local database management system.

## Overview

The Python version maintains the same functionality as the original PHP version:
- Database-driven object management system
- File upload and download capabilities
- Custom report generation
- User authentication and access control
- REST API endpoints

## Requirements

- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

## Installation

### 1. Set up the database

Run these SQL scripts in your MySQL database:

```bash
mysql -u root -p < 1_database.sql
mysql -u root -p ideav < 2_table.sql
```

These scripts will:
- Create the `ideav` database
- Create the `ideav` user with password `ideav`
- Create the main table structure
- Insert initial data

### 2. Install Python dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure the application

Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
```

Edit `.env` file to match your database configuration:

```
DB_HOST=localhost
DB_USER=ideav
DB_PASSWORD=ideav
DB_NAME=ideav
SECRET_KEY=your-secret-key-here
SALT=your-salt-here
```

### 4. Run the application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Project Structure

```
.
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── database.py            # Database connection and operations
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── templates_python/      # Jinja2 templates
│   ├── base.html
│   ├── main.html
│   ├── info.html
│   ├── object.html
│   ├── edit_obj.html
│   ├── upload.html
│   └── report.html
├── logs/                  # Application logs (auto-created)
└── download/              # Uploaded files (auto-created)
```

## Key Features

### Web Interface
- `/` - Main page
- `/<db_name>` - Database-specific main page
- `/<db_name>/object/<id>` - View object
- `/<db_name>/edit_obj/<id>` - Edit object
- `/<db_name>/upload` - Upload files
- `/<db_name>/report/<id>` - View report

### REST API
- `GET /api/<db_name>/objects` - List objects
- `POST /api/<db_name>/objects` - Create object
- `GET /api/<db_name>/objects/<id>` - Get object
- `PUT /api/<db_name>/objects/<id>` - Update object
- `DELETE /api/<db_name>/objects/<id>` - Delete object

## Differences from PHP Version

### Technology Stack
- **Web Framework**: Apache/PHP → Flask (Python)
- **Database Access**: mysqli → PyMySQL
- **Templates**: PHP templates → Jinja2
- **Session Management**: PHP sessions → Flask sessions

### Improvements
- Modern Python 3 syntax and best practices
- Type hints and better code organization
- Modular structure with separate files for different concerns
- Environment-based configuration
- Better error handling
- RESTful API design

### Maintained Compatibility
- Same database schema
- Same SQL scripts for initialization
- Same core functionality
- Similar URL structure
- Compatible with existing data

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

### Running in Production

For production deployment, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or use uWSGI:

```bash
pip install uwsgi
uwsgi --http :5000 --wsgi-file app.py --callable app
```

### Using with Nginx

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/your/app/static;
    }
}
```

## Configuration Options

All configuration options are in `config.py`:

- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Database connection
- `SECRET_KEY` - Flask secret key for sessions
- `SALT` - Salt for password hashing
- `UPLOAD_FOLDER` - Directory for uploaded files
- `LOGS_DIR` - Directory for log files
- `MAX_CONTENT_LENGTH` - Maximum upload file size
- `DEFAULT_LIMIT` - Default pagination limit
- `BLACKLISTED_EXTENSIONS` - File types not allowed for upload

## Security Notes

1. Change default passwords and secrets in production
2. Use HTTPS in production
3. Set proper file permissions on upload directories
4. Keep Python and dependencies updated
5. Use environment variables for sensitive configuration
6. Enable firewall rules to restrict database access

## Troubleshooting

### Database Connection Errors
- Verify MySQL is running
- Check database credentials in `.env`
- Ensure the `ideav` database exists
- Verify the `ideav` user has proper permissions

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version (3.8+ required)

### Port Already in Use
- Change the port in `app.py`: `app.run(port=5001)`
- Or kill the process using port 5000

### File Upload Errors
- Check `UPLOAD_FOLDER` permissions
- Verify `MAX_CONTENT_LENGTH` setting
- Ensure disk space is available

## Migration from PHP

To migrate from the existing PHP installation:

1. Keep the same MySQL database and data
2. Install Python version alongside PHP version
3. Test functionality on a different port
4. Update web server configuration to use Python version
5. Archive or remove PHP files

## License

Same as the original project.

## Support

For issues specific to the Python version, please check:
- Application logs in `logs/` directory
- Flask error messages
- Database connection status

For original functionality questions, refer to the PHP version documentation.
