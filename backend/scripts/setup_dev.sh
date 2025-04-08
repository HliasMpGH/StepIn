#!/bin/bash

# Create development environment

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check if .env file exists, create from example if not
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Initialize SQLite database
echo "Creating SQLite database..."
python -c "
from app.db.database import Database
db = Database()
db.init_db()
print('Database initialized successfully')
"

echo "Development environment setup complete!"
echo "Run 'source venv/bin/activate' to activate the virtual environment"
echo "Run 'uvicorn app.main:app --reload' to start the development server"