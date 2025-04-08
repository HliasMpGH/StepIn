#!/bin/bash

# Build the Vue.js frontend for production

# Check if Node.js and npm are installed
if ! command -v npm &> /dev/null; then
    echo "Error: Node.js and npm are required but not installed."
    echo "Please install them first from https://nodejs.org/"
    exit 1
fi

# Navigate to the frontend directory
cd "$(dirname "$0")/frontend"

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Build for production
echo "Building frontend for production..."
npm run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Frontend built successfully!"
    echo "The build output is in the static/frontend directory."
    echo "You can now start the backend server which will serve the frontend."
else
    echo "Frontend build failed. Please check the errors above."
    exit 1
fi

# Return to the original directory
cd -