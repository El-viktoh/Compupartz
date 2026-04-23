from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import logging

logger = logging.getLogger(__name__)

def send_activation_email(user, domain):
    try:
        mail_subject = 'Verify Your Compupartz Account'
        message = render_to_string('registration/account_activation_email.html', {
            'user': user,
            'domain': domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        
        email = EmailMessage(
            mail_subject, message, to=[user.email]
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
        return True
    except Exception as e:
        logger.error(f"Activation Email Error: {str(e)}")
        return False
