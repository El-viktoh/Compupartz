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


class AbandonedSignupTests(TestCase):
    PW = 'Str0ng-Pass-9981!'

    def _signup(self, username, email):
        return self.client_class().post(reverse('signup'), {
            'username': username, 'first_name': 'A', 'last_name': 'B', 'email': email,
            'password1': self.PW, 'password2': self.PW}, follow=True)

    def _form_errors(self, resp):
        return dict(resp.context['form'].errors) if resp.context and 'form' in resp.context else None

    def test_mistyped_email_can_be_retried_with_same_username(self):
        self._signup('retry', 'wrong@no-such-domain-xyz.com')
        mail.outbox.clear()
        resp = self._signup('retry', 'right@example.com')
        self.assertIsNone(self._form_errors(resp))
        self.assertEqual(list(User.objects.filter(username='retry').values_list('email', flat=True)), ['right@example.com'])
        self.assertEqual(mail.outbox[0].to, ['right@example.com'])

    def test_real_owner_is_not_locked_out_by_an_unverified_squatter(self):
        self._signup('squatter', 'victim@example.com')
        resp = self._signup('owner', 'victim@example.com')
        self.assertIsNone(self._form_errors(resp))
        self.assertFalse(User.objects.filter(username='squatter').exists())
        self.assertTrue(User.objects.filter(username='owner', is_active=False).exists())

    def test_verified_staff_used_and_ticket_owning_accounts_are_never_replaced(self):
        from django.utils import timezone
        from repair.models import RepairTicket
        User.objects.create_user('active', 'active@example.com', self.PW)
        User.objects.create_user('staffer', 'staffer@example.com', self.PW, is_active=False, is_staff=True)
        used = User.objects.create_user('used', 'used@example.com', self.PW, is_active=False)
        used.last_login = timezone.now()
        used.save()
        owner = User.objects.create_user('owner2', 'owner2@example.com', self.PW, is_active=False)
        RepairTicket.objects.create(user=owner, customer_name='T', customer_phone='0200000000', device='d')
        for email in ('active@example.com', 'staffer@example.com', 'used@example.com', 'owner2@example.com'):
            resp = self._signup('newname', email)
            self.assertIn('email', self._form_errors(resp), email)
        for username in ('active', 'ACTIVE', 'staffer', 'used', 'owner2'):
            resp = self._signup(username, f'{username}-new@example.com')
            self.assertIn('username', self._form_errors(resp), username)
        self.assertEqual(User.objects.filter(username__in=['active', 'staffer', 'used', 'owner2']).count(), 4)

    def test_failed_activation_email_keeps_the_existing_unverified_account(self):
        from unittest import mock
        self._signup('keeper', 'keep@example.com')
        with mock.patch('core.utils.EmailMessage.send', side_effect=Exception('smtp down')):
            resp = self._signup('keeper', 'keep2@example.com')
        self.assertContains(resp, 'send the activation email')
        self.assertTrue(User.objects.filter(username='keeper', email='keep@example.com').exists())

    def test_malformed_email_gets_a_clear_error(self):
        for bad in ('notanemail', 'john@', 'john@gmail'):
            resp = self._signup('fmt', bad)
            self.assertIn('Enter a valid email address.', self._form_errors(resp)['email'])


