from django.test import TestCase, Client
from django.core import mail
from django.urls import reverse
from django.contrib.auth.models import User

from repair.models import RepairTicket, PartRequest, PartRequestMessage
from core.models import Testimonial, FAQ
from core.notifications import (
    send_admin_repair_notification,
    send_admin_part_request_notification,
    send_admin_testimonial_notification,
)


class AdminNotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123!'
        )

    def test_send_admin_repair_notification(self):
        ticket = RepairTicket.objects.create(
            customer_name="Kofi Mensah",
            customer_email="kofi@example.com",
            customer_phone="0540123456",
            device_category="laptop",
            manufacturer="Dell",
            device="XPS 15 9500",
            issue_description="No display and blinking orange power LED.",
            contact_method="whatsapp",
            logistics_preference="drop_off",
        )
        mail.outbox = []

        result = send_admin_repair_notification(ticket)
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['support@compupartz.com'])
        self.assertEqual(email.reply_to, ['kofi@example.com'])
        self.assertIn(ticket.ticket_id, email.subject)
        self.assertIn("Kofi Mensah", email.subject)
        self.assertIn("XPS 15 9500", email.subject)
        self.assertIn("No display and blinking orange power LED", email.body)
        self.assertIn(f"/admin/repair/repairticket/{ticket.id}/change/", email.body)
        self.assertIn("wa.me/233540123456", email.body)

    def test_send_admin_part_request_notification(self):
        part_request = PartRequest.objects.create(
            customer_name="Ama Serwaa",
            customer_email="ama@example.com",
            customer_phone="0240987654",
            part_needed="MacBook Air M2 Liquid Retina Display Assembly",
            device_model="MacBook Air M2 2022 (A2681)",
            condition_preference="new",
            additional_details="Midnight blue color finish required.",
        )
        mail.outbox = []

        result = send_admin_part_request_notification(part_request)
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['support@compupartz.com'])
        self.assertEqual(email.reply_to, ['ama@example.com'])
        self.assertIn(part_request.request_id, email.subject)
        self.assertIn("Ama Serwaa", email.subject)
        self.assertIn("MacBook Air M2 Liquid Retina Display Assembly", email.subject)
        self.assertIn("Midnight blue color finish required", email.body)
        self.assertIn(f"/admin/repair/partrequest/{part_request.id}/change/", email.body)
        self.assertIn("wa.me/233240987654", email.body)

    def test_send_admin_testimonial_notification(self):
        testimonial = Testimonial.objects.create(
            user=self.user,
            name="Yaw Boateng",
            role_or_title="Creative Director",
            quote="Compupartz micro-soldered my motherboard within 24 hours. Incredible service!",
            rating=5,
            service_rendered="Logic Board Level Repair",
            is_approved=True,
            is_featured=False,
        )
        mail.outbox = []

        result = send_admin_testimonial_notification(testimonial)
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['support@compupartz.com'])
        self.assertEqual(email.reply_to, ['testuser@example.com'])
        self.assertIn("5★", email.subject)
        self.assertIn("Yaw Boateng", email.subject)
        self.assertIn("Compupartz micro-soldered my motherboard", email.body)
        self.assertIn(f"/admin/core/testimonial/{testimonial.id}/change/", email.body)
        self.assertIn("★★★★★", email.body)

    def test_preview_endpoints_render_successfully(self):
        staff = User.objects.create_user('previewstaff', 'ps@example.com', 'x', is_staff=True)
        self.client.force_login(staff)
        repair_res = self.client.get(reverse('preview_admin_repair_email'))
        self.assertEqual(repair_res.status_code, 200)
        self.assertContains(repair_res, "Repair Ticket Intake")
        self.assertContains(repair_res, "support@compupartz.com")

        part_res = self.client.get(reverse('preview_admin_part_email'))
        self.assertEqual(part_res.status_code, 200)
        self.assertContains(part_res, "Part Sourcing Request")
        self.assertContains(part_res, "support@compupartz.com")

        testimonial_res = self.client.get(reverse('preview_admin_testimonial_email'))
        self.assertEqual(testimonial_res.status_code, 200)
        self.assertContains(testimonial_res, "Client Testimonial")
        self.assertContains(testimonial_res, "support@compupartz.com")

    def test_testimonial_form_submission_triggers_admin_email(self):
        mail.outbox = []
        response = self.client.post(reverse('submit_testimonial'), {
            'name': 'Kwesi Arthur',
            'quote': 'Brilliant tech diagnosis, laptop works like new!',
            'rating': '5',
            'service_rendered': 'Thermal Paste & Board Cleaning',
            'role_or_title': 'Sound Producer',
        })
        self.assertEqual(response.status_code, 302)
        # Should have sent notification email to support@compupartz.com
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['support@compupartz.com'])
        self.assertIn("Kwesi Arthur", mail.outbox[0].subject)

    def test_book_repair_form_submission_triggers_admin_email(self):
        mail.outbox = []
        response = self.client.post(reverse('book_repair'), {
            'customer_name': 'Ekow Hanson',
            'customer_email': 'ekow@example.com',
            'customer_phone': '0541112233',
            'device_category': 'laptop',
            'manufacturer': 'Lenovo',
            'device': 'ThinkPad X1 Carbon Gen 9',
            'issue_description': 'USB-C charging port broken, logic board needs micro-soldering.',
            'logistics_preference': 'drop_off',
        })
        self.assertEqual(response.status_code, 302)
        # Should have sent 2 emails: 1 to customer, 1 to support@compupartz.com
        self.assertEqual(len(mail.outbox), 2)
        recipients = [m.to[0] for m in mail.outbox]
        self.assertIn('ekow@example.com', recipients)
        self.assertIn('support@compupartz.com', recipients)

        admin_email = [m for m in mail.outbox if m.to == ['support@compupartz.com']][0]
        self.assertIn("Ekow Hanson", admin_email.subject)
        self.assertIn("ThinkPad X1 Carbon Gen 9", admin_email.subject)
        self.assertIn("USB-C charging port broken", admin_email.body)

    def test_request_part_form_submission_triggers_admin_email(self):
        mail.outbox = []
        response = self.client.post(reverse('request_part'), {
            'customer_name': 'Abena Osei',
            'customer_email': 'abena@example.com',
            'customer_phone': '0203334455',
            'part_needed': 'OEM Battery for Dell XPS 13 9310',
            'device_model': 'Dell XPS 13 9310',
            'condition_preference': 'new',
            'additional_details': '52Wh 4-cell genuine battery.',
        })
        self.assertEqual(response.status_code, 302)
        # Should have sent 2 emails: 1 to customer, 1 to support@compupartz.com
        self.assertEqual(len(mail.outbox), 2)
        recipients = [m.to[0] for m in mail.outbox]
        self.assertIn('abena@example.com', recipients)
        self.assertIn('support@compupartz.com', recipients)

        admin_email = [m for m in mail.outbox if m.to == ['support@compupartz.com']][0]
        self.assertIn("Abena Osei", admin_email.subject)
        self.assertIn("OEM Battery for Dell XPS 13 9310", admin_email.subject)
        self.assertIn("52Wh 4-cell genuine battery", admin_email.body)

    def test_book_repair_success_notification_and_messages(self):
        # 1. Standard POST redirects back to book_repair (no success page redirect)
        response = self.client.post(reverse('book_repair'), {
            'customer_name': 'Kojo Antwi',
            'customer_email': 'kojo@example.com',
            'customer_phone': '0240998877',
            'device_category': 'laptop',
            'manufacturer': 'Apple',
            'device': 'MacBook Pro M2 14-inch',
            'issue_description': 'Screen backlight dark on left half.',
            'logistics_preference': 'drop_off',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('/repair/book/', response.redirect_chain[0][0])
        messages_list = [str(m) for m in response.context['messages']]
        self.assertTrue(any('repair ticket' in m.lower() for m in messages_list))
        self.assertTrue(any('Thank you for choosing us' in m for m in messages_list))
        content = response.content.decode()
        self.assertIn('TICKET SUBMITTED', content)
        self.assertIn('repairSuccessAlert', content)

        # 2. AJAX submission
        ajax_res = self.client.post(reverse('book_repair'), {
            'customer_name': 'Kojo Antwi 2',
            'customer_email': 'kojo2@example.com',
            'customer_phone': '0240998877',
            'device_category': 'laptop',
            'manufacturer': 'Apple',
            'device': 'MacBook Pro M2 14-inch',
            'issue_description': 'Screen backlight dark on left half.',
            'logistics_preference': 'drop_off',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(ajax_res.status_code, 200)
        data = ajax_res.json()
        self.assertTrue(data['success'])
        self.assertIn('ticket_id', data)
        self.assertIn('Thank you for choosing us', data['message'])

    def test_request_part_success_notification_and_messages(self):
        # 1. Standard POST redirects back to request_part (no success page redirect)
        response = self.client.post(reverse('request_part'), {
            'customer_name': 'Akosua Serwaa',
            'customer_email': 'akosua@example.com',
            'customer_phone': '0550112233',
            'part_needed': 'Trackpad Cable for MacBook Air M1',
            'device_model': 'MacBook Air A2337',
            'condition_preference': 'new',
            'additional_details': 'Original OEM flex ribbon.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('/repair/request-part/', response.redirect_chain[0][0])
        messages_list = [str(m) for m in response.context['messages']]
        self.assertTrue(any('part request' in m.lower() for m in messages_list))
        self.assertTrue(any('Thank you for choosing us' in m for m in messages_list))
        content = response.content.decode()
        self.assertIn('REQUEST SUBMITTED', content)
        self.assertIn('partSuccessAlert', content)

        # 2. AJAX submission
        ajax_res = self.client.post(reverse('request_part'), {
            'customer_name': 'Akosua Serwaa 2',
            'customer_email': 'akosua2@example.com',
            'customer_phone': '0550112233',
            'part_needed': 'Trackpad Cable for MacBook Air M1',
            'device_model': 'MacBook Air A2337',
            'condition_preference': 'new',
            'additional_details': 'Original OEM flex ribbon.',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(ajax_res.status_code, 200)
        data = ajax_res.json()
        self.assertTrue(data['success'])
        self.assertIn('request_id', data)
        self.assertIn('Thank you for choosing us', data['message'])


class NoFixStatusTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffadmin',
            email='staff@compupartz.com',
            password='StaffPassword123!',
            is_staff=True
        )
        self.ticket = RepairTicket.objects.create(
            customer_name="Kwabena Asante",
            customer_email="kwabena@example.com",
            customer_phone="0540112233",
            device_category="laptop",
            manufacturer="Apple",
            device="MacBook Pro 16 A2141",
            issue_description="Severe liquid ingress corrosion on CPU power rails.",
            status="pending"
        )

    def test_status_choice_no_fix_display(self):
        self.ticket.status = "no_fix"
        self.ticket.save()
        self.assertEqual(self.ticket.status, "no_fix")
        self.assertEqual(self.ticket.get_status_display(), "No-Fix")

    def test_legacy_cancelled_normalizes_to_no_fix(self):
        self.ticket.status = "cancelled"
        self.ticket.save()
        self.assertEqual(self.ticket.status, "no_fix")
        self.assertEqual(self.ticket.get_status_display(), "No-Fix")

    def test_staff_update_repair_status_to_no_fix(self):
        self.client.login(username='staffadmin', password='StaffPassword123!')
        mail.outbox = []

        response = self.client.post(
            reverse('staff_update_repair_status', kwargs={'ticket_id': self.ticket.ticket_id}),
            {
                'status': 'no_fix',
                'status_note': 'Corrosion penetrated inner layers of PCB; non-recoverable on bench.'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'no_fix')
        self.assertEqual(self.ticket.get_status_display(), 'No-Fix')

        # Verify No-Fix customer notification email dispatched
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['kwabena@example.com'])
        self.assertIn("No-Fix Notice", email.subject)
        self.assertIn("No Fix = No Fee", email.body)

    def test_admin_mark_no_fix_action(self):
        from django.contrib.admin.sites import AdminSite
        from repair.admin import RepairTicketAdmin

        site = AdminSite()
        admin_obj = RepairTicketAdmin(RepairTicket, site)

        queryset = RepairTicket.objects.filter(id=self.ticket.id)
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/admin/repair/repairticket/')
        request.user = self.staff_user
        from django.contrib.messages.storage.base import BaseStorage
        class DummyStorage(BaseStorage):
            def _get(self, *args, **kwargs):
                return [], True
            def _store(self, *args, **kwargs):
                return []
        setattr(request, '_messages', DummyStorage(request))

        admin_obj.mark_no_fix(request, queryset)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'no_fix')




from django.contrib.auth.models import User
from django.urls import reverse
from .models import RepairTicket, PartRequest


class EmailPreviewAccessTests(TestCase):
    NAMES = [
        'preview_repair_intake_email', 'preview_part_intake_email',
        'preview_repair_quote_email', 'preview_part_quote_email',
        'preview_admin_repair_email', 'preview_admin_part_email',
        'preview_admin_testimonial_email',
    ]

    def test_previews_require_staff(self):
        regular = User.objects.create_user('reg', 'reg@example.com', 'x')
        staff = User.objects.create_user('stf', 'stf@example.com', 'x', is_staff=True)
        for name in self.NAMES:
            url = reverse(name)
            self.assertEqual(self.client.get(url).status_code, 302, name)
            self.client.force_login(regular)
            self.assertEqual(self.client.get(url).status_code, 302, name)
            self.client.force_login(staff)
            self.assertEqual(self.client.get(url).status_code, 200, name)
            self.client.logout()

    def test_previews_never_expose_real_customer_data_to_anonymous(self):
        RepairTicket.objects.create(
            customer_name='RealCustomerName', customer_email='real@example.com',
            customer_phone='0245550123', device='Dev')
        for name in self.NAMES:
            resp = self.client.get(reverse(name), follow=False)
            self.assertNotContains(resp, 'RealCustomerName', status_code=302)


class QuoteApprovalGuardTests(TestCase):
    def setUp(self):
        self.ticket = RepairTicket.objects.create(
            customer_name='Q', customer_phone='0200000001', device='D')
        self.client.post(reverse('track_repair_lookup'),
                         {'ticket_id': self.ticket.ticket_id, 'phone': '0200000001'})

    def test_cannot_approve_when_no_quote_was_sent(self):
        self.client.post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        self.ticket.refresh_from_db()
        self.assertEqual((self.ticket.status, self.ticket.quote_status), ('pending', 'none'))

    def test_cannot_reopen_completed_ticket_via_approve(self):
        self.ticket.status = 'completed'
        self.ticket.save()
        self.client.post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'completed')

    def test_can_approve_and_decline_when_quote_is_sent(self):
        self.ticket.status, self.ticket.quote_status, self.ticket.quoted_price = 'quoted', 'sent', 100
        self.ticket.save()
        self.client.post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        self.ticket.refresh_from_db()
        self.assertEqual((self.ticket.status, self.ticket.quote_status), ('in_progress', 'approved'))

    def test_cannot_approve_part_quote_that_was_not_sent(self):
        pr = PartRequest.objects.create(customer_name='P', customer_phone='0200000002',
                                        part_needed='x', device_model='y')
        self.client.post(reverse('track_part_lookup'), {'request_id': pr.request_id, 'phone': '0200000002'})
        self.client.post(reverse('customer_approve_part_quote', args=[pr.request_id]))
        pr.refresh_from_db()
        self.assertNotEqual(pr.quote_status, 'approved')


class PartRequestMessagingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='partclient',
            email='client@example.com',
            password='Password123!'
        )
        self.staff_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@compupartz.com',
            password='AdminPassword123!'
        )
        self.part_req = PartRequest.objects.create(
            user=self.user,
            customer_name='Client Name',
            customer_email='client@example.com',
            customer_phone='0240000000',
            part_needed='Dell XPS 15 Battery',
            device_model='Dell XPS 15 9500',
            status='pending',
            quote_status='none'
        )

    def test_customer_can_post_message_on_part_request(self):
        self.client.login(username='partclient', password='Password123!')
        response = self.client.post(
            reverse('track_part', args=[self.part_req.request_id]),
            {'message': 'Do you have genuine OEM 86Wh battery in stock?'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.part_req.messages.count(), 1)
        msg = self.part_req.messages.first()
        self.assertFalse(msg.sender_is_admin)
        self.assertEqual(msg.message, 'Do you have genuine OEM 86Wh battery in stock?')

    def test_technician_message_triggers_email_notification(self):
        mail.outbox = []
        PartRequestMessage.objects.create(
            part_request=self.part_req,
            sender_is_admin=True,
            message='We sourced the 86Wh battery from Dell authorized distributor.'
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['client@example.com'])
        self.assertIn(self.part_req.request_id, email.subject)
        self.assertIn("sourced the 86Wh battery", email.body)

    def test_customer_can_edit_and_delete_their_message(self):
        self.client.login(username='partclient', password='Password123!')
        msg = PartRequestMessage.objects.create(
            part_request=self.part_req,
            sender_is_admin=False,
            message='Initial message'
        )
        # Edit
        response = self.client.post(
            reverse('edit_part_request_message', args=[msg.id]),
            {'message': 'Updated message text'}
        )
        self.assertEqual(response.status_code, 302)
        msg.refresh_from_db()
        self.assertEqual(msg.message, 'Updated message text')

        # Delete
        response = self.client.post(reverse('delete_part_request_message', args=[msg.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PartRequestMessage.objects.filter(id=msg.id).exists())

    def test_customer_can_approve_and_decline_part_quote(self):
        self.part_req.status = 'quoted'
        self.part_req.quote_status = 'sent'
        self.part_req.quoted_price = 450.00
        self.part_req.save()

        self.client.login(username='partclient', password='Password123!')

        # Decline
        response = self.client.post(reverse('customer_decline_part_quote', args=[self.part_req.request_id]))
        self.assertEqual(response.status_code, 302)
        self.part_req.refresh_from_db()
        self.assertEqual(self.part_req.quote_status, 'declined')
        self.assertEqual(self.part_req.status, 'quoted')



class StaffClientQuoteButtonTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('qstaff', 'qs@example.com', 'x', first_name='Ama', last_name='Mensah', is_staff=True)
        self.ticket = RepairTicket.objects.create(
            customer_name='Kofi', customer_email='kofi@example.com', customer_phone='0200000007', device='MBP',
            status='quoted', quote_status='sent', quoted_price=450)
        self.part = PartRequest.objects.create(
            customer_name='Esi', customer_email='esi@example.com', customer_phone='0200000008',
            part_needed='Battery', device_model='A1', status='quoted', quote_status='sent', quoted_price=300)

    def test_staff_do_not_see_the_clients_authorize_and_decline_buttons(self):
        self.client.force_login(self.staff)
        for name, arg in (('track_repair', self.ticket.ticket_id), ('track_part', self.part.request_id)):
            html = self.client.get(reverse(name, args=[arg])).content.decode()
            self.assertIn('Awaiting client approval', html)
            self.assertIn('Mark approved (client agreed by phone/WhatsApp)', html)
            self.assertNotIn('Authorize (GH', html)
            self.assertNotIn('Confirm Order (GH', html)
            self.assertNotIn('customer_decline', html)

    def test_clients_still_see_their_own_buttons(self):
        c = self.client_class()
        c.post(reverse('track_repair_lookup'), {'ticket_id': self.ticket.ticket_id, 'phone': '0200000007'})
        c.post(reverse('track_part_lookup'), {'request_id': self.part.request_id, 'phone': '0200000008'})
        self.assertContains(c.get(reverse('track_repair', args=[self.ticket.ticket_id])), 'Authorize (GH')
        self.assertContains(c.get(reverse('track_part', args=[self.part.request_id])), 'Confirm Order (GH')
        self.assertNotContains(c.get(reverse('track_part', args=[self.part.request_id])), 'Mark approved')

    def test_staff_recorded_approval_is_attributed_in_the_thread(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        self.client.post(reverse('customer_approve_part_quote', args=[self.part.request_id]))
        self.ticket.refresh_from_db(); self.part.refresh_from_db()
        self.assertEqual((self.ticket.status, self.ticket.quote_status), ('in_progress', 'approved'))
        self.assertEqual(self.part.quote_status, 'approved')
        from .models import RepairMessage, PartRequestMessage
        for msg in (RepairMessage.objects.filter(ticket=self.ticket).latest('id'),
                    PartRequestMessage.objects.filter(part_request=self.part).latest('id')):
            self.assertIn("on the client's behalf by Ama Mensah", msg.message)
            self.assertTrue(msg.sender_is_admin)
            self.assertNotIn('Client Kofi approved', msg.message)

    def test_client_approval_message_is_unchanged(self):
        c = self.client_class()
        c.post(reverse('track_repair_lookup'), {'ticket_id': self.ticket.ticket_id, 'phone': '0200000007'})
        c.post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        from .models import RepairMessage
        msg = RepairMessage.objects.filter(ticket=self.ticket).latest('id')
        self.assertIn('Client Kofi approved the repair estimate', msg.message)
        self.assertFalse(msg.sender_is_admin)


class QuoteApprovalAdvancesBothTypesTests(TestCase):
    def setUp(self):
        self.ticket = RepairTicket.objects.create(
            customer_name='R', customer_email='r@example.com', customer_phone='0200000011', device='d',
            status='quoted', quote_status='sent', quoted_price=100)
        self.part = PartRequest.objects.create(
            customer_name='P', customer_email='p@example.com', customer_phone='0200000012',
            part_needed='Battery', device_model='m', status='quoted', quote_status='sent', quoted_price=100)

    def _client_with_access(self):
        c = self.client_class()
        c.post(reverse('track_repair_lookup'), {'ticket_id': self.ticket.ticket_id, 'phone': '0200000011'})
        c.post(reverse('track_part_lookup'), {'request_id': self.part.request_id, 'phone': '0200000012'})
        return c

    def test_client_approval_moves_both_to_in_progress(self):
        c = self._client_with_access()
        c.post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        mail.outbox.clear()
        c.post(reverse('customer_approve_part_quote', args=[self.part.request_id]))
        self.ticket.refresh_from_db(); self.part.refresh_from_db()
        self.assertEqual((self.ticket.status, self.ticket.quote_status), ('in_progress', 'approved'))
        self.assertEqual((self.part.status, self.part.quote_status), ('in_progress', 'approved'))
        customer_mail = [m for m in mail.outbox if m.to == ['p@example.com']]
        self.assertEqual(len(customer_mail), 1)
        self.assertIn('Sourcing Underway', customer_mail[0].subject)
        self.assertEqual(len([m for m in mail.outbox if m.to == ['support@compupartz.com']]), 1)

    def test_staff_recorded_approval_also_advances_a_part_request(self):
        staff = User.objects.create_user('pstaff', 'ps@example.com', 'x', is_staff=True)
        self.client.force_login(staff)
        self.client.post(reverse('customer_approve_part_quote', args=[self.part.request_id]))
        self.part.refresh_from_db()
        self.assertEqual(self.part.status, 'in_progress')

    def test_part_without_a_sent_quote_is_not_advanced(self):
        self.part.quote_status = 'none'; self.part.status = 'pending'; self.part.save()
        c = self._client_with_access()
        c.post(reverse('customer_approve_part_quote', args=[self.part.request_id]))
        self.part.refresh_from_db()
        self.assertEqual(self.part.status, 'pending')

    def test_in_progress_is_shown_and_selectable_for_staff_and_can_move_to_fulfilled(self):
        self.part.status, self.part.quote_status = 'in_progress', 'approved'; self.part.save()
        staff = User.objects.create_user('pstaff2', 'ps2@example.com', 'x', is_staff=True)
        self.client.force_login(staff)
        html = self.client.get(reverse('track_part', args=[self.part.request_id])).content.decode()
        self.assertIn('value="in_progress" selected', html)
        self.client.post(reverse('staff_update_part_status', args=[self.part.request_id]), {'status': 'fulfilled'})
        self.part.refresh_from_db()
        self.assertEqual(self.part.status, 'fulfilled')

    def test_migration_advances_previously_approved_parts_only(self):
        import importlib
        from django.apps import apps
        mig = importlib.import_module('repair.migrations.0014_part_request_in_progress_status')
        old_approved = PartRequest.objects.create(customer_name='O', customer_phone='1', part_needed='x', device_model='y', status='quoted', quote_status='approved')
        still_waiting = PartRequest.objects.create(customer_name='W', customer_phone='2', part_needed='x', device_model='y', status='quoted', quote_status='sent')
        done = PartRequest.objects.create(customer_name='D', customer_phone='3', part_needed='x', device_model='y', status='fulfilled', quote_status='approved')
        mig.advance_already_approved_parts(apps, None)
        for obj in (old_approved, still_waiting, done):
            obj.refresh_from_db()
        self.assertEqual(old_approved.status, 'in_progress')
        self.assertEqual(still_waiting.status, 'quoted')
        self.assertEqual(done.status, 'fulfilled')


class QuoteApprovedAdminAlertTests(TestCase):
    def setUp(self):
        self.ticket = RepairTicket.objects.create(
            customer_name='Kofi <b>Mensah</b>', customer_email='kofi@example.com', customer_phone='0244123456',
            device='MacBook Pro', status='quoted', quote_status='sent', quoted_price=450,
            estimated_turnaround='48h', warranty_period='90 days')
        self.part = PartRequest.objects.create(
            customer_name='Esi Boateng', customer_email='esi@example.com', customer_phone='0244000111',
            part_needed='Mother board', device_model='Lenovo X1', condition_preference='new',
            status='quoted', quote_status='sent', quoted_price=1200, estimated_delivery='3 - 5 Days')

    def _client(self):
        c = self.client_class()
        c.post(reverse('track_repair_lookup'), {'ticket_id': self.ticket.ticket_id, 'phone': '0244123456'})
        c.post(reverse('track_part_lookup'), {'request_id': self.part.request_id, 'phone': '0244000111'})
        return c

    def _alerts(self):
        return [m for m in mail.outbox if m.to == ['support@compupartz.com']]

    def test_support_is_alerted_when_a_client_approves_a_repair_quote(self):
        mail.outbox.clear()
        self._client().post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        alert = self._alerts()[0]
        self.assertEqual(len(self._alerts()), 1)
        self.assertIn(f'[Quote Approved] #{self.ticket.ticket_id}', alert.subject)
        self.assertIn('GH₵ 450', alert.subject)
        self.assertEqual(alert.reply_to, ['kofi@example.com'])
        for text in ('Client Approved Repair Quote', 'In Progress', 'MacBook Pro', '48h', '90 days',
                     f'/admin/repair/repairticket/{self.ticket.id}/change/', 'https://wa.me/233244123456'):
            self.assertIn(text, alert.body)
        self.assertIn('&lt;b&gt;Mensah&lt;/b&gt;', alert.body)
        self.assertNotIn('<b>Mensah</b>', alert.body)

    def test_support_is_alerted_when_a_client_approves_a_part_quote(self):
        mail.outbox.clear()
        self._client().post(reverse('customer_approve_part_quote', args=[self.part.request_id]))
        alert = self._alerts()[0]
        self.assertEqual(len(self._alerts()), 1)
        self.assertIn(f'[Quote Approved] #{self.part.request_id}', alert.subject)
        for text in ('Client Approved Part Quote', 'Sourcing in Progress', 'Mother board', 'Lenovo X1', '3 - 5 Days',
                     f'/admin/repair/partrequest/{self.part.id}/change/'):
            self.assertIn(text, alert.body)

    def test_no_alert_when_staff_record_the_approval_or_when_a_client_declines(self):
        staff = User.objects.create_user('alertstaff', 'als@example.com', 'x', is_staff=True)
        self.client.force_login(staff)
        mail.outbox.clear()
        self.client.post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        self.client.post(reverse('customer_approve_part_quote', args=[self.part.request_id]))
        self.assertEqual(self._alerts(), [])
        self.ticket.quote_status, self.ticket.status = 'sent', 'quoted'; self.ticket.save()
        self._client().post(reverse('customer_decline_repair_quote', args=[self.ticket.ticket_id]))
        self.assertEqual(self._alerts(), [])

    def test_no_alert_when_there_was_no_quote_to_approve(self):
        self.ticket.quote_status, self.ticket.status = 'none', 'pending'; self.ticket.save()
        mail.outbox.clear()
        self._client().post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        self.assertEqual(self._alerts(), [])

    def test_existing_intake_alerts_still_use_their_own_layouts(self):
        mail.outbox.clear()
        send_admin_part_request_notification(self.part)
        send_admin_repair_notification(self.ticket)
        bodies = ' '.join(m.body for m in self._alerts())
        self.assertIn('Submitted', bodies)
        self.assertNotIn('Client Approved', bodies)

    def test_preview_is_staff_only_and_renders_both_versions(self):
        url = reverse('preview_admin_quote_approved_email')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(User.objects.create_user('pv', 'pv@example.com', 'x', is_staff=True))
        self.assertContains(self.client.get(url), 'Client Approved Part Quote')
        self.assertContains(self.client.get(url + '?kind=repair'), 'Client Approved Repair Quote')


class QuoteApprovedSameTemplateTests(TestCase):
    @staticmethod
    def _skeleton(html):
        import re
        html = re.sub(r'(href|src)="[^"]*"', r'\1=""', html)
        html = re.sub(r'>[^<]+<', '><', html)
        return re.sub(r'\s+', ' ', html).strip()

    def _bodies(self):
        from core.notifications import send_admin_quote_approved_notification
        t = RepairTicket.objects.create(
            customer_name='Kwame', customer_email='k@example.com', customer_phone='0244123456', device_category='laptop',
            manufacturer='Apple', device='MBP A2485', issue_description='No power', quoted_price=850,
            estimated_turnaround='48h', warranty_period='90d', status='in_progress', quote_status='approved')
        p = PartRequest.objects.create(
            customer_name='Esi', customer_email='e@example.com', customer_phone='0244000111', part_needed='Mother board',
            device_model='Lenovo X1', condition_preference='new', quoted_price=1200, estimated_delivery='3 days',
            warranty_period='90d', status='in_progress', quote_status='approved')
        mail.outbox.clear()
        send_admin_quote_approved_notification(t)
        send_admin_quote_approved_notification(p)
        return mail.outbox[0].body, mail.outbox[1].body

    def test_repair_and_part_alerts_share_the_exact_same_layout(self):
        repair, part = self._bodies()
        self.assertEqual(self._skeleton(repair), self._skeleton(part))

    def test_both_show_the_same_rows_in_the_same_order(self):
        import re
        labels = lambda body: re.findall(r'color: #64748b; font-weight: 600;[^>]*>([^<]+)</td>', body)
        repair, part = self._bodies()
        expected = ['Reference', 'Customer Name', 'Email Address', 'Phone Number', 'Request Type',
                    'Work Requested', 'Device / Model', None, 'Approved Price', None, 'Warranty', 'Current Status']
        for body in (repair, part):
            found = labels(body)
            self.assertEqual(len(found), len(expected), found)
            for got, want in zip(found, expected):
                if want:
                    self.assertEqual(got, want)
        self.assertEqual((labels(repair)[7], labels(repair)[9]), ('Drop-off Method', 'Turnaround'))
        self.assertEqual((labels(part)[7], labels(part)[9]), ('Condition', 'Estimated Delivery'))

    def test_values_differ_per_type_but_never_leak_across(self):
        repair, part = self._bodies()
        for text in ('Device Repair', 'MBP A2485', 'No power', 'Apple Laptop', '48h', 'Drop-off', 'Client Approved Repair Quote'):
            self.assertIn(text, repair)
            self.assertNotIn(text, part)
        for text in ('Part Sourcing', 'Mother board', 'Lenovo X1', '3 days', 'Client Approved Part Quote'):
            self.assertIn(text, part)
            self.assertNotIn(text, repair)


class StaffMessageEmailsCustomerTests(TestCase):
    """Guards against the shared message email template failing for one of the two item types."""

    def setUp(self):
        self.ticket = RepairTicket.objects.create(
            customer_name='Kofi', customer_email='kofi@example.com', customer_phone='0200000021', device='MBP')
        self.part = PartRequest.objects.create(
            customer_name='Esi', customer_email='esi@example.com', customer_phone='0200000022',
            part_needed='Fan', device_model='X1')
        self.staff = User.objects.create_user('msgstaff', 'ms@example.com', 'x', is_staff=True)

    def test_staff_message_on_a_repair_ticket_emails_the_customer(self):
        from .models import RepairMessage
        mail.outbox.clear()
        RepairMessage.objects.create(ticket=self.ticket, message='Your laptop is ready for pickup', sender_is_admin=True)
        sent = [m for m in mail.outbox if m.to == ['kofi@example.com']]
        self.assertEqual(len(sent), 1)
        self.assertIn('Lab Bench Update', sent[0].subject)
        self.assertIn('Hello <strong>Kofi</strong>', sent[0].alternatives[0][0])
        self.assertIn('Your laptop is ready for pickup', sent[0].alternatives[0][0])

    def test_staff_message_on_a_part_request_emails_the_customer(self):
        from .models import PartRequestMessage
        mail.outbox.clear()
        PartRequestMessage.objects.create(part_request=self.part, message='We found your fan', sender_is_admin=True)
        sent = [m for m in mail.outbox if m.to == ['esi@example.com']]
        self.assertEqual(len(sent), 1)
        self.assertIn('Sourcing Desk Update', sent[0].subject)
        self.assertIn('Hello <strong>Esi</strong>', sent[0].alternatives[0][0])

    def test_posting_a_message_through_the_tracking_page_sends_the_email_end_to_end(self):
        self.client.force_login(self.staff)
        mail.outbox.clear()
        self.client.post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': 'Quick update'})
        self.assertEqual(len([m for m in mail.outbox if m.to == ['kofi@example.com']]), 1)

    def test_customers_own_messages_never_email_themselves(self):
        from .models import RepairMessage
        mail.outbox.clear()
        RepairMessage.objects.create(ticket=self.ticket, message='When will it be ready?', sender_is_admin=False)
        self.assertEqual([m for m in mail.outbox if m.to == ['kofi@example.com']], [])


class TrackingPageBackLinkTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('backowner', 'bo@example.com', 'x')
        self.staff = User.objects.create_user('backstaff', 'bs@example.com', 'x', is_staff=True)
        self.ticket = RepairTicket.objects.create(
            user=self.owner, customer_name='B', customer_email='bo@example.com', customer_phone='0200000061', device='d')
        self.part = PartRequest.objects.create(
            user=self.owner, customer_name='B', customer_email='bo@example.com', customer_phone='0200000062',
            part_needed='p', device_model='m')

    def _backs(self, resp):
        import re
        html = resp.content.decode()
        return set(re.findall(r'href="([^"]+)"[^>]*>\s*<span[^>]*>&larr;</span>\s*<span>Back</span>', html))

    def test_guest_back_link_goes_to_the_lookup_page_not_a_login_wall(self):
        guest = self.client_class()
        guest.post(reverse('track_repair_lookup'), {'ticket_id': self.ticket.ticket_id, 'phone': '0200000061'})
        guest.post(reverse('track_part_lookup'), {'request_id': self.part.request_id, 'phone': '0200000062'})
        self.assertEqual(self._backs(guest.get(reverse('track_repair', args=[self.ticket.ticket_id]))), {reverse('track_repair_lookup')})
        self.assertEqual(self._backs(guest.get(reverse('track_part', args=[self.part.request_id]))), {reverse('track_part_lookup')})

    def test_owner_and_staff_back_links_still_go_to_the_right_dashboard_tab(self):
        self.client.force_login(self.owner)
        self.assertEqual(self._backs(self.client.get(reverse('track_repair', args=[self.ticket.ticket_id]))), {reverse('dashboard')})
        self.client.force_login(self.staff)
        self.assertEqual(self._backs(self.client.get(reverse('track_repair', args=[self.ticket.ticket_id]))), {reverse('dashboard') + '?tab=staff-workshop'})
        self.assertEqual(self._backs(self.client.get(reverse('track_part', args=[self.part.request_id]))), {reverse('dashboard') + '?tab=hardware-parts-queue'})


class TrackingPageStructureTests(TestCase):
    """An unclosed <div> in the chat loop once swallowed the Back row into the chat card."""

    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr',
            'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'stop'}

    def _unbalanced(self, html):
        from html.parser import HTMLParser
        outer = self

        class P(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack, self.bad = [], []

            def handle_starttag(self, tag, attrs):
                if tag not in outer.VOID:
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if tag in outer.VOID:
                    return
                if self.stack and self.stack[-1] == tag:
                    self.stack.pop()
                else:
                    self.bad.append(tag)

        p = P()
        p.feed(html)
        return p.bad, p.stack

    def setUp(self):
        self.owner = User.objects.create_user('domowner', 'do@example.com', 'x')
        self.ticket = RepairTicket.objects.create(
            user=self.owner, customer_name='D', customer_email='do@example.com', customer_phone='0200000081', device='d')
        self.part = PartRequest.objects.create(
            user=self.owner, customer_name='D', customer_email='do@example.com', customer_phone='0200000082',
            part_needed='p', device_model='m')
        from .models import RepairMessage, PartRequestMessage
        for i in range(3):
            RepairMessage.objects.create(ticket=self.ticket, message=f'client {i}', sender_is_admin=False)
            RepairMessage.objects.create(ticket=self.ticket, message=f'staff {i}', sender_is_admin=True)
            PartRequestMessage.objects.create(part_request=self.part, message=f'client {i}', sender_is_admin=False)
            PartRequestMessage.objects.create(part_request=self.part, message=f'staff {i}', sender_is_admin=True)
        self.client.force_login(self.owner)

    def test_tracking_pages_with_messages_are_well_formed(self):
        for name, arg in (('track_repair', self.ticket.ticket_id), ('track_part', self.part.request_id)):
            bad, unclosed = self._unbalanced(self.client.get(reverse(name, args=[arg])).content.decode())
            self.assertEqual((bad, unclosed), ([], []), name)

    def test_repair_page_with_no_messages_is_well_formed(self):
        empty = RepairTicket.objects.create(
            user=self.owner, customer_name='E', customer_email='do@example.com', customer_phone='0200000083', device='d')
        bad, unclosed = self._unbalanced(self.client.get(reverse('track_repair', args=[empty.ticket_id])).content.decode())
        self.assertEqual((bad, unclosed), ([], []))

    def test_back_row_sits_after_the_chat_card_not_inside_it(self):
        html = self.client.get(reverse('track_repair', args=[self.ticket.ticket_id])).content.decode()
        chat_start = html.index('id="chat-box"')
        back_row = html.index('Bottom Back Navigation')
        chat_box_html = html[chat_start:back_row]
        opens, closes = chat_box_html.count('<div'), chat_box_html.count('</div>')
        self.assertGreaterEqual(closes, opens + 1, 'chat box and its card must be closed before the Back row')
        self.assertEqual(html.count('class="flex flex-col items-end"') + html.count('class="flex flex-col items-start"'), 6)


class ChatEmailNotificationTests(TestCase):
    """Who gets emailed when someone sends a chat message in the repair or part-sourcing queue."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.staff = User.objects.create_user('chatstaff', 'cs@example.com', 'x', is_staff=True)
        self.ticket = RepairTicket.objects.create(
            customer_name='Kofi', customer_email='kofi@example.com', customer_phone='0200000091', device='MBP',
            status='in_progress')
        self.part = PartRequest.objects.create(
            customer_name='Esi', customer_email='esi@example.com', customer_phone='0200000092',
            part_needed='Board', device_model='X1', status='in_progress')

    def _client_for(self):
        c = self.client_class()
        c.post(reverse('track_repair_lookup'), {'ticket_id': self.ticket.ticket_id, 'phone': '0200000091'})
        c.post(reverse('track_part_lookup'), {'request_id': self.part.request_id, 'phone': '0200000092'})
        return c

    def _emails_to(self, addr):
        return [m for m in mail.outbox if m.to == [addr]]

    def test_staff_chat_in_either_queue_emails_the_client(self):
        self.client.force_login(self.staff)
        for url, addr, subject in ((reverse('track_repair', args=[self.ticket.ticket_id]), 'kofi@example.com', 'Lab Bench Update'),
                                   (reverse('track_part', args=[self.part.request_id]), 'esi@example.com', 'Sourcing Desk Update')):
            mail.outbox.clear()
            self.client.post(url, {'message': 'Please bring your charger.'})
            sent = self._emails_to(addr)
            self.assertEqual(len(sent), 1, url)
            self.assertIn(subject, sent[0].subject)
            self.assertIn('Please bring your charger.', sent[0].alternatives[0][0])

    def test_staff_chat_starting_with_a_status_emoji_is_still_emailed(self):
        self.client.force_login(self.staff)
        for emoji in ('📦', '🔧', '✅', '❌', '📋'):
            for url, addr in ((reverse('track_repair', args=[self.ticket.ticket_id]), 'kofi@example.com'),
                              (reverse('track_part', args=[self.part.request_id]), 'esi@example.com')):
                mail.outbox.clear()
                self.client.post(url, {'message': f'{emoji} All good, come collect it.'})
                self.assertEqual(len(self._emails_to(addr)), 1, (emoji, url))

    def test_automatic_notes_do_not_double_email_the_client(self):
        self.client.force_login(self.staff)
        mail.outbox.clear()
        self.client.post(reverse('staff_create_repair_quote', args=[self.ticket.ticket_id]),
                         {'quoted_price': '100', 'diagnostic_notes': 'n', 'estimated_turnaround': '1d', 'warranty_period': '90d'})
        self.assertEqual(len(self._emails_to('kofi@example.com')), 1)
        mail.outbox.clear()
        self.client.post(reverse('staff_update_repair_status', args=[self.ticket.ticket_id]), {'status': 'completed'})
        self.assertEqual(len(self._emails_to('kofi@example.com')), 1)
        mail.outbox.clear()
        self.client.post(reverse('staff_create_part_quote', args=[self.part.request_id]),
                         {'quoted_price': '50', 'admin_notes': 'n', 'estimated_delivery': '2d', 'warranty_period': '30d'})
        self.assertEqual(len(self._emails_to('esi@example.com')), 1)

    def test_client_chat_never_emails_the_client_back(self):
        c = self._client_for()
        mail.outbox.clear()
        c.post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': 'Is it ready?'})
        c.post(reverse('track_part', args=[self.part.request_id]), {'message': 'Any update?'})
        self.assertEqual(self._emails_to('kofi@example.com'), [])
        self.assertEqual(self._emails_to('esi@example.com'), [])

    def test_editing_a_message_sends_no_email(self):
        from .models import RepairMessage
        msg = RepairMessage.objects.create(ticket=self.ticket, message='first', sender_is_admin=True)
        self.client.force_login(self.staff)
        mail.outbox.clear()
        self.client.post(reverse('edit_repair_message', args=[msg.id]), {'message': 'edited'})
        self.assertEqual(mail.outbox, [])


    def test_a_revised_quote_is_still_emailed_but_never_twice(self):
        self.client.force_login(self.staff)
        form = {'quoted_price': '100', 'diagnostic_notes': 'n', 'estimated_turnaround': '1d', 'warranty_period': '90d'}
        pform = {'quoted_price': '50', 'admin_notes': 'n', 'estimated_delivery': '2d', 'warranty_period': '30d'}
        for price in ('100', '130'):
            mail.outbox.clear()
            self.client.post(reverse('staff_create_repair_quote', args=[self.ticket.ticket_id]), dict(form, quoted_price=price))
            self.assertEqual(len(self._emails_to('kofi@example.com')), 1, price)
        for price in ('50', '70'):
            mail.outbox.clear()
            self.client.post(reverse('staff_create_part_quote', args=[self.part.request_id]), dict(pform, quoted_price=price))
            self.assertEqual(len(self._emails_to('esi@example.com')), 1, price)

    def test_admin_send_formal_quote_actions_email_once(self):
        admin_user = User.objects.create_superuser('chatadmin', 'ca@example.com', 'x')
        self.client.force_login(admin_user)
        self.ticket.quoted_price = 90
        self.ticket.save()
        self.part.quoted_price = 40
        self.part.save()
        mail.outbox.clear()
        self.client.post(reverse('admin:repair_repairticket_changelist'),
                         {'action': 'send_formal_quote', '_selected_action': [self.ticket.pk]})
        self.assertEqual(len(self._emails_to('kofi@example.com')), 1)
        mail.outbox.clear()
        self.client.post(reverse('admin:repair_partrequest_changelist'),
                         {'action': 'send_formal_part_quote', '_selected_action': [self.part.pk]})
        self.assertEqual(len(self._emails_to('esi@example.com')), 1)

    def test_part_intake_confirmation_is_not_affected_by_the_quote_dedupe(self):
        c = self.client_class()
        mail.outbox.clear()
        for name in ('Ama', 'Yaw'):
            c.post(reverse('request_part'), dict(customer_name=name, customer_email='same@example.com',
                   customer_phone='0244000111', part_needed='Fan', device_model='Y', condition_preference='new'))
        self.assertEqual(len(self._emails_to('same@example.com')), 2)


class ExistingSupportAndClientEmailsStillWorkTests(TestCase):
    """Guards every email the site already sent, so adding new alerts can never switch one off."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.staff = User.objects.create_user('matrixstaff', 'ms@example.com', 'x', is_staff=True)
        self.cs = self.client_class()
        self.cs.force_login(self.staff)

    def _to(self, addr):
        return [m for m in mail.outbox if m.to == [addr]]

    def test_new_repair_booking_emails_client_and_support(self):
        mail.outbox.clear()
        self.client.post(reverse('book_repair'), dict(
            customer_name='Ama', customer_email='ama@example.com', customer_phone='0244000401', device_category='laptop',
            manufacturer='Apple', device='MBP', issue_description='No power', logistics_preference='drop_off'))
        self.assertEqual(len(self._to('ama@example.com')), 1)
        self.assertIn('[New Repair Ticket]', self._to('support@compupartz.com')[0].subject)

    def test_new_part_request_emails_client_and_support(self):
        mail.outbox.clear()
        self.client.post(reverse('request_part'), dict(
            customer_name='Yaw', customer_email='yaw@example.com', customer_phone='0244000402',
            part_needed='Battery', device_model='A2338', condition_preference='new'))
        self.assertEqual(len(self._to('yaw@example.com')), 1)
        self.assertIn('[New Part Request]', self._to('support@compupartz.com')[0].subject)

    def test_quotes_status_updates_and_chats_reach_the_client(self):
        t = RepairTicket.objects.create(customer_name='K', customer_email='k@example.com', customer_phone='0244000403', device='d', status='in_progress')
        p = PartRequest.objects.create(customer_name='E', customer_email='e@example.com', customer_phone='0244000404', part_needed='x', device_model='y', status='in_progress')
        steps = [
            (lambda: self.cs.post(reverse('staff_create_repair_quote', args=[t.ticket_id]), {'quoted_price': '90', 'diagnostic_notes': 'n', 'estimated_turnaround': '1d', 'warranty_period': '90d'}), 'k@example.com', 'Formal Repair Quotation'),
            (lambda: self.cs.post(reverse('staff_create_part_quote', args=[p.request_id]), {'quoted_price': '40', 'admin_notes': 'n', 'estimated_delivery': '2d', 'warranty_period': '30d'}), 'e@example.com', 'Formal Part Sourcing Quotation'),
            (lambda: self.cs.post(reverse('staff_update_repair_status', args=[t.ticket_id]), {'status': 'completed'}), 'k@example.com', 'Restoration Complete'),
            (lambda: self.cs.post(reverse('staff_update_part_status', args=[p.request_id]), {'status': 'fulfilled'}), 'e@example.com', 'Procured'),
            (lambda: self.cs.post(reverse('staff_update_repair_status', args=[t.ticket_id]), {'status': 'no_fix'}), 'k@example.com', 'No-Fix'),
            (lambda: self.cs.post(reverse('track_repair', args=[t.ticket_id]), {'message': 'hello'}), 'k@example.com', 'Lab Bench Update'),
            (lambda: self.cs.post(reverse('track_part', args=[p.request_id]), {'message': 'hello'}), 'e@example.com', 'Sourcing Desk Update'),
        ]
        for action, addr, subject in steps:
            mail.outbox.clear()
            action()
            sent = self._to(addr)
            self.assertEqual(len(sent), 1, subject)
            self.assertIn(subject, sent[0].subject)

    def test_client_quote_approval_alerts_support_and_a_review_alerts_support(self):
        t = RepairTicket.objects.create(customer_name='K', customer_email='k@example.com', customer_phone='0244000405', device='d', status='quoted', quote_status='sent', quoted_price=90)
        c = self.client_class()
        c.post(reverse('track_repair_lookup'), {'ticket_id': t.ticket_id, 'phone': '0244000405'})
        mail.outbox.clear()
        c.post(reverse('customer_approve_repair_quote', args=[t.ticket_id]))
        self.assertTrue(any('[Quote Approved]' in m.subject for m in self._to('support@compupartz.com')))
        mail.outbox.clear()
        self.client.post(reverse('submit_testimonial'), {'quote': 'Great', 'name': 'Rev', 'rating': '5'})
        self.assertTrue(any('[New Review]' in m.subject for m in self._to('support@compupartz.com')))
        mail.outbox.clear()
        self.client.post(reverse('contact'), {'name': 'N', 'email': 'n@example.com', 'subject': 'Hi', 'message': 'x'})
        self.assertTrue(any('[Contact Form]' in m.subject for m in self._to('support@compupartz.com')))


class ClientChatAlertToSupportTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.staff = User.objects.create_user('alertchatstaff', 'acs@example.com', 'x', is_staff=True)
        self.ticket = RepairTicket.objects.create(
            customer_name='Kofi <b>Mensah</b>', customer_email='kofi@example.com', customer_phone='0244123456',
            device='MacBook Pro', status='in_progress')
        self.part = PartRequest.objects.create(
            customer_name='Esi Boateng', customer_email='esi@example.com', customer_phone='0244000111',
            part_needed='Mother board', device_model='Lenovo X1', status='in_progress')

    def _client(self):
        c = self.client_class()
        c.post(reverse('track_repair_lookup'), {'ticket_id': self.ticket.ticket_id, 'phone': '0244123456'})
        c.post(reverse('track_part_lookup'), {'request_id': self.part.request_id, 'phone': '0244000111'})
        return c

    def _support(self):
        return [m for m in mail.outbox if m.to == ['support@compupartz.com']]

    def test_support_is_emailed_when_a_client_chats_in_the_repair_queue(self):
        mail.outbox.clear()
        self._client().post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': 'Is my laptop ready?\nI can come at 4pm.'})
        alerts = self._support()
        self.assertEqual(len(alerts), 1)
        a = alerts[0]
        self.assertEqual(a.subject, f'[Client Message] #{self.ticket.ticket_id} — Kofi <b>Mensah</b>')
        for text in ('New Client Message on Repair', 'Is my laptop ready?', 'I can come at 4pm.', 'MacBook Pro',
                     f'/admin/repair/repairticket/{self.ticket.id}/change/', 'https://wa.me/233244123456'):
            self.assertIn(text, a.body)
        self.assertEqual(a.reply_to, ['kofi@example.com'])
        self.assertIn('&lt;b&gt;Mensah&lt;/b&gt;', a.body)
        self.assertNotIn('<b>Mensah</b>', a.body)

    def test_support_is_emailed_when_a_client_chats_in_the_part_sourcing_queue(self):
        mail.outbox.clear()
        self._client().post(reverse('track_part', args=[self.part.request_id]), {'message': 'Any update on the board?'})
        alerts = self._support()
        self.assertEqual(len(alerts), 1)
        for text in ('New Client Message on Part Sourcing', 'Any update on the board?', 'Mother board', 'Lenovo X1',
                     f'/admin/repair/partrequest/{self.part.id}/change/'):
            self.assertIn(text, alerts[0].body)
        self.assertIn(f'[Client Message] #{self.part.request_id}', alerts[0].subject)

    def test_a_logged_in_client_triggers_the_alert_too(self):
        owner = User.objects.create_user('chatowner', 'co@example.com', 'x')
        self.ticket.user = owner
        self.ticket.save()
        self.client.force_login(owner)
        mail.outbox.clear()
        self.client.post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': 'Hello from my account'})
        self.assertEqual(len(self._support()), 1)

    def test_message_text_is_escaped_in_the_alert(self):
        mail.outbox.clear()
        self._client().post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': '<script>alert(1)</script> hi'})
        body = self._support()[0].body
        self.assertNotIn('<script>alert(1)</script>', body)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', body)

    def test_no_alert_for_staff_messages_blank_messages_or_edits(self):
        from .models import RepairMessage
        self.client.force_login(self.staff)
        mail.outbox.clear()
        self.client.post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': 'We are on it.'})
        self.client.post(reverse('track_part', args=[self.part.request_id]), {'message': 'Part located.'})
        self.assertEqual(self._support(), [])
        c = self._client()
        c.post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': '   '})
        self.assertEqual(self._support(), [])
        msg = RepairMessage.objects.create(ticket=self.ticket, message='original', sender_is_admin=False)
        c.post(reverse('edit_repair_message', args=[msg.id]), {'message': 'edited'})
        self.assertEqual(self._support(), [])

    def test_automatic_client_notes_do_not_trigger_the_chat_alert(self):
        self.ticket.status, self.ticket.quote_status, self.ticket.quoted_price = 'quoted', 'sent', 100
        self.ticket.save()
        mail.outbox.clear()
        self._client().post(reverse('customer_approve_repair_quote', args=[self.ticket.ticket_id]))
        subjects = [m.subject for m in self._support()]
        self.assertEqual(len(subjects), 1)
        self.assertIn('[Quote Approved]', subjects[0])

    def test_preview_page_is_staff_only_and_renders_both_versions(self):
        url = reverse('preview_admin_client_message_email')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(url), 'New Client Message on Part Sourcing')
        self.assertContains(self.client.get(url + '?kind=repair'), 'New Client Message on Repair')


class SupportOnlyReceivesTheAgreedAlertsTests(TestCase):
    """support@compupartz.com gets: new ticket, new part request, review, contact form,
    approved quote and client chats. Quotations, status updates and staff messages go to the client alone."""

    ALLOWED = ('[New Repair Ticket]', '[New Part Request]', '[New Review]', '[Contact Form]', '[Quote Approved]', '[Client Message]')

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.staff = User.objects.create_user('policystaff', 'ps@example.com', 'x', is_staff=True)
        self.cs = self.client_class()
        self.cs.force_login(self.staff)

    def _support_subjects(self):
        return [m.subject for m in mail.outbox if m.to == ['support@compupartz.com']]

    def test_every_staff_action_reaches_the_client_and_never_support(self):
        t = RepairTicket.objects.create(customer_name='K', customer_email='k@example.com', customer_phone='0244000611', device='d', status='in_progress')
        p = PartRequest.objects.create(customer_name='E', customer_email='e@example.com', customer_phone='0244000612', part_needed='x', device_model='y', status='in_progress')
        actions = [
            lambda: self.cs.post(reverse('staff_create_repair_quote', args=[t.ticket_id]), {'quoted_price': '90', 'diagnostic_notes': 'n', 'estimated_turnaround': '1d', 'warranty_period': '90d'}),
            lambda: self.cs.post(reverse('staff_create_part_quote', args=[p.request_id]), {'quoted_price': '40', 'admin_notes': 'n', 'estimated_delivery': '2d', 'warranty_period': '30d'}),
            lambda: self.cs.post(reverse('staff_update_repair_status', args=[t.ticket_id]), {'status': 'completed', 'status_note': 'done'}),
            lambda: self.cs.post(reverse('staff_update_part_status', args=[p.request_id]), {'status': 'fulfilled', 'admin_notes': 'ready'}),
            lambda: self.cs.post(reverse('track_repair', args=[t.ticket_id]), {'message': 'hello'}),
            lambda: self.cs.post(reverse('track_part', args=[p.request_id]), {'message': 'hello'}),
        ]
        for action in actions:
            mail.outbox.clear()
            action()
            self.assertEqual(self._support_subjects(), [])
            self.assertTrue(any(m.to in (['k@example.com'], ['e@example.com']) for m in mail.outbox))

    def test_support_only_ever_receives_the_agreed_subjects(self):
        guest = self.client_class()
        mail.outbox.clear()
        guest.post(reverse('book_repair'), dict(customer_name='Ama', customer_email='ama@example.com', customer_phone='0244000621',
                   device_category='laptop', manufacturer='Apple', device='MBP', issue_description='No power', logistics_preference='drop_off'))
        guest.post(reverse('request_part'), dict(customer_name='Yaw', customer_email='yaw@example.com', customer_phone='0244000622',
                   part_needed='Battery', device_model='A2338', condition_preference='new'))
        guest.post(reverse('submit_testimonial'), {'quote': 'Great', 'name': 'Rev', 'rating': '5'})
        guest.post(reverse('contact'), {'name': 'N', 'email': 'n@example.com', 'subject': 'Hi', 'message': 'x'})
        ticket = RepairTicket.objects.get(customer_name='Ama')
        self.cs.post(reverse('staff_create_repair_quote', args=[ticket.ticket_id]), {'quoted_price': '90', 'diagnostic_notes': 'n', 'estimated_turnaround': '1d', 'warranty_period': '90d'})
        guest.post(reverse('track_repair_lookup'), {'ticket_id': ticket.ticket_id, 'phone': '0244000621'})
        guest.post(reverse('track_repair', args=[ticket.ticket_id]), {'message': 'Question from the client'})
        guest.post(reverse('customer_approve_repair_quote', args=[ticket.ticket_id]))
        self.cs.post(reverse('staff_update_repair_status', args=[ticket.ticket_id]), {'status': 'completed'})
        subjects = self._support_subjects()
        self.assertEqual(len(subjects), 6, subjects)
        for subject in subjects:
            self.assertTrue(subject.startswith(self.ALLOWED), subject)
        for prefix in self.ALLOWED:
            self.assertEqual(len([s for s in subjects if s.startswith(prefix)]), 1, prefix)


    def test_a_status_update_note_stays_in_the_thread_and_sends_only_the_normal_status_email(self):
        from .models import RepairMessage
        t = RepairTicket.objects.create(customer_name='K', customer_email='k@example.com', customer_phone='0244000631', device='d', status='in_progress')
        mail.outbox.clear()
        self.cs.post(reverse('staff_update_repair_status', args=[t.ticket_id]), {'status': 'completed', 'status_note': 'Replaced the screen.'})
        self.assertEqual(len([m for m in mail.outbox if m.to == ['k@example.com']]), 1)
        self.assertEqual(self._support_subjects(), [])
        self.assertTrue(RepairMessage.objects.filter(ticket=t, message__contains='Replaced the screen.').exists())


class StaffChatAlwaysEmailsClientTests(TestCase):
    """Whatever staff type to a client (any wording, any emoji, any screen) is emailed and kept in the thread."""

    TEXTS = ['Your laptop is ready.', '✅ Your laptop is ready.', '🔧 Repair started.', '📦 Part arrived.',
             '❌ Sorry, not fixable.', '📋 Please review the quote.', '👋 Quick question for you.']

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.staff = User.objects.create_user('alwaysstaff', 'as@example.com', 'x', is_staff=True)
        self.admin = User.objects.create_superuser('alwaysadmin', 'aa@example.com', 'x')
        self.ticket = RepairTicket.objects.create(
            customer_name='Kofi', customer_email='kofi@example.com', customer_phone='0244000641', device='MBP', status='in_progress')
        self.part = PartRequest.objects.create(
            customer_name='Esi', customer_email='esi@example.com', customer_phone='0244000642',
            part_needed='Fan', device_model='Y', status='in_progress')

    def _to(self, addr):
        return [m for m in mail.outbox if m.to == [addr]]

    def test_chat_box_messages_with_or_without_an_emoji_all_email_the_client_and_stay_in_the_thread(self):
        from .models import RepairMessage, PartRequestMessage
        self.client.force_login(self.staff)
        for text in self.TEXTS:
            mail.outbox.clear()
            self.client.post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': text})
            self.assertEqual(len(self._to('kofi@example.com')), 1, text)
            self.assertTrue(RepairMessage.objects.filter(ticket=self.ticket, message=text, sender_is_admin=True).exists())
            mail.outbox.clear()
            self.client.post(reverse('track_part', args=[self.part.request_id]), {'message': text})
            self.assertEqual(len(self._to('esi@example.com')), 1, text)
            self.assertTrue(PartRequestMessage.objects.filter(part_request=self.part, message=text, sender_is_admin=True).exists())

    def test_messages_written_on_the_django_admin_screen_email_the_client_too(self):
        self.client.force_login(self.admin)
        for text in ('Plain admin message', '✅ Admin message starting with an emoji'):
            mail.outbox.clear()
            self.client.post(reverse('admin:repair_repairmessage_add'), {'ticket': self.ticket.pk, 'message': text, 'sender_is_admin': 'on'})
            self.assertEqual(len(self._to('kofi@example.com')), 1, text)
            mail.outbox.clear()
            self.client.post(reverse('admin:repair_partrequestmessage_add'), {'part_request': self.part.pk, 'message': text, 'sender_is_admin': 'on'})
            self.assertEqual(len(self._to('esi@example.com')), 1, text)

    def test_the_email_shows_the_staff_text_and_links_to_the_tracking_page(self):
        self.client.force_login(self.staff)
        mail.outbox.clear()
        self.client.post(reverse('track_repair', args=[self.ticket.ticket_id]), {'message': '✅ Ready for pickup after 2pm.'})
        sent = self._to('kofi@example.com')[0]
        self.assertIn('Ready for pickup after 2pm.', sent.alternatives[0][0])
        self.assertIn('/accounts/login/?next=/repair/track/', sent.alternatives[0][0])

    def test_automatic_system_notes_still_do_not_send_their_own_extra_email(self):
        self.client.force_login(self.staff)
        mail.outbox.clear()
        self.client.post(reverse('staff_create_repair_quote', args=[self.ticket.ticket_id]),
                         {'quoted_price': '90', 'diagnostic_notes': 'n', 'estimated_turnaround': '1d', 'warranty_period': '90d'})
        self.assertEqual(len(self._to('kofi@example.com')), 1)
        mail.outbox.clear()
        self.client.post(reverse('staff_update_repair_status', args=[self.ticket.ticket_id]), {'status': 'completed'})
        self.assertEqual(len(self._to('kofi@example.com')), 1)
