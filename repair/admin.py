from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import RepairTicket, RepairMessage, PartRequest


# ==========================================
# 1. DIRECT TECHNICIAN COMMUNICATION INLINE
# ==========================================
class RepairMessageInline(admin.TabularInline):
    model = RepairMessage
    extra = 1
    fields = ('sender_is_admin', 'message', 'created_at')
    readonly_fields = ('created_at',)
    verbose_name = "Direct Technician Message / Bench Note"
    verbose_name_plural = "Direct Technician Communication Thread"


# ==========================================
# 2. REPAIR TICKET ADMIN
# ==========================================
@admin.register(RepairTicket)
class RepairTicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_id',
        'customer_name',
        'customer_phone',
        'device',
        'device_category',
        'logistics_preference',
        'status_badge',
        'created_at',
    )
    list_filter = ('status', 'device_category', 'logistics_preference', 'created_at')
    search_fields = (
        'ticket_id',
        'customer_name',
        'customer_email',
        'customer_phone',
        'device',
        'issue_description',
    )
    list_editable = ()
    readonly_fields = ('ticket_id', 'created_at')
    inlines = [RepairMessageInline]
    actions = ['mark_in_progress', 'mark_completed']

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'in_progress': '#ff7200',
            'completed': '#10b981',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 999px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, RepairMessage) and not instance.pk:
                # Automatic flag as sent by lab technician when entered from admin
                instance.sender_is_admin = True
            instance.save()
        formset.save_m2m()

    @admin.action(description="Mark selected tickets as In Progress (Diagnostic / Restoration)")
    def mark_in_progress(self, request, queryset):
        for ticket in queryset:
            ticket.status = 'in_progress'
            ticket.save()
        self.message_user(
            request,
            f"{queryset.count()} ticket(s) set to In Progress. Customer email notifications sent.",
            messages.SUCCESS
        )

    @admin.action(description="Mark selected tickets as Completed (Ready for Collection)")
    def mark_completed(self, request, queryset):
        for ticket in queryset:
            ticket.status = 'completed'
            ticket.save()
        self.message_user(
            request,
            f"{queryset.count()} ticket(s) marked Completed. Customer email notifications sent.",
            messages.SUCCESS
        )


# ==========================================
# 3. DIRECT TECHNICIAN COMMUNICATIONS ADMIN
# ==========================================
@admin.register(RepairMessage)
class RepairMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket_link', 'sender_role', 'message_snippet', 'created_at')
    list_filter = ('sender_is_admin', 'created_at', 'ticket__status')
    search_fields = ('ticket__ticket_id', 'ticket__customer_name', 'ticket__customer_phone', 'message')
    readonly_fields = ('created_at',)

    def ticket_link(self, obj):
        return format_html(
            '<a href="/admin/repair/repairticket/{}/change/"><strong>{}</strong> ({} - {})</a>',
            obj.ticket.id,
            obj.ticket.ticket_id,
            obj.ticket.customer_name,
            obj.ticket.device
        )
    ticket_link.short_description = "Repair Ticket"

    def sender_role(self, obj):
        if obj.sender_is_admin:
            return format_html(
                '<span style="background-color: #008BC6; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Lab Technician</span>'
            )
        return format_html(
            '<span style="background-color: #64748b; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Client</span>'
        )
    sender_role.short_description = "Sender"

    def message_snippet(self, obj):
        return (obj.message[:80] + '...') if len(obj.message) > 80 else obj.message
    message_snippet.short_description = "Note Content"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.sender_is_admin = True
        super().save_model(request, obj, form, change)


# ==========================================
# 4. PART REQUEST SOURCING ADMIN
# ==========================================
@admin.register(PartRequest)
class PartRequestAdmin(admin.ModelAdmin):
    list_display = (
        'request_id',
        'customer_name',
        'customer_phone',
        'part_needed',
        'device_model',
        'condition_preference',
        'status_badge',
        'quoted_price',
        'created_at',
    )
    list_filter = ('status', 'condition_preference', 'created_at')
    search_fields = (
        'request_id',
        'customer_name',
        'customer_phone',
        'customer_email',
        'part_needed',
        'device_model',
    )
    readonly_fields = ('request_id', 'created_at')
    actions = ['mark_quoted', 'mark_fulfilled', 'mark_declined']

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'quoted': '#008BC6',
            'fulfilled': '#10b981',
            'declined': '#ef4444',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 999px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    @admin.action(description="Mark selected requests as Quoted")
    def mark_quoted(self, request, queryset):
        for req in queryset:
            req.status = 'quoted'
            req.save()
        self.message_user(
            request,
            f"{queryset.count()} part request(s) set to Quoted. Customer email notifications sent.",
            messages.SUCCESS
        )

    @admin.action(description="Mark selected requests as Fulfilled (Ready)")
    def mark_fulfilled(self, request, queryset):
        for req in queryset:
            req.status = 'fulfilled'
            req.save()
        self.message_user(
            request,
            f"{queryset.count()} part request(s) set to Fulfilled. Customer email notifications sent.",
            messages.SUCCESS
        )

    @admin.action(description="Mark selected requests as Declined / Unavailable")
    def mark_declined(self, request, queryset):
        for req in queryset:
            req.status = 'declined'
            req.save()
        self.message_user(
            request,
            f"{queryset.count()} part request(s) set to Declined. Customer email notifications sent.",
            messages.WARNING
        )
