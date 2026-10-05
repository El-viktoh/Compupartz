from django.test import TestCase, Client
from django.urls import reverse
from core.models import FAQ

class FAQHomepageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_published_faqs_appear_on_homepage(self):
        faq1 = FAQ.objects.create(
            question="Can I bring in custom laptop parts for installation?",
            answer="Yes, we can install customer-provided parts after inspecting compatibility.",
            is_published=True
        )
        faq2 = FAQ.objects.create(
            question="Internal secret question not yet ready?",
            answer="Draft answer.",
            is_published=False
        )

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Can I bring in custom laptop parts for installation?")
        self.assertContains(response, "Yes, we can install customer-provided parts after inspecting compatibility.")
        self.assertNotContains(response, "Internal secret question not yet ready?")

    def test_updating_faq_in_admin_reflects_on_homepage(self):
        faq = FAQ.objects.create(
            question="Do you fix liquid-damaged motherboards?",
            answer="Initial answer about ultrasonic cleaning.",
            is_published=True
        )

        # Initial check
        res1 = self.client.get(reverse('home'))
        self.assertContains(res1, "Do you fix liquid-damaged motherboards?")
        self.assertContains(res1, "Initial answer about ultrasonic cleaning.")

        # Simulate update via Django Admin
        faq.question = "Do you specialize in MacBook ultrasonic liquid repair?"
        faq.answer = "Yes, we perform component-level microsoldering and ultrasonic board cleaning."
        faq.save()

        res2 = self.client.get(reverse('home'))
        self.assertNotContains(res2, "Do you fix liquid-damaged motherboards?")
        self.assertContains(res2, "Do you specialize in MacBook ultrasonic liquid repair?")
        self.assertContains(res2, "Yes, we perform component-level microsoldering and ultrasonic board cleaning.")

    def test_unpublishing_faq_removes_it_from_homepage(self):
        faq = FAQ.objects.create(
            question="Is rush repair available?",
            answer="Yes, same-day expedited service is offered.",
            is_published=True
        )

        res1 = self.client.get(reverse('home'))
        self.assertContains(res1, "Is rush repair available?")

        # Unpublish
        faq.is_published = False
        faq.save()

        res2 = self.client.get(reverse('home'))
        self.assertNotContains(res2, "Is rush repair available?")

    def test_empty_faqs_renders_fallback_message(self):
        # With no published FAQs
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No frequently asked questions published at this time.")


from django.contrib.auth.models import User
from django.core import mail


class RegistrationSecurityTests(TestCase):
    def _signup(self, email, username):
        return self.client.post(reverse('signup'), {
            'username': username, 'first_name': 'A', 'last_name': 'B', 'email': email,
            'password1': 'Str0ng-Pass-9981!', 'password2': 'Str0ng-Pass-9981!',
        })

    def test_duplicate_email_signup_is_blocked_case_insensitively(self):
        User.objects.create_user('first', 'dupe@example.com', 'x')
        resp = self._signup('DUPE@Example.com', 'second')
        self.assertContains(resp, "already exists")
        self.assertFalse(User.objects.filter(username='second').exists())

    def test_unique_email_signup_still_works(self):
        self._signup('fresh@example.com', 'fresh')
        self.assertTrue(User.objects.filter(username='fresh').exists())

    def test_social_buttons_use_login_process_not_connect(self):
        for name in ('signup', 'login'):
            html = self.client.get(reverse(name)).content.decode()
            self.assertNotIn('process=connect', html)
            self.assertIn('/accounts/google/login/?process=login', html)
            self.assertIn('/accounts/microsoft/login/?process=login', html)
            self.assertNotIn('apple', html.lower().replace('apple-touch', '').replace('-apple-system', ''))
            self.assertNotIn('twitter_oauth2', html)

    def test_apple_and_x_login_routes_are_gone(self):
        for path in ('/accounts/apple/login/', '/accounts/twitter_oauth2/login/'):
            self.assertEqual(self.client.get(path).status_code, 404, path)
        self.assertEqual(self.client.get('/accounts/google/login/').status_code, 302)
        self.assertEqual(self.client.get('/accounts/microsoft/login/').status_code, 302)


class ProfileUpdateFeedbackTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', 'owner@example.com', 'x')
        User.objects.create_user('other', 'taken@example.com', 'x')
        self.client.force_login(self.owner)

    def test_duplicate_email_is_rejected_with_visible_error(self):
        resp = self.client.post(reverse('update_profile'), {
            'first_name': 'O', 'last_name': 'W', 'email': 'taken@example.com'}, follow=True)
        self.assertContains(resp, "Another account is already using this email")
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.email, 'owner@example.com')

    def test_valid_update_shows_success(self):
        resp = self.client.post(reverse('update_profile'), {
            'first_name': 'New', 'last_name': 'Name', 'email': 'owner2@example.com'}, follow=True)
        self.assertContains(resp, "updated successfully")


class TestimonialRedirectTests(TestCase):
    def _post(self, **extra):
        data = {'quote': 'Great service', 'name': 'T', 'rating': '5'}
        data.update(extra.pop('data', {}))
        return self.client.post(reverse('submit_testimonial'), data, **extra)

    def test_external_next_is_not_followed(self):
        for target in ('https://evil.example.com/x', '//evil.example.com', 'javascript:alert(1)'):
            self.assertEqual(self._post(data={'next': target})['Location'], reverse('reviews'))

    def test_internal_next_is_followed(self):
        self.assertEqual(self._post(data={'next': '/repair/'})['Location'], '/repair/')


class EmailEscapingTests(TestCase):
    def test_user_supplied_html_is_escaped_in_status_emails(self):
        from repair.models import RepairTicket
        t = RepairTicket.objects.create(
            customer_name='<script>alert(1)</script>', customer_email='c@example.com',
            customer_phone='0200000000', device='<img src=x onerror=alert(2)>')
        mail.outbox.clear()
        t.status = 'in_progress'
        t.save()
        bodies = ''.join(str(m.alternatives) + m.body for m in mail.outbox)
        self.assertNotIn('<script>alert(1)', bodies)
        self.assertNotIn('<img src=x onerror', bodies)


class TestimonialModerationTests(TestCase):
    def _submit(self, **extra):
        return self.client.post(reverse('submit_testimonial'), {
            'quote': 'Brilliant repair work', 'name': 'Ama', 'rating': '5'}, follow=True, **extra)

    def test_guest_review_is_held_for_moderation(self):
        from core.models import Testimonial
        resp = self._submit()
        t = Testimonial.objects.get(name='Ama')
        self.assertFalse(t.is_approved)
        self.assertContains(resp, "once our team has approved it")
        self.assertNotContains(self.client.get(reverse('reviews')), 'Brilliant repair work')
        self.assertNotContains(self.client.get(reverse('home')), 'Brilliant repair work')

    def test_logged_in_review_is_also_held_for_moderation(self):
        from core.models import Testimonial
        self.client.force_login(User.objects.create_user('member', 'm@example.com', 'x'))
        self._submit()
        self.assertFalse(Testimonial.objects.get(name='Ama').is_approved)

    def test_admin_approve_action_publishes_the_review(self):
        from core.models import Testimonial
        self._submit()
        t = Testimonial.objects.get(name='Ama')
        admin_user = User.objects.create_superuser('boss', 'boss@example.com', 'x')
        self.client.force_login(admin_user)
        self.client.post(reverse('admin:core_testimonial_changelist'), {
            'action': 'approve_testimonials', '_selected_action': [t.pk]})
        t.refresh_from_db()
        self.assertTrue(t.is_approved)
        self.client.logout()
        self.assertContains(self.client.get(reverse('reviews')), 'Brilliant repair work')

    def test_staff_notification_email_says_awaiting_approval(self):
        self._submit()
        body = ''.join(m.body for m in mail.outbox)
        self.assertIn('Awaiting Approval', body)


class EmailLinkSchemeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('linkuser', 'link@example.com', 'x')

    def test_password_reset_link_uses_https_for_secure_requests(self):
        self.client.post(reverse('password_reset'), {'email': 'link@example.com'}, secure=True)
        from django.contrib.sites.models import Site
        domain = Site.objects.get_current().domain
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn(f'https://{domain}/accounts/reset/', mail.outbox[0].body)
        self.assertIn('href="https://', html)
        self.assertNotIn('href="http://', html)
        self.assertNotIn(f'http://{domain}', mail.outbox[0].body)

    def test_activation_link_uses_https_in_production(self):
        from django.test import override_settings
        from core.utils import send_activation_email
        with override_settings(DEBUG=False):
            send_activation_email(self.user, 'compupartz.com')
        self.assertIn('href="https://compupartz.com/activate/', mail.outbox[0].body)
        self.assertNotIn('href="http://', mail.outbox[0].body)


