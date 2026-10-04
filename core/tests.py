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
