from django.core.mail import send_mail
from django.conf import settings


def send_repair_email(ticket):
    subject = f"Repair Booking Received — Ticket #{ticket.ticket_id}"

    message = f"""
    Hello {ticket.customer_name},

    Thank you for booking a repair with Compupartz.

    Here are your booking details:

    Ticket ID: {ticket.ticket_id}
    Device: {ticket.device}
    Phone: {ticket.customer_phone}
    Email: {ticket.customer_email}
    Service Type: {ticket.get_logistics_preference_display()}

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


def send_part_request_email(part_request):
    if not part_request.customer_email:
        return

    subject = f"Part Request Received — {part_request.request_id}"

    message = f"""
    Hello {part_request.customer_name},

    Thanks for your part request with Compupartz.

    Request ID: {part_request.request_id}
    Part Needed: {part_request.part_needed}
    Device / Model: {part_request.device_model}
    Condition Preference: {part_request.get_condition_preference_display()}
    Phone: {part_request.customer_phone}

    Our team will source it and get back to you with a quote shortly.

    Best regards,
    Compupartz Team
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [part_request.customer_email],
        fail_silently=False,
    )