import re


class PasswordResetFlowTests(TestCase):
    OLD, NEW = 'Old-Passw0rd-4471!', 'Brand-New-Pass-2290!'

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.user = User.objects.create_user('resetter', 'resetter@example.com', self.OLD)

    def _request_reset(self, email='resetter@example.com'):
        return self.client.post(reverse('password_reset'), {'email': email}, secure=True)

    def _link(self):
        import re
        return re.search(r'(https://\S+/accounts/reset/\S+?/)\s', mail.outbox[0].body + ' ').group(1)

    def test_email_is_multipart_with_readable_text_and_html(self):
        self._request_reset()
        msg = mail.outbox[0]
        self.assertEqual(msg.alternatives[0][1], 'text/html')
        self.assertNotIn('<', msg.body)
        self.assertIn('href="https://', msg.alternatives[0][0])

    def test_full_reset_changes_password_and_kills_old_sessions(self):
        other = self.client_class()
        other.login(username='resetter', password=self.OLD)
        self._request_reset()
        link = self._link()
        resp = self.client.get(re.sub(r'^https://[^/]+', '', link), secure=True, follow=True)
        set_url = resp.redirect_chain[-1][0]
        done = self.client.post(set_url, {'new_password1': self.NEW, 'new_password2': self.NEW}, secure=True)
        self.assertEqual(done.status_code, 302)
        self.assertTrue(self.client_class().login(username='resetter', password=self.NEW))
        self.assertFalse(self.client_class().login(username='resetter', password=self.OLD))
        self.assertEqual(other.get(reverse('dashboard')).status_code, 302)

    def test_weak_or_mismatched_passwords_are_rejected(self):
        self._request_reset()
        resp = self.client.get(re.sub(r'^https://[^/]+', '', self._link()), secure=True, follow=True)
        set_url = resp.redirect_chain[-1][0]
        for p1, p2 in [(self.NEW, 'Different-Pass-1!'), ('Ab1!', 'Ab1!'), ('83920174651', '83920174651'), ('password123', 'password123')]:
            self.assertEqual(self.client.post(set_url, {'new_password1': p1, 'new_password2': p2}, secure=True).status_code, 200)
        self.assertTrue(self.client_class().login(username='resetter', password=self.OLD))

    def test_unknown_unverified_and_social_only_accounts_get_no_email_and_same_response(self):
        User.objects.create_user('inactive', 'inactive@example.com', self.OLD, is_active=False)
        social = User.objects.create_user('socialonly', 'social@example.com')
        social.set_unusable_password()
        social.save()
        known = self._request_reset()['Location']
        for email in ('inactive@example.com', 'social@example.com', 'nobody@example.com'):
            mail.outbox.clear()
            self.assertEqual(self._request_reset(email)['Location'], known)
            self.assertEqual(len(mail.outbox), 0, email)

    def test_requests_are_throttled_per_address_without_revealing_it(self):
        responses = {self._request_reset('Resetter@Example.com ')['Location'] for _ in range(8)}
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(len(responses), 1)

    def test_expired_token_is_rejected(self):
        from django.test import override_settings
        self._request_reset()
        link = re.sub(r'^https://[^/]+', '', self._link())
        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            resp = self.client.get(link, secure=True, follow=True)
        self.assertNotIn('set-password', resp.redirect_chain[-1][0] if resp.redirect_chain else '')


class CsrfFailurePageTests(TestCase):
    def test_stale_token_shows_friendly_page_and_keeps_user_logged_in(self):
        user = User.objects.create_user('stale', 'stale@example.com', 'x')
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(user)
        resp = client.post(reverse('logout'), {'csrfmiddlewaretoken': 'stale-token'})
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, 'PAGE', status_code=403)
        self.assertContains(resp, 'Reload', status_code=403)
        self.assertNotContains(resp, 'CSRF verification failed', status_code=403)
        self.assertEqual(client.get(reverse('dashboard')).status_code, 200)

    def test_valid_token_logout_still_works(self):
        user = User.objects.create_user('fresh', 'fresh@example.com', 'x')
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(user)
        page = client.get(reverse('dashboard')).content.decode()
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page).group(1)
        self.assertEqual(client.post(reverse('logout'), {'csrfmiddlewaretoken': token}).status_code, 302)
