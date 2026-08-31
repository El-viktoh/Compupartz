from django.contrib import admin
from .models import RepairTicket, RepairMessage, PartRequest

class RepairMessageInline(admin.TabularInline):
    model = RepairMessage
    extra = 1

@admin.register(RepairTicket)
class RepairTicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_id',
        'customer_name',
        'device',
        'status',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('ticket_id', 'customer_name', 'customer_email')
    inlines = [RepairMessageInline]


@admin.register(PartRequest)
class PartRequestAdmin(admin.ModelAdmin):
    list_display = (
        'request_id',
        'customer_name',
        'part_needed',
        'device_model',
        'status',
        'created_at',
    )
    list_filter = ('status', 'condition_preference', 'created_at')
    search_fields = ('request_id', 'customer_name', 'customer_phone', 'part_needed')
