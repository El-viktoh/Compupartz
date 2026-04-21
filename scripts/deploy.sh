#!/bin/bash
set -e

# --- CONFIGURATION ---
PROJECT_DIR="/var/www/django-app/Compupartz"
VENV_DIR="/var/www/django-app/Compupartz/venv"

echo "🚀 Starting Deployment..."

# 1. Navigate to project directory and ensure git is happy with ownership
cd $PROJECT_DIR
git config --global --add safe.directory $PROJECT_DIR

# 2. Synchronize with GitHub (Force overwrite local changes)
echo "📥 Fetching latest code..."
git fetch origin main
git reset --hard origin/main

# 3. Ensure virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "🛠️ Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# 4. Install/Update dependencies
echo "📦 Installing dependencies..."
$VENV_DIR/bin/pip install -r requirements.txt

# 5. Run migrations
echo "🗄️ Running migrations..."
$VENV_DIR/bin/python manage.py migrate --noinput

# 6. Collect static files
echo "🎨 Collecting static files..."
$VENV_DIR/bin/python manage.py collectstatic --noinput

# 7. Restart OpenLiteSpeed (by touching wsgi.py)
# OpenLiteSpeed's Django worker usually detects changes to wsgi.py
echo "🔄 Restarting Django worker..."
touch config/wsgi.py

echo "✅ Deployment Successful!"