class DashboardCounterTests(TestCase):
    def setUp(self):
        from repair.models import RepairTicket
        self.RepairTicket = RepairTicket
        self.user = User.objects.create_user('counter', 'counter@example.com', 'x')
        self.client.force_login(self.user)

    def _ticket(self, status, **kw):
        return self.RepairTicket.objects.create(
            user=self.user, customer_name='C', customer_email='counter@example.com',
            customer_phone='0200000041', device='MBP', status=status, **kw)

    def _counts(self):
        ctx = self.client.get(reverse('dashboard')).context
        return ctx['active_repairs'].count(), ctx['past_repairs'].count()

    def test_each_status_lands_in_the_right_counter(self):
        t = self._ticket('pending')
        expected = {'pending': (1, 0), 'quoted': (1, 0), 'in_progress': (1, 0), 'completed': (0, 1), 'no_fix': (0, 0)}
        for status, counts in expected.items():
            t.status = status
            t.save()
            self.assertEqual(self._counts(), counts, status)

    def test_a_quote_awaiting_approval_is_listed_with_its_authorize_button(self):
        self._ticket('quoted', quote_status='sent', quoted_price=450)
        resp = self.client.get(reverse('dashboard'))
        self.assertContains(resp, 'Review quote')
        self.assertContains(resp, reverse('track_repair', args=[self.RepairTicket.objects.get(user=self.user).ticket_id]))

    def test_completing_a_ticket_moves_it_from_active_to_completed(self):
        t = self._ticket('in_progress')
        self.assertEqual(self._counts(), (1, 0))
        t.status = 'completed'
        t.save()
        self.assertEqual(self._counts(), (0, 1))

    def test_a_logged_out_booking_with_the_same_email_is_claimed_on_dashboard_load(self):
        self.RepairTicket.objects.create(
            user=None, customer_name='Guest', customer_email='COUNTER@example.com',
            customer_phone='0200000042', device='x', status='in_progress')
        self.assertEqual(self._counts(), (1, 0))

    def test_active_and_completed_sums_both_repairs_and_part_requests(self):
        from repair.models import PartRequest
        # Create 1 active repair ticket and 1 active part request
        self._ticket('in_progress')
        PartRequest.objects.create(
            user=self.user, customer_name='Counter', customer_email='counter@example.com',
            customer_phone='0200000041', part_needed='Battery', device_model='MacBook',
            status='pending')

        # Create 1 completed repair and 1 fulfilled part request
        self._ticket('completed')
        PartRequest.objects.create(
            user=self.user, customer_name='Counter', customer_email='counter@example.com',
            customer_phone='0200000041', part_needed='Screen', device_model='Dell',
            status='fulfilled')

        resp = self.client.get(reverse('dashboard'))
        ctx = resp.context
        self.assertEqual(ctx['total_active_services'], 2)
        self.assertEqual(ctx['total_completed_restorations'], 2)

        content = resp.content.decode('utf-8')
        self.assertIn('2', content)
        self.assertIn('1 Repairs &bull; 1 Parts', content)
        self.assertIn('1 Repaired &bull; 1 Sourced', content)


