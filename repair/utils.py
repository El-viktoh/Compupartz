from django.core.mail import send_mail
from django.conf import settings


def send_repair_email(ticket):
    subject = f"Repair Booking Received — Ticket #{ticket.id}"

    message = f"""
    Hello {ticket.customer_name},

    Thank you for booking a repair with Compupartz.

    Here are your booking details:

    Ticket ID: {ticket.id}
    Device: {ticket.device}
    Phone: {ticket.customer_phone}
    Email: {ticket.customer_email}
    Service Type: {'In-Person' if ticket.in_person else 'Remote / Pickup'}

    Issue Description:
    {ticket.issue_description}

    Our team will contact you shortly.

    Best regards,
    Compupartz Team
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [ticket.customer_email],
        fail_silently=False,
    )
