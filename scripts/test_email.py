import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_smtp():
    print("--- COMPUPARTZ SMTP DIAGNOSTIC ---")
    print(f"HOST: {settings.EMAIL_HOST}")
    print(f"PORT: {settings.EMAIL_PORT}")
    print(f"USER: {settings.EMAIL_HOST_USER}")
    print(f"TLS: {settings.EMAIL_USE_TLS}")
    print(f"SSL: {settings.EMAIL_USE_SSL}")
    print("-" * 30)

    try:
        print("Attempting to send test email to support@compupartz.com...")
        send_mail(
            'SMTP Diagnostic Test',
            'This is a test email from your Compupartz VPS to verify SMTP settings.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER], # Sending to self for test
            fail_silently=False,
        )
        print("\n✅ SUCCESS! Email sent successfully.")
        print("Please check your Hostinger inbox (including Spam folder).")
    except Exception as e:
        print("\n❌ FAILED!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("\n--- TROUBLESHOOTING TIPS ---")
        if "Authentication failed" in str(e) or "authentication error" in str(e).lower():
            print("1. Your password in .env might be incorrect.")
        elif "Connection refused" in str(e) or "Timeout" in str(e):
            print("1. Your VPS firewall might be blocking Port 465/587.")
            print("2. Try switching between Port 465 (SSL=True) and Port 587 (TLS=True).")
        else:
            print("1. Check if Hostinger requires an 'App Password' instead of your main password.")

if __name__ == "__main__":
    test_smtp()
