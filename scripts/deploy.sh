#!/bin/bash
set -e

# --- CONFIGURATION ---
PROJECT_DIR="/var/www/django-app/Compupartz"
VENV_DIR="/var/www/django-app/Compupartz/venv"

echo "🚀 Starting Bulletproof Deployment..."

# 0. Ensure parent directories are traversable (Crucial for OpenLiteSpeed)
echo "🔒 Securing parent directory access..."
chmod 755 /var/www
chmod 755 /var/www/django-app

# 1. Navigate to project directory and ensure git is happy with ownership
cd $PROJECT_DIR
git config --global --add safe.directory $PROJECT_DIR

# 2. Synchronize with GitHub
echo "📥 Fetching latest code..."
git fetch origin main
git reset --hard origin/main

# 2.5 EARLY PERMISSION FIX (To prevent 500 error during install/migrate)
echo "🔐 Setting interim permissions..."
chown -R nobody:nogroup $PROJECT_DIR
chmod -R 775 $PROJECT_DIR

# 3. Ensure virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "🛠️ Creating virtual environment..."
    python3 -m venv $VENV_DIR
    chown -R nobody:nogroup $VENV_DIR
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

# 7. Stabilize Logs
echo "📝 Stabilizing log files..."
mkdir -p $PROJECT_DIR/logs
touch $PROJECT_DIR/logs/error.log
touch $PROJECT_DIR/stderr.log
chown nobody:nogroup $PROJECT_DIR/stderr.log
chown -R nobody:nogroup $PROJECT_DIR/logs

# 8. Force Restart Django worker
echo "🔄 Forcing fresh worker restart..."
pkill -9 python || true
touch config/wsgi.py

# 9. FINAL PERMISSION LOCK (MUST BE LAST)
echo "🔐 Finalizing permissions..."
chown -R nobody:nogroup $PROJECT_DIR
chmod -R 775 $PROJECT_DIR
chmod 664 $PROJECT_DIR/db.sqlite3 || true

echo "✅ Deployment Successful and Stable!"
