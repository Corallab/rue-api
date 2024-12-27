#!/bin/bash

# Pull the latest changes from the repository
cd /home/appuser/rue-api/backend
git pull origin main

# Activate the virtual environment
source /home/appuser/rue-api/backend/venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart the server (e.g., Gunicorn, Nginx, etc.)
sudo systemctl restart rue-api
