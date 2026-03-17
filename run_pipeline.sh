#!/bin/bash

# 1. SETUP ENVIRONMENT
echo "--- Initializing Video CDN Pipeline ---"
BASE_DIR=$(pwd)
LOCAL_DIR="$BASE_DIR/.local"
NGINX_PATH="/c/nginx/nginx.exe" # UPDATE THIS to your actual Nginx path

# 2. CREATE NECESSARY DIRECTORIES
mkdir -p "$LOCAL_DIR/raw_uploads"
mkdir -p "$LOCAL_DIR/processed"
echo "Directories created in .local/"

# 3. INSTALL DEPENDENCIES
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found."
    exit 1
fi

# 4. START NGINX
# We start Nginx in the background using the specific config provided
if [ -f "$BASE_DIR/server/nginx.conf" ]; then
    echo "Starting Nginx..."
    # Using 'start' on Windows/Git Bash to run Nginx without blocking the script
    "$NGINX_PATH" -c "$BASE_DIR/server/nginx.conf" &
else
    echo "Warning: server/nginx.conf not found. Nginx not started."
fi

# 5. START PYTHON PIPELINE
echo "Starting Python Watcher..."
echo "To stop the pipeline, press CTRL+C"
python main.py