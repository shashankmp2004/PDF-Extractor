#!/bin/bash

# Build script for PDF Extractor
# This builds the Docker image according to the competition requirements

IMAGE_NAME="pdf-extractor:latest"

echo "Building Docker image: $IMAGE_NAME"
docker build --platform linux/amd64 -t $IMAGE_NAME .

echo "Build completed!"
echo ""
echo "To run the container:"
echo "docker run --rm -v \$(pwd)/input:/app/input -v \$(pwd)/output:/app/output --network none $IMAGE_NAME"
