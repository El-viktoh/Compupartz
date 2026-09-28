from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# ✅ SIGNALS
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Frequently Asked Question"
        verbose_name_plural = "Frequently Asked Questions"
        ordering = ['-created_at']

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    RATING_CHOICES = [
        (5, '5 Stars (★★★★★)'),
        (4, '4 Stars (★★★★☆)'),
        (3, '3 Stars (★★★☆☆)'),
        (2, '2 Stars (★★☆☆☆)'),
        (1, '1 Star (★☆☆☆☆)'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='testimonials')
    name = models.CharField(max_length=150, help_text="Client Name")
    role_or_title = models.CharField(max_length=150, blank=True, help_text="e.g. Software Engineer, TechLab")
    quote = models.TextField(help_text="Client testimonial quote")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    avatar = models.ImageField(upload_to='testimonials/', null=True, blank=True)
    service_rendered = models.CharField(max_length=150, blank=True, help_text="e.g. MacBook Logic Board Repair, OEM Screen")
    is_approved = models.BooleanField(default=True, help_text="Approve to display on website")
    is_featured = models.BooleanField(default=True, help_text="Feature on homepage carousel")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client Testimonial"
        verbose_name_plural = "Client Testimonials"
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.rating}★)"
