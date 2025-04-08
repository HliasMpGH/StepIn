#!/bin/bash

# Create directory for scripts
mkdir -p $(dirname "$0")

# Check if Python virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests with coverage
echo "Running tests..."
pytest --cov=app tests/

# Generate coverage report
echo "Generating coverage report..."
coverage html

echo "Tests completed. View coverage report in htmlcov/index.html"