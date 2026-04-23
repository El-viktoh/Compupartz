from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import FAQ
from .utils import send_activation_email
from django.contrib import messages

# 1. FAQS
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('is_published',)

# 2. BETTER USER MANAGEMENT
admin.site.unregister(User)

@admin.register(User)
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
