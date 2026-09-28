from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'variations_display', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id_display',
        'name',
        'phone',
        'email',
        'total_amount_display',
        'status_badge',
        'payment_status_badge',
        'created_at',
    )
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('id', 'name', 'phone', 'email', 'address')
    list_editable = ()
    readonly_fields = ('created_at', 'paid_at')
    inlines = [OrderItemInline]
    actions = ['mark_processing', 'mark_ready', 'mark_completed']

    def order_id_display(self, obj):
        return f"Order #{obj.id}"
    order_id_display.short_description = "Order"

    def total_amount_display(self, obj):
        return f"GH₵ {obj.total_amount}"
    total_amount_display.short_description = "Total"

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'processing': '#ff7200',
            'ready': '#008BC6',
            'completed': '#10b981',
            'cancelled': '#ef4444',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 999px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def payment_status_badge(self, obj):
        colors = {
            'paid': '#10b981',
            'pending': '#f59e0b',
            'unpaid': '#64748b',
            'failed': '#ef4444',
        }
        color = colors.get(obj.payment_status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 6px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = "Payment"

    @admin.action(description="Mark selected orders as Processing")
    def mark_processing(self, request, queryset):
        for o in queryset:
            o.status = 'processing'
            o.save()
        self.message_user(request, f"{queryset.count()} order(s) marked Processing. Client emails dispatched.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as Ready for Pickup / Dispatch")
    def mark_ready(self, request, queryset):
        for o in queryset:
            o.status = 'ready'
            o.save()
        self.message_user(request, f"{queryset.count()} order(s) marked Ready. Client emails dispatched.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as Completed")
    def mark_completed(self, request, queryset):
        for o in queryset:
            o.status = 'completed'
            o.save()
        self.message_user(request, f"{queryset.count()} order(s) marked Completed. Client emails dispatched.", messages.SUCCESS)
