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
