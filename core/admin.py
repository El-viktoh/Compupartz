from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import FAQ, Testimonial
from .utils import send_activation_email
from django.contrib import messages

# 1. FAQS
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('is_published',)


# 2. CLIENT TESTIMONIALS
@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_or_title', 'rating_stars', 'service_rendered', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('is_approved', 'is_featured', 'rating', 'created_at')
    search_fields = ('name', 'role_or_title', 'quote', 'service_rendered')
    list_editable = ('is_approved', 'is_featured')
    actions = ['approve_testimonials', 'feature_testimonials', 'unapprove_testimonials']

    def rating_stars(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)
    rating_stars.short_description = "Rating"

    @admin.action(description="Approve selected testimonials")
    def approve_testimonials(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f"{count} testimonial(s) approved for publication.", messages.SUCCESS)

    @admin.action(description="Unapprove selected testimonials")
    def unapprove_testimonials(self, request, queryset):
        count = queryset.update(is_approved=False)
        self.message_user(request, f"{count} testimonial(s) unapproved.", messages.WARNING)

    @admin.action(description="Feature selected testimonials on homepage")
    def feature_testimonials(self, request, queryset):
        count = queryset.update(is_featured=True, is_approved=True)
        self.message_user(request, f"{count} testimonial(s) featured on homepage.", messages.SUCCESS)

# 2. BETTER USER MANAGEMENT
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class CustomUserAdmin(BaseUserAdmin):
    # Differentiate users clearly in the list
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    
    actions = ['resend_activation_email', 'manually_verify_users']

    @admin.action(description="Resend Verification Email to selected users")
    def resend_activation_email(self, request, queryset):
        success_count = 0
        domain = request.get_host()
        
        for user in queryset:
            if not user.is_active:
                if send_activation_email(user, domain):
                    success_count += 1
        
        self.message_user(
            request, 
            f"Successfully resent activation emails to {success_count} user(s).",
            messages.SUCCESS
        )

    @admin.action(description="Manually Verify (Activate) selected users")
    def manually_verify_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(
            request, 
            f"Successfully activated {count} user(s).",
            messages.SUCCESS
        )

admin.site.register(User, CustomUserAdmin)
