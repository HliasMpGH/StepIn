#!/bin/bash

# Make sure Docker and Docker Compose are installed
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker and Docker Compose are required but not installed."
    echo "Please install them first:"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# First build the frontend
echo "Building frontend..."
./build-frontend.sh

if [ $? -ne 0 ]; then
    echo "Frontend build failed. Aborting deployment."
    exit 1
fi

# Stop any existing containers and remove them
echo "Stopping any existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build and start the containers in detached mode
echo "Building and starting containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# Display the status of the containers
echo ""
echo "Container status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "StepIn is now running in production mode!"
echo "Access the web interface at http://localhost:8000"
echo "API documentation is available at http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "To stop: docker-compose -f docker-compose.prod.yml down"