class StaffQueueFilterTests(TestCase):
    def setUp(self):
        from repair.models import RepairTicket, PartRequest
        self.staff_user = User.objects.create_user('staff_tech', 'tech@example.com', 'x', is_staff=True)
        self.client.force_login(self.staff_user)

        self.ticket = RepairTicket.objects.create(
            customer_name='Hillary Ofori',
            customer_email='hillary@example.com',
            customer_phone='0540123456',
            device='HP Pavillion',
            issue_description='Fixing hinge',
            status='in_progress',
            quoted_price=250.00
        )
        self.part_req = PartRequest.objects.create(
            customer_name='Kofi Mensah',
            customer_email='kofi@example.com',
            customer_phone='0244123456',
            part_needed='Mother board',
            device_model='Lenovo Thinkpad',
            additional_details='Model X1 Carbon',
            status='quoted',
            quoted_price=450.00
        )

    def test_staff_dashboard_renders_queues_and_filter_attributes(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

        # Check filter elements
        self.assertContains(resp, 'id="repair-filter-search"')
        self.assertContains(resp, 'id="repair-filter-sort"')
        self.assertContains(resp, 'id="repair-filter-status"')
        self.assertContains(resp, 'id="part-filter-search"')
        self.assertContains(resp, 'id="part-filter-sort"')
        self.assertContains(resp, 'id="part-filter-status"')

        # Check data attributes for client filtering
        self.assertContains(resp, 'data-ticket-id=')
        self.assertContains(resp, 'data-customer="hillary ofori"')
        self.assertContains(resp, 'data-phone="0540123456"')
        self.assertContains(resp, 'data-email="hillary@example.com"')
        self.assertContains(resp, 'data-request-id=')
        self.assertContains(resp, 'data-customer="kofi mensah"')
        self.assertContains(resp, 'data-part="mother board"')

    def test_staff_and_client_tab_ordering(self):
        # Staff user gets Lab Process Queue first
        resp = self.client.get(reverse('dashboard'))
        content = resp.content.decode('utf-8')
        staff_pos = content.find('id="tab-btn-staff-workshop"')
        parts_pos = content.find('id="tab-btn-hardware-parts-queue"')
        raised_pos = content.find('id="tab-btn-raised-tickets"')
        comms_pos = content.find('id="tab-btn-lab-communications"')

        self.assertTrue(staff_pos != -1 and parts_pos != -1 and raised_pos != -1 and comms_pos != -1)
        self.assertTrue(staff_pos < parts_pos < raised_pos < comms_pos)

        # Non-staff client does not get staff queue tabs, gets raised-tickets first
        client_user = User.objects.create_user('normal_client', 'client@example.com', 'x', is_staff=False)
        self.client.force_login(client_user)
        resp_client = self.client.get(reverse('dashboard'))
        content_client = resp_client.content.decode('utf-8')

        self.assertNotIn('id="tab-btn-staff-workshop"', content_client)
        self.assertNotIn('id="tab-btn-hardware-parts-queue"', content_client)
        self.assertIn('id="tab-btn-raised-tickets"', content_client)



class ClientRequestListBuilderTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        from repair.models import RepairTicket, PartRequest
        self.user = User.objects.create_user('lister', 'lister@example.com', 'x')
        self.now = timezone.now()

        def ticket(status, days_ago, **kw):
            t = RepairTicket.objects.create(user=self.user, customer_name='L', customer_email='lister@example.com',
                                            customer_phone='0244', device=f'Laptop {status} {days_ago}', status=status, **kw)
            RepairTicket.objects.filter(pk=t.pk).update(created_at=self.now - timedelta(days=days_ago))
            return t

        def part(status, days_ago, **kw):
            p = PartRequest.objects.create(user=self.user, customer_name='L', customer_email='lister@example.com',
                                           customer_phone='0244', part_needed=f'Part {status} {days_ago}', device_model='X1', status=status, **kw)
            PartRequest.objects.filter(pk=p.pk).update(created_at=self.now - timedelta(days=days_ago))
            return p

        self.done_old = ticket('completed', 20)
        self.active_new = ticket('in_progress', 1)
        self.needs_action = ticket('quoted', 10, quote_status='sent', quoted_price=100)
        self.declined = ticket('quoted', 5, quote_status='declined', quoted_price=100)
        self.part_action = part('quoted', 3, quote_status='sent', quoted_price=50)
        self.part_done = part('fulfilled', 8)
        self.part_active = part('in_progress', 2)

    def _build(self):
        from repair.models import RepairTicket, PartRequest
        from core.dashboard_requests import build_client_requests
        return build_client_requests(
            RepairTicket.objects.filter(user=self.user).prefetch_related('messages'),
            PartRequest.objects.filter(user=self.user).prefetch_related('messages'))

    def test_needs_action_first_then_active_then_done_newest_first_within_each(self):
        rows, _ = self._build()
        groups = [r['group'] for r in rows]
        self.assertEqual(groups, sorted(groups, key=lambda g: {'action': 0, 'active': 1, 'done': 2}[g]))
        self.assertEqual([r['ref'] for r in rows if r['group'] == 'action'], [self.part_action.request_id, self.needs_action.ticket_id])
        self.assertEqual([r['ref'] for r in rows if r['group'] == 'done'], [self.part_done.request_id, self.done_old.ticket_id])

    def test_a_sent_quote_needs_action_and_a_declined_quote_does_not(self):
        rows = {r['ref']: r for r in self._build()[0]}
        self.assertEqual(rows[self.needs_action.ticket_id]['group'], 'action')
        self.assertIn('needs your approval', rows[self.needs_action.ticket_id]['status_label'])
        self.assertEqual(rows[self.declined.ticket_id]['group'], 'active')
        self.assertEqual(rows[self.declined.ticket_id]['status_label'], 'Quote declined')

    def test_counts_match_the_rows(self):
        rows, counts = self._build()
        self.assertEqual(counts, {'all': 7, 'action': 2, 'active': 3, 'done': 2, 'repair': 4, 'part': 3})
        self.assertEqual(counts['all'], len(rows))

    def test_stage_and_search_text(self):
        rows = {r['ref']: r for r in self._build()[0]}
        self.assertEqual((rows[self.active_new.ticket_id]['stage'], rows[self.done_old.ticket_id]['stage']), (2, 3))
        search = rows[self.part_active.request_id]['search']
        self.assertIn(self.part_active.request_id.lower(), search)
        self.assertIn('part in_progress 2'.lower(), search)
        self.assertEqual(search, search.lower())

    def test_message_counts_need_no_extra_queries_once_prefetched(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from repair.models import RepairMessage, RepairTicket, PartRequest
        for _ in range(3):
            RepairMessage.objects.create(ticket=self.active_new, message='hi', sender_is_admin=True)
        tickets = list(RepairTicket.objects.filter(user=self.user).prefetch_related('messages'))
        parts = list(PartRequest.objects.filter(user=self.user).prefetch_related('messages'))
        from core.dashboard_requests import build_client_requests
        with CaptureQueriesContext(connection) as ctx:
            rows, _ = build_client_requests(tickets, parts)
        self.assertEqual(len(ctx), 0)
        self.assertEqual({r['ref']: r['message_count'] for r in rows}[self.active_new.ticket_id], 3)


class ClientDashboardRequestListTests(TestCase):
    def setUp(self):
        from repair.models import RepairTicket, PartRequest
        self.user = User.objects.create_user('dashclient', 'dc@example.com', 'x')
        self.other = User.objects.create_user('dashother', 'do@example.com', 'x')
        self.client.force_login(self.user)
        self.tickets = [RepairTicket.objects.create(user=self.user, customer_name='Me', customer_email='dc@example.com', customer_phone='0244',
                                                    device=f'MyLaptop{i}', status=('quoted' if i == 0 else 'in_progress' if i < 6 else 'completed'),
                                                    quote_status=('sent' if i == 0 else 'none'), quoted_price=(120 if i == 0 else None)) for i in range(10)]
        self.parts = [PartRequest.objects.create(user=self.user, customer_name='Me', customer_email='dc@example.com', customer_phone='0244',
                                                 part_needed=f'MyPart{i}', device_model='M', status=('fulfilled' if i < 3 else 'pending')) for i in range(8)]
        RepairTicket.objects.create(user=self.other, customer_name='Other Person', customer_email='do@example.com', customer_phone='0201',
                                    device='OtherSecretLaptop', status='in_progress')

    def test_the_page_lists_every_request_in_one_compact_list_with_counts(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['client_counts'], {'all': 18, 'action': 1, 'active': 10, 'done': 7, 'repair': 10, 'part': 8})
        html = resp.content.decode()
        self.assertEqual(html.count('class="req-row'), 18)
        self.assertIn('My Requests', html)
        self.assertIn('1 quote waiting for your approval', html)
        self.assertIn('Search by ID, device or part', html)
        self.assertIn('data-page-size="6"', html)

    def test_the_old_one_card_per_ticket_layout_is_gone(self):
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertNotIn('Open Diagnostic Monitoring Report', html)
        self.assertNotIn('Live Lab Ticket', html)

    def test_quote_rows_link_to_the_right_page_and_chat_buttons_use_the_right_functions(self):
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn(reverse('track_repair', args=[self.tickets[0].ticket_id]), html)
        self.assertIn(reverse('track_part', args=[self.parts[0].request_id]), html)
        self.assertIn(f"openTicketChat('{self.tickets[0].id}')", html)
        self.assertIn(f"openPartChat('{self.parts[0].id}')", html)
        self.assertIn('Review quote', html)

    def test_other_customers_requests_never_appear(self):
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertNotIn('OtherSecretLaptop', html)
        self.assertNotIn('Other Person', html)

    def test_a_client_with_no_requests_sees_a_friendly_empty_state(self):
        self.client.force_login(self.other)
        from repair.models import RepairTicket
        RepairTicket.objects.filter(user=self.other).delete()
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn('No requests yet', html)
        self.assertIn(reverse('book_repair'), html)
        self.assertIn(reverse('request_part'), html)
        self.assertNotIn('id="client-requests"', html)

    def test_the_dashboard_markup_is_well_formed_for_clients_and_staff(self):
        from html.parser import HTMLParser
        void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr',
                'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'stop'}

        class P(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack, self.bad = [], []

            def handle_starttag(self, tag, attrs):
                if tag not in void:
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if tag in void:
                    return
                if self.stack and self.stack[-1] == tag:
                    self.stack.pop()
                else:
                    self.bad.append(tag)

        staff = User.objects.create_user('dashstaff', 'ds@example.com', 'x', is_staff=True)
        for account in (self.user, staff):
            self.client.force_login(account)
            p = P()
            p.feed(self.client.get(reverse('dashboard')).content.decode())
            self.assertEqual((p.bad, p.stack), ([], []), account.username)

    def test_staff_dashboard_still_shows_their_own_requests_in_the_same_panel(self):
        from repair.models import RepairTicket
        staff = User.objects.create_user('dashstaff2', 'ds2@example.com', 'x', is_staff=True)
        RepairTicket.objects.create(user=staff, customer_name='Staff Own', customer_email='ds2@example.com', customer_phone='0244', device='StaffOwnLaptop', status='pending')
        self.client.force_login(staff)
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['client_counts']['all'], 1)
        self.assertEqual([r['title'] for r in resp.context['client_requests']], ['StaffOwnLaptop'])
        html = resp.content.decode()
        my_requests_list = html[html.index('id="req-list"'):html.index('</ul>', html.index('id="req-list"'))]
        self.assertIn('StaffOwnLaptop', my_requests_list)
        self.assertNotIn('MyLaptop0', my_requests_list)  # other clients' tickets live only in the separate staff workshop tab


class ClientRequestRowPhotoTests(TestCase):
    def test_a_repair_with_a_diagnostic_photo_shows_a_thumbnail_link_in_its_row(self):
        import io, tempfile, shutil
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from repair.models import RepairTicket
        media = tempfile.mkdtemp(prefix='test_media_')
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        buf = io.BytesIO()
        Image.new('RGB', (4, 4), 'red').save(buf, 'PNG')
        user = User.objects.create_user('photoclient', 'pc@example.com', 'x')
        with override_settings(MEDIA_ROOT=media):
            t = RepairTicket.objects.create(user=user, customer_name='P', customer_email='pc@example.com', customer_phone='0244',
                                            device='PhotoLaptop', status='pending',
                                            diagnostic_image=SimpleUploadedFile('f.png', buf.getvalue(), 'image/png'))
            RepairTicket.objects.create(user=user, customer_name='P', customer_email='pc@example.com', customer_phone='0245',
                                        device='NoPhotoLaptop', status='pending')
            self.client.force_login(user)
            html = self.client.get(reverse('dashboard')).content.decode()
        self.assertEqual(html.count('Uploaded Diagnostic Photo'), 2)  # link title + image alt, for the one ticket with a photo
        self.assertIn(t.diagnostic_image.url, html)


class CommsTabPageTests(TestCase):
    def setUp(self):
        from repair.models import RepairTicket, PartRequest, RepairMessage
        self.user = User.objects.create_user('commsclient', 'cc@example.com', 'x')
        self.other = User.objects.create_user('commsother', 'co@example.com', 'x')
        self.t1 = RepairTicket.objects.create(user=self.user, customer_name='C', customer_email='cc@example.com', customer_phone='0244', device='ClientLaptopOne', status='in_progress')
        self.t2 = RepairTicket.objects.create(user=self.user, customer_name='C', customer_email='cc@example.com', customer_phone='0245', device='ClientLaptopTwo', status='pending')
        self.p1 = PartRequest.objects.create(user=self.user, customer_name='C', customer_email='cc@example.com', customer_phone='0246', part_needed='ClientPart', device_model='M', status='pending')
        RepairMessage.objects.create(ticket=self.t1, message='Lab says hello', sender_is_admin=True)
        other_ticket = RepairTicket.objects.create(user=self.other, customer_name='Other', customer_email='co@example.com', customer_phone='0201', device='OtherSecretLaptop', status='in_progress')
        RepairMessage.objects.create(ticket=other_ticket, message='OTHER-PRIVATE-MSG', sender_is_admin=True)
        self.client.force_login(self.user)

    def test_clients_and_staff_both_get_the_same_service_thread_strip(self):
        staff = User.objects.create_user('commsstaff', 'cs@example.com', 'x', is_staff=True)
        for account in (self.user, staff):
            self.client.force_login(account)
            html = self.client.get(reverse('dashboard')).content.decode()
            self.assertIn('Service Threads:', html, account.username)
            self.assertEqual(html.count('comms-ticket-tab px-4'), 3 if account.is_staff else 2, account.username)  # one pill per ticket
            for needle in (f'id="comms-tab-btn-{self.t1.id}"', f'id="comms-tab-btn-{self.t2.id}"',
                           f'id="comms-ticket-container-{self.t1.id}"', f'id="comms-ticket-container-{self.t2.id}"'):
                self.assertIn(needle, html, account.username)
            # the conversation picker is gone for everyone
            for marker in ('id="comms-picker"', 'class="comms-item-tab comms-thread-row', 'id="comms-search"', 'Needs reply', 'Lab replied'):
                self.assertNotIn(marker, html, account.username)

    def test_a_client_sees_their_part_request_pill_and_chat(self):
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn(f'id="comms-part-tab-btn-{self.p1.id}"', html)
        self.assertIn(f'id="comms-part-container-{self.p1.id}"', html)
        self.assertIn('Lab says hello', html)

    def test_deep_link_handling_is_present(self):
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn("urlParams.get('ticket')", html)
        self.assertIn('selectCommsTicket(ticketParam)', html)

    def test_other_customers_conversations_never_appear_for_clients(self):
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertNotIn('OtherSecretLaptop', html)
        self.assertNotIn('OTHER-PRIVATE-MSG', html)

    def test_page_markup_stays_well_formed_for_clients_and_staff(self):
        from html.parser import HTMLParser
        void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr',
                'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'stop'}

        class P(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack, self.bad = [], []

            def handle_starttag(self, tag, attrs):
                if tag not in void:
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if tag in void:
                    return
                if self.stack and self.stack[-1] == tag:
                    self.stack.pop()
                else:
                    self.bad.append(tag)

        staff = User.objects.create_user('commsstaff2', 'cs2@example.com', 'x', is_staff=True)
        for account in (self.user, staff):
            self.client.force_login(account)
            p = P()
            p.feed(self.client.get(reverse('dashboard')).content.decode())
            self.assertEqual((p.bad, p.stack), ([], []), account.username)


class ClearFinishedRequestsTests(TestCase):
    """Clients can tidy finished requests off their dashboard; nothing is ever deleted."""

    def setUp(self):
        from repair.models import RepairTicket, PartRequest, RepairMessage
        self.user = User.objects.create_user('clearme', 'clearme@example.com', 'x')
        self.other = User.objects.create_user('clearother', 'clearother@example.com', 'x')
        self.staff = User.objects.create_user('clearstaff', 'clearstaff@example.com', 'x', is_staff=True)
        mk = dict(customer_name='C', customer_email='clearme@example.com', customer_phone='0244')
        self.done_t = RepairTicket.objects.create(user=self.user, device='DoneLaptop', status='completed', **mk)
        self.nofix_t = RepairTicket.objects.create(user=self.user, device='NoFixLaptop', status='no_fix', **mk)
        self.live_t = RepairTicket.objects.create(user=self.user, device='LiveLaptop', status='in_progress', **mk)
        self.done_p = PartRequest.objects.create(user=self.user, part_needed='DonePart', device_model='M', status='fulfilled', **mk)
        self.live_p = PartRequest.objects.create(user=self.user, part_needed='LivePart', device_model='M', status='pending', **mk)
        self.foreign_t = RepairTicket.objects.create(user=self.other, device='ForeignLaptop', status='completed',
                                                     customer_name='O', customer_email='clearother@example.com', customer_phone='0201')
        RepairMessage.objects.create(ticket=self.done_t, sender_is_admin=True, message='all fixed')
        self.client.force_login(self.user)

    def _refresh(self, *objs):
        for o in objs:
            o.refresh_from_db()

    def test_clearing_one_finished_repair_hides_it_but_keeps_the_record(self):
        resp = self.client.post(reverse('clear_repair_request', args=[self.done_t.ticket_id]))
        self.assertRedirects(resp, reverse('dashboard') + '?tab=raised-tickets', fetch_redirect_response=False)
        self._refresh(self.done_t)
        self.assertTrue(self.done_t.cleared_by_client)
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertNotIn('DoneLaptop', html)
        self.assertIn('NoFixLaptop', html)
        self.assertEqual(self.done_t.messages.count(), 1)  # chat history kept
        # still reachable by its tracking id
        self.assertEqual(self.client.get(reverse('track_repair', args=[self.done_t.ticket_id])).status_code, 200)

    def test_clearing_one_finished_part_request(self):
        self.client.post(reverse('clear_part_request', args=[self.done_p.request_id]))
        self._refresh(self.done_p)
        self.assertTrue(self.done_p.cleared_by_client)
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertNotIn('DonePart', html)
        self.assertIn('LivePart', html)

    def test_clear_all_finished_only_touches_finished_requests_of_this_user(self):
        resp = self.client.post(reverse('clear_finished_requests'), follow=True)
        self.assertContains(resp, '3 finished requests cleared')
        self._refresh(self.done_t, self.nofix_t, self.live_t, self.done_p, self.live_p, self.foreign_t)
        self.assertTrue(self.done_t.cleared_by_client and self.nofix_t.cleared_by_client and self.done_p.cleared_by_client)
        self.assertFalse(self.live_t.cleared_by_client)
        self.assertFalse(self.live_p.cleared_by_client)
        self.assertFalse(self.foreign_t.cleared_by_client)

    def test_unfinished_requests_cannot_be_cleared(self):
        resp = self.client.post(reverse('clear_repair_request', args=[self.live_t.ticket_id]), follow=True)
        self.assertContains(resp, 'Only finished requests can be cleared')
        resp = self.client.post(reverse('clear_part_request', args=[self.live_p.request_id]), follow=True)
        self.assertContains(resp, 'Only finished requests can be cleared')
        self._refresh(self.live_t, self.live_p)
        self.assertFalse(self.live_t.cleared_by_client or self.live_p.cleared_by_client)

    def test_a_client_cannot_clear_someone_elses_request(self):
        resp = self.client.post(reverse('clear_repair_request', args=[self.foreign_t.ticket_id]))
        self.assertEqual(resp.status_code, 404)
        self._refresh(self.foreign_t)
        self.assertFalse(self.foreign_t.cleared_by_client)

    def test_staff_clearing_does_not_touch_a_clients_dashboard(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('clear_repair_request', args=[self.done_t.ticket_id])).status_code, 404)
        self._refresh(self.done_t)
        self.assertFalse(self.done_t.cleared_by_client)

    def test_clearing_needs_post_and_login(self):
        url = reverse('clear_repair_request', args=[self.done_t.ticket_id])
        self.client.get(url)
        self.client.get(reverse('clear_finished_requests'))
        self._refresh(self.done_t)
        self.assertFalse(self.done_t.cleared_by_client)
        self.client.logout()
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp['Location'])
        self._refresh(self.done_t)
        self.assertFalse(self.done_t.cleared_by_client)

    def test_clear_requires_csrf_token(self):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        self.assertEqual(strict.post(reverse('clear_finished_requests')).status_code, 403)
        self._refresh(self.done_t)
        self.assertFalse(self.done_t.cleared_by_client)

    def test_a_cleared_request_comes_back_if_the_lab_reopens_it(self):
        self.client.post(reverse('clear_repair_request', args=[self.done_t.ticket_id]))
        self.assertNotIn('DoneLaptop', self.client.get(reverse('dashboard')).content.decode())
        self.done_t.status = 'in_progress'
        self.done_t.save()
        self.assertIn('DoneLaptop', self.client.get(reverse('dashboard')).content.decode())

    def test_cleared_requests_leave_the_conversation_list_and_counts_but_not_the_lab_queue(self):
        self.client.post(reverse('clear_finished_requests'))
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['client_counts']['done'], 0)
        self.assertEqual(resp.context['client_counts']['all'], 2)
        self.assertNotIn(f'id="comms-tab-btn-{self.done_t.id}"', resp.content.decode())
        self.assertIn(f'id="comms-tab-btn-{self.live_t.id}"', resp.content.decode())
        self.assertNotIn(f'comms-ticket-container-{self.done_t.id}"', resp.content.decode())
        self.assertIn(f'comms-ticket-container-{self.live_t.id}"', resp.content.decode())
        self.assertEqual(resp.context['total_user_messages'], 0)
        # the lab still sees every ticket
        self.client.force_login(self.staff)
        staff_html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn('DoneLaptop', staff_html)
        # the lifetime "repaired" tile still counts the work that was done
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('dashboard')).context['past_repairs'].count(), 1)

    def test_buttons_show_only_for_finished_requests(self):
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn(reverse('clear_finished_requests'), html)
        self.assertIn('Clear completed (3)', html)
        self.assertIn(reverse('clear_repair_request', args=[self.done_t.ticket_id]), html)
        self.assertIn(reverse('clear_part_request', args=[self.done_p.request_id]), html)
        self.assertNotIn(reverse('clear_repair_request', args=[self.live_t.ticket_id]), html)
        self.assertNotIn(reverse('clear_part_request', args=[self.live_p.request_id]), html)
        self.client.post(reverse('clear_finished_requests'))
        self.assertNotIn('Clear completed', self.client.get(reverse('dashboard')).content.decode())

    def test_my_repairs_page_also_hides_cleared_tickets(self):
        self.client.post(reverse('clear_repair_request', args=[self.done_t.ticket_id]))
        html = self.client.get(reverse('my_repairs')).content.decode()
        self.assertNotIn('DoneLaptop', html)
        self.assertIn('LiveLaptop', html)


