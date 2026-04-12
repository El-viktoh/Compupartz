from django.contrib import admin
from .models import RepairTicket

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

