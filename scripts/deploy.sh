#!/bin/bash
set -e

# --- CONFIGURATION ---
PROJECT_DIR="/var/www/django-app/Compupartz"
VENV_DIR="/var/www/django-app/Compupartz/venv"

echo "🚀 Starting Deployment..."

# 1. Navigate to project directory
cd $PROJECT_DIR

# 2. Pull latest code from GitHub
echo "📥 Pulling latest code..."
git pull origin main

# 3. Activate virtual environment
echo "🐍 Activating virtual environment..."
source $VENV_DIR/bin/activate

# 4. Install/Update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 5. Run migrations
echo "🗄️ Running migrations..."
python manage.py migrate --noinput

# 6. Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# 7. Restart OpenLiteSpeed (by touching wsgi.py)
# OpenLiteSpeed's Django worker usually detects changes to wsgi.py
echo "🔄 Restarting Django worker..."
touch config/wsgi.py

echo "✅ Deployment Successful!"
