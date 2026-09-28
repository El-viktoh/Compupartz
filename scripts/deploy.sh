#!/bin/bash
set -e

# --- CONFIGURATION ---
PROJECT_DIR="/var/www/django-app/Compupartz"
VENV_DIR="/var/www/django-app/Compupartz/venv"

echo "🚀 Starting Bulletproof Deployment..."

# 0. Ensure parent directories are traversable (Crucial for OpenLiteSpeed)
echo "🔒 Securing parent directory access..."
chmod 755 /var/www || true
chmod 755 /var/www/django-app || true

# 1. Navigate to project directory and ensure git is happy with ownership
cd $PROJECT_DIR
git config --global --add safe.directory $PROJECT_DIR

# 2. Synchronize with GitHub
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
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install -r requirements.txt

# 5. Run migrations
echo "🗄️ Running migrations..."
$VENV_DIR/bin/python manage.py migrate --noinput

# 6. Collect static files
echo "🎨 Collecting static files..."
$VENV_DIR/bin/python manage.py collectstatic --noinput

# 7. Stabilize Logs and Database
echo "📝 Stabilizing log files and database..."
mkdir -p $PROJECT_DIR/logs
touch $PROJECT_DIR/logs/error.log
touch $PROJECT_DIR/stderr.log
touch $PROJECT_DIR/django_errors.log
touch $PROJECT_DIR/db.sqlite3

# 8. Ownership and permissions lock
echo "🔐 Setting permissions..."
chown -R nobody:nogroup $PROJECT_DIR
chmod -R 775 $PROJECT_DIR
chmod 666 $PROJECT_DIR/logs/error.log $PROJECT_DIR/stderr.log $PROJECT_DIR/django_errors.log 2>/dev/null || true
chmod 666 $PROJECT_DIR/db.sqlite3* 2>/dev/null || true
chown nobody:nogroup $PROJECT_DIR/db.sqlite3* 2>/dev/null || true
chown nobody:nogroup $PROJECT_DIR/django_errors.log 2>/dev/null || true

# 9. Django Health Check
echo "🧪 Running Django self-check..."
$VENV_DIR/bin/python manage.py check
$VENV_DIR/bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.test import Client
c = Client()
res = c.get('/', HTTP_HOST='compupartz.com')
print(f'Internal Django Check Status: {res.status_code}')
if res.status_code != 200:
    raise SystemExit(f'Django returned status {res.status_code}')
"

# 10. Restart Web Server & Workers
echo "🔄 Forcing fresh lswsgi and worker restart..."
killall -9 lswsgi 2>/dev/null || true
pkill -9 -f lswsgi || true
pkill -9 -f "python.*Compupartz" || true
pkill -9 -f "fcgi-bin/lswsgi" || true

touch $PROJECT_DIR/config/wsgi.py
touch /tmp/lshttpd/lsup.eval 2>/dev/null || true

if [ -x "/usr/local/lsws/bin/lswsctrl" ]; then
    echo "Restarting via /usr/local/lsws/bin/lswsctrl restart..."
    /usr/local/lsws/bin/lswsctrl restart || true
elif command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet lsws; then
    echo "Restarting via systemctl restart lsws..."
    systemctl restart lsws || true
elif command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet openlitespeed; then
    echo "Restarting via systemctl restart openlitespeed..."
    systemctl restart openlitespeed || true
fi

# 11. Verification Check
echo "🩺 Verifying live site response..."
sleep 6
rm -f $PROJECT_DIR/staticfiles/debug.txt 2>/dev/null || true
HTTP_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" https://compupartz.com/ || true)
echo "Live site HTTP status: $HTTP_CODE"

if [ "$HTTP_CODE" != "200" ]; then
    echo "⚠️ Live check returned $HTTP_CODE. Showing recent error logs..."
    tail -n 30 $PROJECT_DIR/stderr.log 2>/dev/null || true
    tail -n 30 $PROJECT_DIR/django_errors.log 2>/dev/null || true
fi

echo "✅ Deployment Process Finished!"
