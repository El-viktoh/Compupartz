import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def get_site_domain():
    return getattr(settings, 'SITE_DOMAIN', 'compupartz.com')


def send_repair_email(ticket):
    """Initial email sent when client books a repair."""
    try:
        domain = get_site_domain()
        tracking_url = f"https://{domain}/repair/track/{ticket.ticket_id}/" if not settings.DEBUG else f"http://127.0.0.1:8000/repair/track/{ticket.ticket_id}/"

        subject = f"[Compupartz] Repair Booking Intake Confirmed — Ticket #{ticket.ticket_id}"

        status_message = "Your repair booking has been registered on our intake bench. Our certified technicians are reviewing your fault telemetry and will initiate diagnostics shortly."

        context = {
            "ticket": ticket,
            "status_display": ticket.get_status_display(),
            "status_message": status_message,
            "tracking_url": tracking_url,
        }

        html_content = render_to_string("emails/repair_status_update.html", context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.customer_email],
            html_message=html_content,
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending booking confirmation email for {ticket.ticket_id}: {e}")
        return False


def send_repair_status_email(ticket, old_status, new_status):
    """Email sent to customer whenever technician updates repair status in admin."""
    if not ticket.customer_email:
        return False

    try:
        domain = get_site_domain()
        tracking_url = f"https://{domain}/repair/track/{ticket.ticket_id}/" if not settings.DEBUG else f"http://127.0.0.1:8000/repair/track/{ticket.ticket_id}/"

        status_display = ticket.get_status_display()
        if new_status == 'in_progress':
            subject = f"[Compupartz] Diagnostic Process & Bench Restoration Started — Ticket #{ticket.ticket_id}"
            status_message = (
                f"Great news! Your {ticket.device} has passed intake and our certified technicians are actively performing "
                f"diagnostic process & board-level component restoration on the lab bench."
            )
        elif new_status == 'completed':
            subject = f"[Compupartz] Restoration Complete & Ready for Collection — Ticket #{ticket.ticket_id}"
            status_message = (
                f"All bench repairs and 4-stage quality stress tests are complete! Your {ticket.device} has been verified, "
                f"packaged with your 90-day Compupartz warranty seal, and is now ready for pickup or dispatch."
            )
        else:
            subject = f"[Compupartz] Repair Ticket Status Updated — Ticket #{ticket.ticket_id}"
            status_message = f"The status of your repair ticket #{ticket.ticket_id} has been updated to: {status_display}."

        context = {
            "ticket": ticket,
            "status_display": status_display,
            "status_message": status_message,
            "tracking_url": tracking_url,
        }

        html_content = render_to_string("emails/repair_status_update.html", context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.customer_email],
            html_message=html_content,
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending repair status email for {ticket.ticket_id}: {e}")
        return False


def send_technician_message_email(message):
    """Email sent to customer when a lab technician replies/messages on their ticket."""
    ticket = message.ticket
    if not ticket.customer_email:
        return False

    try:
        domain = get_site_domain()
        tracking_url = f"https://{domain}/repair/track/{ticket.ticket_id}/" if not settings.DEBUG else f"http://127.0.0.1:8000/repair/track/{ticket.ticket_id}/"

        subject = f"[Compupartz] Lab Bench Update on Ticket #{ticket.ticket_id}"

        context = {
            "ticket": ticket,
            "message_text": message.message,
            "tracking_url": tracking_url,
        }

        html_content = render_to_string("emails/technician_message.html", context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.customer_email],
            html_message=html_content,
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending technician message email for {ticket.ticket_id}: {e}")
        return False


def send_part_request_email(part_request):
    """Initial email sent when client submits a part request."""
    if not part_request.customer_email:
        return False

    try:
        domain = get_site_domain()
        dashboard_url = f"https://{domain}/dashboard/?tab=parts" if not settings.DEBUG else "http://127.0.0.1:8000/dashboard/?tab=parts"

        subject = f"[Compupartz] Part Request Intake Confirmed — #{part_request.request_id}"
        status_message = "Your hardware part sourcing request has been received. Our parts desk is contacting verified OEM distributors to verify component availability and compute your quote."

        context = {
            "part_request": part_request,
            "status_display": part_request.get_status_display(),
            "status_message": status_message,
            "dashboard_url": dashboard_url,
        }

        html_content = render_to_string("emails/part_request_status_update.html", context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[part_request.customer_email],
            html_message=html_content,
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending part request email for {part_request.request_id}: {e}")
        return False


def send_part_request_status_email(part_request, old_status, new_status):
    """Email sent to customer whenever technician updates a part request status or quotes a price."""
    if not part_request.customer_email:
        return False

    try:
        domain = get_site_domain()
        dashboard_url = f"https://{domain}/dashboard/?tab=parts" if not settings.DEBUG else "http://127.0.0.1:8000/dashboard/?tab=parts"

        status_display = part_request.get_status_display()
        if new_status == 'quoted':
            subject = f"[Compupartz] Quote Available for Part Request #{part_request.request_id}"
            status_message = (
                f"We have located the component you requested ({part_request.part_needed} for {part_request.device_model}). "
                f"Our technicians have generated a formal price quote. Review details below to confirm your order."
            )
        elif new_status == 'fulfilled':
            subject = f"[Compupartz] Hardware Part Procured & Ready — #{part_request.request_id}"
            status_message = (
                f"Your requested hardware part ({part_request.part_needed}) has arrived at our lab and is tested and ready for collection or courier dispatch!"
            )
        elif new_status == 'declined':
            subject = f"[Compupartz] Sourcing Notice on Part Request #{part_request.request_id}"
            status_message = (
                f"Our technicians investigated distributor channels for {part_request.part_needed} ({part_request.device_model}). "
                f"Unfortunately, this component is currently discontinued or unverified for OEM quality standards."
            )
        else:
            subject = f"[Compupartz] Part Request Status Updated — #{part_request.request_id}"
            status_message = f"The status of your hardware request #{part_request.request_id} is now: {status_display}."

        context = {
            "part_request": part_request,
            "status_display": status_display,
            "status_message": status_message,
            "dashboard_url": dashboard_url,
        }

        html_content = render_to_string("emails/part_request_status_update.html", context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[part_request.customer_email],
            html_message=html_content,
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending part request status email for {part_request.request_id}: {e}")
        return False
