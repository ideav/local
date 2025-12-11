# IdeaV Local - Implementation Guide

This guide provides step-by-step instructions for implementing and deploying the IdeaV Local database management system (Python version).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [Production Deployment](#production-deployment)
8. [Verification & Testing](#verification--testing)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)
11. [Maintenance](#maintenance)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Database**: MySQL 5.7+ or MariaDB 10.2+
- **Memory**: Minimum 512MB RAM
- **Disk Space**: Minimum 100MB free space

### Required Software

1. **Python 3.8+**
   ```bash
   # Check Python version
   python3 --version

   # If not installed:
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install python3 python3-pip python3-venv

   # CentOS/RHEL
   sudo yum install python3 python3-pip

   # macOS
   brew install python3
   ```

2. **MySQL Server**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mysql-server mysql-client

   # CentOS/RHEL
   sudo yum install mysql-server mysql

   # macOS
   brew install mysql

   # Start MySQL service
   sudo systemctl start mysql  # Linux
   brew services start mysql   # macOS
   ```

3. **Git** (for cloning the repository)
   ```bash
   git --version
   ```

---

## Quick Start

For experienced users who want to get started quickly:

```bash
# 1. Clone the repository
git clone https://github.com/ideav/local.git
cd local

# 2. Run automated setup
chmod +x setup.sh
./setup.sh

# 3. Configure database credentials
cp .env.example .env
# Edit .env with your settings

# 4. Initialize database
mysql -u root -p < 1_database.sql
mysql -u root -p ideav < 2_table.sql

# 5. Start the application
source venv/bin/activate
python app.py
```

The application will be available at `http://localhost:5000`

---

## Detailed Installation

### Step 1: Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/ideav/local.git
cd local

# Or download as ZIP and extract
wget https://github.com/ideav/local/archive/refs/heads/main.zip
unzip main.zip
cd local-main
```

### Step 2: Create Python Virtual Environment

A virtual environment isolates the application's dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your prompt
```

### Step 3: Install Python Dependencies

```bash
# Ensure virtual environment is activated
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

**Required packages:**
- Flask 3.0.0 - Web framework
- PyMySQL 1.1.0 - MySQL database driver
- Flask-CORS 4.0.0 - Cross-Origin Resource Sharing support
- python-dotenv 1.0.0 - Environment variable management
- Werkzeug 3.0.1 - WSGI utilities

### Step 4: Create Necessary Directories

```bash
# Create directories for logs and uploads
mkdir -p logs
mkdir -p download
mkdir -p download/ideav

# Set appropriate permissions
chmod 755 logs download
chmod 755 download/ideav
```

---

## Configuration

### Step 1: Create Environment File

```bash
# Copy example configuration
cp .env.example .env
```

### Step 2: Edit Configuration

Edit the `.env` file with your preferred text editor:

```bash
nano .env
# or
vim .env
# or
code .env
```

### Configuration Options

```bash
# Database Configuration
DB_HOST=localhost          # MySQL host (use 'localhost' for local installation)
DB_USER=ideav             # Database username (created by 1_database.sql)
DB_PASSWORD=ideav         # Database password (change in production!)
DB_NAME=ideav             # Database name

# Application Configuration
SECRET_KEY=your-secret-key-here    # Change this to a random string in production
SALT=your-salt-here                # Change this to a random string in production
FLASK_ENV=production               # Use 'development' for debugging
FLASK_DEBUG=0                      # Set to 1 for development mode
```

**Important Security Notes:**
- ⚠️ Change `SECRET_KEY` and `SALT` in production environments
- ⚠️ Use strong passwords for database credentials
- ⚠️ Never commit `.env` file to version control (it's in `.gitignore`)

### Generating Secure Keys

```bash
# Generate random secret key (Python)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate random salt
python3 -c "import secrets; print(secrets.token_hex(16))"
```

---

## Database Setup

### Step 1: Prepare MySQL

```bash
# Start MySQL service if not running
sudo systemctl start mysql

# Access MySQL console
mysql -u root -p
```

### Step 2: Run Database Scripts

The repository includes two SQL scripts:

1. **1_database.sql** - Creates the database and user
2. **2_table.sql** - Creates tables and initial data

```bash
# Run from command line (recommended)
mysql -u root -p < 1_database.sql
mysql -u root -p ideav < 2_table.sql

# Or from MySQL console
mysql> source 1_database.sql;
mysql> use ideav;
mysql> source 2_table.sql;
```

### Step 3: Verify Database Setup

```bash
# Connect to verify
mysql -u ideav -p
# Password: ideav (or your custom password)

# Check tables
mysql> USE ideav;
mysql> SHOW TABLES;
mysql> SELECT COUNT(*) FROM ideav;
mysql> EXIT;
```

You should see the `ideav` table with initial data rows.

### Multiple Databases (Optional)

To create additional databases for different projects:

```bash
# Edit 2_table.sql before running
# Replace all instances of 'ideav' with your new database name
sed 's/ideav/myproject/g' 2_table.sql > 2_table_myproject.sql

# Create new database
mysql -u root -p -e "CREATE DATABASE myproject;"
mysql -u root -p myproject < 2_table_myproject.sql
```

---

## Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Set development environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run the application
python app.py
```

The application will start on `http://localhost:5000` with:
- Auto-reload on code changes
- Detailed error messages
- Debug toolbar

### Production Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Ensure production settings in .env
export FLASK_ENV=production
export FLASK_DEBUG=0

# Run with production server (see Production Deployment section)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Running as Background Service

```bash
# Using nohup
nohup python app.py > logs/app.log 2>&1 &

# Using screen
screen -S ideav
python app.py
# Press Ctrl+A, then D to detach

# Using systemd (see Production Deployment section)
```

---

## Production Deployment

### Option 1: Gunicorn (Recommended)

Gunicorn is a production-ready WSGI server:

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With additional options
gunicorn -w 4 \
  --bind 0.0.0.0:5000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  app:app
```

**Worker calculation:** Number of workers = (2 × CPU cores) + 1

### Option 2: uWSGI

```bash
# Install uWSGI
pip install uwsgi

# Run uWSGI
uwsgi --http :5000 \
  --wsgi-file app.py \
  --callable app \
  --processes 4 \
  --threads 2
```

### Option 3: Systemd Service

Create a systemd service file for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/ideav.service
```

Add the following content:

```ini
[Unit]
Description=IdeaV Local Application
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/local
Environment="PATH=/path/to/local/venv/bin"
ExecStart=/path/to/local/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable ideav

# Start the service
sudo systemctl start ideav

# Check status
sudo systemctl status ideav

# View logs
sudo journalctl -u ideav -f
```

### Nginx Reverse Proxy

Use Nginx as a reverse proxy for better performance:

```bash
# Install Nginx
sudo apt-get install nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/ideav
```

Add configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/local/static;
        expires 30d;
    }

    location /download {
        alias /path/to/local/download;
        internal;
    }

    client_max_body_size 50M;
}
```

Enable the site:

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/ideav /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### SSL/HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## Verification & Testing

### Basic Connectivity Test

```bash
# Test if application is running
curl http://localhost:5000/

# Should return HTML content
```

### Database Connection Test

```bash
# Activate virtual environment
source venv/bin/activate

# Run Python test
python3 << EOF
from database import get_db_connection
try:
    conn = get_db_connection('ideav')
    print("✓ Database connection successful")
    conn.close()
except Exception as e:
    print(f"✗ Database connection failed: {e}")
EOF
```

### API Endpoint Tests

```bash
# Test API endpoints
# List objects
curl http://localhost:5000/api/ideav/objects

# Get specific object
curl http://localhost:5000/api/ideav/objects/1

# Create object (requires authentication)
curl -X POST http://localhost:5000/api/ideav/objects \
  -H "Content-Type: application/json" \
  -d '{"t": 3, "up": 0, "ord": 0, "val": "Test"}'
```

### File Upload Test

Access `http://localhost:5000/ideav/upload` in your browser and test file upload functionality.

### Smoke Test Checklist

- [ ] Application starts without errors
- [ ] Homepage loads successfully
- [ ] Database connection works
- [ ] Can view objects
- [ ] Can create new objects
- [ ] Can edit objects
- [ ] Can delete objects
- [ ] File upload works
- [ ] File download works
- [ ] Reports generate correctly

---

## Troubleshooting

### Application Won't Start

**Error: `ModuleNotFoundError`**
```bash
# Solution: Ensure virtual environment is activated and packages installed
source venv/bin/activate
pip install -r requirements.txt
```

**Error: `Address already in use`**
```bash
# Solution: Port 5000 is occupied
# Find process using port
sudo lsof -i :5000
# Kill process or use different port
python app.py  # Edit port in app.py if needed
```

### Database Connection Errors

**Error: `Access denied for user`**
```bash
# Solution: Check database credentials
# Verify .env file settings
# Test MySQL connection manually
mysql -u ideav -p
```

**Error: `Unknown database`**
```bash
# Solution: Database not created
mysql -u root -p < 1_database.sql
mysql -u root -p ideav < 2_table.sql
```

**Error: `Can't connect to MySQL server`**
```bash
# Solution: MySQL not running
sudo systemctl start mysql
sudo systemctl status mysql
```

### Permission Errors

**Error: `Permission denied` on logs/ or download/**
```bash
# Solution: Fix directory permissions
chmod 755 logs download
chown -R $USER:$USER logs download
```

### File Upload Issues

**Error: `413 Request Entity Too Large`**
```bash
# Solution: Increase max upload size
# In config.py, increase MAX_CONTENT_LENGTH
# If using Nginx, add to nginx config:
client_max_body_size 50M;
```

**Error: `No such file or directory`**
```bash
# Solution: Create upload directories
mkdir -p download/ideav
chmod 755 download/ideav
```

### Performance Issues

**Slow response times**
```bash
# Solutions:
# 1. Use production WSGI server (Gunicorn/uWSGI)
# 2. Increase worker processes
# 3. Enable database query caching
# 4. Add Nginx caching
# 5. Monitor resource usage: htop
```

### Viewing Logs

```bash
# Application logs
tail -f logs/app.log

# If using systemd
sudo journalctl -u ideav -f

# If using Gunicorn
tail -f logs/access.log
tail -f logs/error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Security Considerations

### Production Security Checklist

- [ ] Change default database password
- [ ] Generate strong SECRET_KEY and SALT
- [ ] Set FLASK_DEBUG=0 in production
- [ ] Use HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Restrict MySQL remote access
- [ ] Set proper file permissions
- [ ] Keep software updated
- [ ] Configure backup strategy
- [ ] Monitor logs for suspicious activity

### Firewall Configuration

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### MySQL Security

```bash
# Run MySQL security script
sudo mysql_secure_installation

# Restrict MySQL to localhost
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# Add or verify:
bind-address = 127.0.0.1

# Restart MySQL
sudo systemctl restart mysql
```

### File Permissions

```bash
# Set secure permissions
chmod 600 .env              # Environment variables
chmod 755 logs download     # Writable directories
chmod 644 *.py              # Python files
chmod 755 setup.sh          # Executable scripts
```

---

## Maintenance

### Backup Strategy

**Database Backup**
```bash
# Create backup script
nano backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u ideav -p ideav > "$BACKUP_DIR/ideav_$DATE.sql"
gzip "$BACKUP_DIR/ideav_$DATE.sql"
# Keep only last 30 days
find "$BACKUP_DIR" -name "ideav_*.sql.gz" -mtime +30 -delete
```

```bash
# Make executable
chmod +x backup.sh

# Add to crontab for daily backups
crontab -e
# Add line:
0 2 * * * /path/to/backup.sh
```

**Application Backup**
```bash
# Backup application files
tar -czf ideav_app_backup_$(date +%Y%m%d).tar.gz \
  --exclude='venv' \
  --exclude='logs' \
  --exclude='*.pyc' \
  /path/to/local
```

### Updates and Upgrades

**Update Python Dependencies**
```bash
# Activate virtual environment
source venv/bin/activate

# Update all packages
pip install --upgrade -r requirements.txt

# Or update specific package
pip install --upgrade Flask
```

**Update Application Code**
```bash
# Pull latest changes
git pull origin main

# Restart application
sudo systemctl restart ideav
```

### Monitoring

**Monitor Application Status**
```bash
# Check if service is running
sudo systemctl status ideav

# Monitor resource usage
htop

# Check disk space
df -h

# Check memory usage
free -h
```

**Monitor Logs**
```bash
# Watch application logs in real-time
tail -f logs/app.log

# Check for errors
grep ERROR logs/app.log

# Monitor system logs
sudo journalctl -u ideav --since "1 hour ago"
```

### Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/ideav
```

```
/path/to/local/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 www-data www-data
}
```

---

## Additional Resources

### Documentation
- [README_PYTHON.md](README_PYTHON.md) - Detailed Python version documentation
- [README.md](README.md) - Original PHP version documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyMySQL Documentation](https://pymysql.readthedocs.io/)

### Support
- GitHub Issues: https://github.com/ideav/local/issues
- Application logs: `logs/app.log`
- Database logs: Check MySQL error logs

### Useful Commands

```bash
# Check what's listening on port 5000
sudo netstat -tlnp | grep 5000

# Check Python version
python3 --version

# List installed packages
pip list

# Check MySQL status
sudo systemctl status mysql

# View active connections
mysqladmin -u root -p processlist

# Check application process
ps aux | grep python

# Monitor network traffic
sudo tcpdump -i any port 5000
```

---

## Summary

You should now have a fully functional IdeaV Local installation. The application provides:

- ✅ Database-driven object management
- ✅ File upload and download capabilities
- ✅ Custom report generation
- ✅ RESTful API endpoints
- ✅ Web interface for all operations

For any issues not covered in this guide, please:
1. Check the troubleshooting section
2. Review application logs
3. Consult the README_PYTHON.md documentation
4. Open an issue on GitHub

**Happy implementing!**
