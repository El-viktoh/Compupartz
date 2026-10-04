from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from blog.models import Post, Category
from blog.templatetags.blog_extras import render_markdown

class BlogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(username='tech_author', password='password123')
        self.category = Category.objects.create(name='Micro-Soldering', slug='micro-soldering')
        
        self.published_post = Post.objects.create(
            title='Thermal Camera Diagnostic Protocol',
            slug='thermal-camera-diagnostic-protocol',
            author=self.author,
            category=self.category,
            content='### Thermal Isolation\nInspecting the 12V bus with infrared sensors.\n- **Probe 1**: 0.4V\n- **Probe 2**: 12.6V\n\nShort identified at C7050.',
            excerpt='Inspecting logic board power rails with infrared thermal imaging.',
            status='published'
        )

        self.draft_post = Post.objects.create(
            title='Internal Unreleased Teardown',
            slug='internal-unreleased-teardown',
            author=self.author,
            category=self.category,
            content='Draft content not ready for public release.',
            excerpt='Internal draft.',
            status='draft'
        )

    def test_post_list_shows_only_published_posts(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thermal Camera Diagnostic Protocol')
        self.assertNotContains(response, 'Internal Unreleased Teardown')

    def test_post_detail_renders_published_post(self):
        response = self.client.get(reverse('blog:post_detail', kwargs={'slug': self.published_post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thermal Camera Diagnostic Protocol')
        self.assertContains(response, 'Micro-Soldering')

    def test_post_detail_returns_404_for_draft_post(self):
        response = self.client.get(reverse('blog:post_detail', kwargs={'slug': self.draft_post.slug}))
        self.assertEqual(response.status_code, 404)

    def test_render_markdown_filter_converts_syntax_to_html(self):
        sample = (
            "### Section Title\n"
            "This is a paragraph with **critical bold text**.\n\n"
            "- **Item 1**: First test\n"
            "- **Item 2**: Second test\n\n"
            "1. Step one\n"
            "2. Step two"
        )
        rendered = render_markdown(sample)
        self.assertIn('<h3', rendered)
        self.assertIn('Section Title', rendered)
        self.assertIn('<strong class="font-semibold text-slate-900 dark:text-white">critical bold text</strong>', rendered)
        self.assertIn('<ul class="list-disc', rendered)
        self.assertIn('<ol class="list-decimal', rendered)