class ClearedRequestChatTests(TestCase):
    """Clearing a finished request also takes its Lab Communications chat away from the client."""

    def setUp(self):
        from repair.models import RepairTicket, PartRequest, RepairMessage, PartRequestMessage
        self.user = User.objects.create_user('chatclear', 'chatclear@example.com', 'x')
        self.staff = User.objects.create_user('chatstaff', 'chatstaff@example.com', 'x', is_staff=True)
        mk = dict(user=self.user, customer_name='C', customer_email='chatclear@example.com', customer_phone='0244')
        self.t = RepairTicket.objects.create(device='ChatLaptop', status='completed', **mk)
        self.p = PartRequest.objects.create(part_needed='ChatPart', device_model='M', status='fulfilled', **mk)
        self.tm = RepairMessage.objects.create(ticket=self.t, sender_is_admin=False, message='client-secret-note')
        self.pm = PartRequestMessage.objects.create(part_request=self.p, sender_is_admin=False, message='client-part-note')
        self.client.force_login(self.user)
        self.client.post(reverse('clear_finished_requests'))

    def test_client_no_longer_sees_the_chat_on_the_tracking_pages(self):
        for url, text in ((reverse('track_repair', args=[self.t.ticket_id]), 'client-secret-note'),
                          (reverse('track_part', args=[self.p.request_id]), 'client-part-note')):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.context['chat_hidden'])
            html = resp.content.decode()
            self.assertNotIn(text, html)
            self.assertNotIn('enctype="multipart/form-data"', html)
            self.assertIn('conversation for this request is closed', html)

    def test_client_cannot_post_edit_or_delete_in_a_closed_chat(self):
        resp = self.client.post(reverse('track_repair', args=[self.t.ticket_id]), {'message': 'sneaky'}, follow=True)
        self.assertContains(resp, 'its conversation is closed')
        self.assertEqual(self.t.messages.count(), 1)
        resp = self.client.post(reverse('track_part', args=[self.p.request_id]), {'message': 'sneaky'}, follow=True)
        self.assertEqual(self.p.messages.count(), 1)
        self.assertEqual(self.client.post(reverse('edit_repair_message', args=[self.tm.id]), {'message': 'x'}).status_code, 403)
        self.assertEqual(self.client.post(reverse('delete_repair_message', args=[self.tm.id])).status_code, 403)
        self.assertEqual(self.client.post(reverse('edit_part_request_message', args=[self.pm.id]), {'message': 'x'}).status_code, 403)
        self.assertEqual(self.client.post(reverse('delete_part_request_message', args=[self.pm.id])).status_code, 403)
        self.tm.refresh_from_db()
        self.assertEqual(self.tm.message, 'client-secret-note')

    def test_the_lab_still_sees_and_can_use_the_chat(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('track_repair', args=[self.t.ticket_id]))
        self.assertFalse(resp.context['chat_hidden'])
        self.assertContains(resp, 'client-secret-note')
        self.client.post(reverse('track_repair', args=[self.t.ticket_id]), {'message': 'lab note'})
        self.assertEqual(self.t.messages.count(), 2)

    def test_the_chat_returns_if_the_request_is_reopened(self):
        self.t.status = 'in_progress'
        self.t.save()
        resp = self.client.get(reverse('track_repair', args=[self.t.ticket_id]))
        self.assertFalse(resp.context['chat_hidden'])
        self.assertContains(resp, 'client-secret-note')

    def test_an_uncleared_finished_request_keeps_its_chat(self):
        from repair.models import RepairTicket
        other = RepairTicket.objects.create(user=self.user, device='KeptLaptop', status='completed',
                                            customer_name='C', customer_email='chatclear@example.com', customer_phone='0244')
        resp = self.client.get(reverse('track_repair', args=[other.ticket_id]))
        self.assertFalse(resp.context['chat_hidden'])
        self.assertContains(resp, 'enctype="multipart/form-data"')

