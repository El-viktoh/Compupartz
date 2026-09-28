from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site


def send_order_email(order, request=None):
    # Determine domain for the tracking link
    domain = ""
    if request:
        domain = request.get_host()
    else:
        # Fallback if no request (e.g. background task)
        domain = "compupartz.com"

    subject = f"Compupartz Order #{order.id}"
    
    # Render HTML content
    html_content = render_to_string("customer_orders/order_email.html", {
        "order": order,
        "domain": domain,
    })

    # Render fallback text content
    items_str = ""
    for item in order.items.all():
        var_info = f" ({item.variations_display})" if item.variations_display else ""
        items_str += f"- {item.product_name}{var_info} x {item.quantity} (GHS {item.price})\n"

    text_content = f"Thank you for your order, {order.name}!\n\nTracking ID: #{order.id}\nTotal: GHS {order.total_amount}\n\nItems:\n{items_str}\n\nTrack here: http://{domain}/order/track/{order.id}/"

    email = EmailMessage(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
    )
    email.content_subtype = "html"
    email.body = html_content
    email.send(fail_silently=False)


def send_order_status_email(order, old_status, new_status):
    """Email notification sent to customer whenever admin updates order status."""
    if not order.email:
        return False
    try:
        from django.utils.html import strip_tags
        import logging
        domain = "compupartz.com" if not settings.DEBUG else "127.0.0.1:8000"
        dashboard_url = f"https://{domain}/dashboard/?tab=parts" if not settings.DEBUG else "http://127.0.0.1:8000/dashboard/?tab=parts"

        status_display = order.get_status_display()
        if new_status == 'processing':
            status_message = "Your hardware order is currently being prepared and components are being verified on the test bench."
        elif new_status == 'ready':
            status_message = "Your order is packaged, quality-verified, and ready for pickup or dispatch via courier!"
        elif new_status == 'completed':
            status_message = "Your order has been fulfilled. Thank you for choosing Compupartz!"
        elif new_status == 'cancelled':
            status_message = "Your order has been marked as cancelled. If this is an error, please reach out to our team."
        else:
            status_message = f"Your order status has been updated to: {status_display}."

        subject = f"[Compupartz] Order #{order.id} Status: {status_display}"
        context = {
            "order": order,
            "status_display": status_display,
            "status_message": status_message,
            "dashboard_url": dashboard_url,
        }
        html_content = render_to_string("emails/order_status_update.html", context)

        email = EmailMessage(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error sending order status email for Order #{order.id}: {e}")
        return False
