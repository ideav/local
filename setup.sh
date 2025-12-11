#!/bin/bash

# Setup script for IdeaV Python version

echo "========================================="
echo "IdeaV Python Installation Script"
echo "========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
fi
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi
echo "✓ Virtual environment activated"
echo ""

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install requirements."
    exit 1
fi
echo "✓ Python packages installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠️  Please edit .env file to configure your database settings"
else
    echo "✓ .env file already exists"
fi
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p download
mkdir -p download/ideav
echo "✓ Directories created"
echo ""

# Check MySQL connection
echo "Checking MySQL connection..."
if command -v mysql &> /dev/null; then
    echo "MySQL client found. You can now run the database setup scripts:"
    echo "  mysql -u root -p < 1_database.sql"
    echo "  mysql -u root -p ideav < 2_table.sql"
else
    echo "⚠️  MySQL client not found. Please install MySQL client to set up the database."
fi
echo ""

echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials"
echo "2. Run the database setup scripts (if not already done)"
echo "3. Activate the virtual environment: source venv/bin/activate"
echo "4. Start the application: python app.py"
echo ""
echo "The application will be available at http://localhost:5000"
echo ""
