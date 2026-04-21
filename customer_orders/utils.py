from django.core.mail import send_mail
from django.conf import settings


def send_order_email(order):
    subject = f"Compupartz Order #{order.id}"

    items_str = ""
    for item in order.items.all():
        var_info = f" ({item.variations_display})" if item.variations_display else ""
        items_str += f"- {item.product_name}{var_info} x {item.quantity} (GHS {item.price})\n"

    message = f"""
Hello {order.name},

Thank you for your order at Compupartz.

Order ID: {order.id}
Total: GHS {order.total_amount}
Status: {order.status}

Items:
{items_str}

We will notify you as your order progresses.

Thank you for choosing Compupartz.
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        fail_silently=False,
    )
