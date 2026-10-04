from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.utils import timezone
from .models import RepairTicket, RepairMessage, PartRequest
from .utils import send_formal_repair_quote_email, send_formal_part_quote_email


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
        'status_badge',
        'quote_badge',
        'quoted_price_display',
        'created_at',
    )
    list_filter = ('status', 'quote_status', 'device_category', 'logistics_preference', 'created_at')
    search_fields = (
        'ticket_id',
        'customer_name',
        'customer_email',
        'customer_phone',
        'device',
        'issue_description',
        'diagnostic_notes',
    )
    readonly_fields = ('ticket_id', 'created_at', 'quote_sent_at')
    inlines = [RepairMessageInline]
    actions = [
        'mark_pending',
        'mark_in_progress',
        'mark_completed',
        'mark_no_fix',
        'send_formal_quote',
    ]

    fieldsets = (
        ("Client Identification", {
            "fields": ("user", "customer_name", "customer_email", "customer_phone")
        }),
        ("Hardware Intake & Diagnostics", {
            "fields": (
                "device_category",
                "manufacturer",
                "device",
                "issue_description",
                "diagnostic_image",
                "logistics_preference",
                "status",
            )
        }),
        ("🎯 Formal Repair Quotation Desk (Staff Only)", {
            "description": "Set diagnostic findings and repair pricing. Dispatches a formal quote email with approval buttons to the client.",
            "fields": (
                "quoted_price",
                "diagnostic_notes",
                "estimated_turnaround",
                "warranty_period",
                "quote_status",
                "quote_sent_at",
            )
        }),
        ("System Audit", {
            "classes": ("collapse",),
            "fields": ("ticket_id", "created_at")
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'quoted': '#008BC6',
            'in_progress': '#ff7200',
            'completed': '#10b981',
            'no_fix': '#ef4444',
            'cancelled': '#ef4444',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 999px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Repair Status"

    def quote_badge(self, obj):
        if obj.quote_status == 'sent':
            return mark_safe(
                '<span style="background-color: #008BC6; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Quote Sent</span>'
            )
        elif obj.quote_status == 'approved':
            return mark_safe(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Client Approved ✓</span>'
            )
        elif obj.quote_status == 'declined':
            return mark_safe(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Declined ✗</span>'
            )
        elif obj.quoted_price:
            return mark_safe(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Draft Quote</span>'
            )
        return mark_safe(
            '<span style="color: #94a3b8; font-size: 11px;">No Quote</span>'
        )
    quote_badge.short_description = "Quote Status"


    def quoted_price_display(self, obj):
        if obj.quoted_price:
            return format_html('<strong>GH₵ {}</strong>', obj.quoted_price)
        return "—"
    quoted_price_display.short_description = "Quoted (GH₵)"

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, RepairMessage) and not instance.pk:
                instance.sender_is_admin = True
            instance.save()
        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        # Automatically mark quote as sent and dispatch email when admin sets a quoted price & changes status
        if obj.quoted_price and (obj.status == 'quoted' or obj.quote_status == 'sent'):
            if obj.quote_status != 'approved':
                obj.quote_status = 'sent'
            if not obj.quote_sent_at or 'quoted_price' in form.changed_data:
                obj.quote_sent_at = timezone.now()
                send_formal_repair_quote_email(obj)
                # Auto record on communication thread
                RepairMessage.objects.create(
                    ticket=obj,
                    sender_is_admin=True,
                    message=f"📋 Formal Repair Quotation Dispatched: GH₵ {obj.quoted_price}. Diagnostic Scope: {obj.diagnostic_notes or 'Bench hardware restoration'}. Estimated Turnaround: {obj.estimated_turnaround}. Warranty: {obj.warranty_period}."
                )
        super().save_model(request, obj, form, change)

    @admin.action(description="🎯 Send / Resend Formal Quote Email to Selected Tickets")
    def send_formal_quote(self, request, queryset):
        count = 0
        for ticket in queryset:
            if ticket.quoted_price:
                ticket.status = 'quoted'
                ticket.quote_status = 'sent'
                ticket.quote_sent_at = timezone.now()
                ticket.save()
                send_formal_repair_quote_email(ticket)
                RepairMessage.objects.create(
                    ticket=ticket,
                    sender_is_admin=True,
                    message=f"📋 Formal Repair Quotation Dispatched: GH₵ {ticket.quoted_price}. Turnaround: {ticket.estimated_turnaround}. Warranty: {ticket.warranty_period}."
                )
                count += 1
        if count:
            self.message_user(
                request,
                f"Formal repair quote emails sent for {count} ticket(s).",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "Please set a Quoted Price on the selected ticket(s) before sending quotes.",
                messages.WARNING
            )

    @admin.action(description="Mark selected tickets as Pending Intake")
    def mark_pending(self, request, queryset):
        for ticket in queryset:
            ticket.status = 'pending'
            ticket.save()
        self.message_user(
            request,
            f"{queryset.count()} ticket(s) set to Pending Intake. Customer notifications dispatched.",
            messages.SUCCESS
        )

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

    @admin.action(description="Mark selected tickets as No-Fix")
    def mark_no_fix(self, request, queryset):
        for ticket in queryset:
            ticket.status = 'no_fix'
            ticket.save()
        self.message_user(
            request,
            f"{queryset.count()} ticket(s) marked No-Fix. Customer notifications dispatched.",
            messages.WARNING
        )
    mark_cancelled = mark_no_fix


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
            return mark_safe(
                '<span style="background-color: #008BC6; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Lab Technician</span>'
            )
        return mark_safe(
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
        'status_badge',
        'quote_badge',
        'quoted_price_display',
        'created_at',
    )
    list_filter = ('status', 'quote_status', 'condition_preference', 'created_at')
    search_fields = (
        'request_id',
        'customer_name',
        'customer_phone',
        'customer_email',
        'part_needed',
        'device_model',
        'admin_notes',
    )
    readonly_fields = ('request_id', 'created_at', 'quote_sent_at')
    actions = [
        'mark_pending',
        'mark_fulfilled',
        'mark_declined',
        'send_formal_part_quote',
    ]

    fieldsets = (
        ("Client Identification", {
            "fields": ("user", "customer_name", "customer_phone", "customer_email")
        }),
        ("Hardware Component Requested", {
            "fields": (
                "part_needed",
                "device_model",
                "condition_preference",
                "additional_details",
                "status",
            )
        }),
        ("🎯 Formal Hardware Sourcing Quote Desk (Staff Only)", {
            "description": "Set component price and availability notes. Dispatches a formal price quote email to the client.",
            "fields": (
                "quoted_price",
                "admin_notes",
                "estimated_delivery",
                "warranty_period",
                "quote_status",
                "quote_sent_at",
            )
        }),
        ("System Audit", {
            "classes": ("collapse",),
            "fields": ("request_id", "created_at")
        }),
    )

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
    status_badge.short_description = "Request Status"

    def quote_badge(self, obj):
        if obj.quote_status == 'sent':
            return mark_safe(
                '<span style="background-color: #008BC6; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Quote Sent</span>'
            )
        elif obj.quote_status == 'approved':
            return mark_safe(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Client Approved ✓</span>'
            )
        elif obj.quote_status == 'declined':
            return mark_safe(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Declined ✗</span>'
            )
        elif obj.quoted_price:
            return mark_safe(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">Draft Quote</span>'
            )
        return mark_safe(
            '<span style="color: #94a3b8; font-size: 11px;">No Quote</span>'
        )
    quote_badge.short_description = "Quote Status"


    def quoted_price_display(self, obj):
        if obj.quoted_price:
            return format_html('<strong>GH₵ {}</strong>', obj.quoted_price)
        return "—"
    quoted_price_display.short_description = "Quoted (GH₵)"

    def save_model(self, request, obj, form, change):
        if obj.quoted_price and (obj.status == 'quoted' or obj.quote_status == 'sent'):
            if obj.quote_status != 'approved':
                obj.quote_status = 'sent'
            if not obj.quote_sent_at or 'quoted_price' in form.changed_data:
                obj.quote_sent_at = timezone.now()
                send_formal_part_quote_email(obj)
        super().save_model(request, obj, form, change)

    @admin.action(description="🎯 Send / Resend Formal Quote Email to Selected Part Requests")
    def send_formal_part_quote(self, request, queryset):
        count = 0
        for req in queryset:
            if req.quoted_price:
                req.status = 'quoted'
                req.quote_status = 'sent'
                req.quote_sent_at = timezone.now()
                req.save()
                send_formal_part_quote_email(req)
                count += 1
        if count:
            self.message_user(
                request,
                f"Formal part quotes sent for {count} request(s).",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "Please enter a Quoted Price on the selected request(s) before sending quotes.",
                messages.WARNING
            )

    @admin.action(description="Mark selected requests as Pending Intake")
    def mark_pending(self, request, queryset):
        for req in queryset:
            req.status = 'pending'
            req.save()
        self.message_user(
            request,
            f"{queryset.count()} part request(s) set to Pending Intake. Customer notifications dispatched.",
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

