from django.test import TestCase, Client
from django.core import mail
from django.urls import reverse
from django.contrib.auth.models import User

from repair.models import RepairTicket, PartRequest
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

