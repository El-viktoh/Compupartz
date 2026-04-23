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
