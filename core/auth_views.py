import hashlib

from django.contrib.auth.views import PasswordResetView
from django.core.cache import cache
from django.http import HttpResponseRedirect


class ThrottledPasswordResetView(PasswordResetView):
    """Password reset that sends a real multipart email and caps requests per address."""

    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'

    max_requests_per_hour = 3

    def form_valid(self, form):
        email = form.cleaned_data['email'].strip().lower()
        key = 'pwreset:' + hashlib.sha256(email.encode()).hexdigest()
        cache.add(key, 0, 3600)
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, 3600)
            count = 1
        if count > self.max_requests_per_hour:
            # Same response as a normal request so nothing is revealed to the requester.
            return HttpResponseRedirect(self.get_success_url())
        return super().form_valid(form)
