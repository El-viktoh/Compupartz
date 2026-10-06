import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def get_site_domain():
    return getattr(settings, 'SITE_DOMAIN', 'compupartz.com')


def get_base_url():
    domain = get_site_domain()
    return "http://127.0.0.1:8000" if settings.DEBUG else f"https://{domain}"


def get_support_email():
    return getattr(settings, 'SUPPORT_EMAIL', getattr(settings, 'SERVER_EMAIL', 'support@compupartz.com'))


def format_whatsapp_phone(phone_str):
    if not phone_str:
        return ""
    digits = "".join(ch for ch in str(phone_str) if ch.isdigit())
    if digits.startswith("0") and len(digits) == 10:
        return "233" + digits[1:]
    return digits


def send_admin_repair_notification(ticket):
    """
    Dispatches a staff notification to support@compupartz.com 
    when a new repair ticket intake form is submitted.
    """
    try:
        support_email = get_support_email()
        base_url = get_base_url()
        admin_url = f"{base_url}/admin/repair/repairticket/{ticket.id}/change/"
        
        clean_phone = format_whatsapp_phone(ticket.customer_phone)
        whatsapp_url = f"https://wa.me/{clean_phone}" if clean_phone else ""

        subject = f"[New Repair Ticket] #{ticket.ticket_id} — {ticket.customer_name} ({ticket.device})"

        context = {
            "notification_type": "repair_ticket",
            "ticket": ticket,
            "admin_url": admin_url,
            "whatsapp_url": whatsapp_url,
            "domain": get_site_domain(),
        }

        html_content = render_to_string("emails/admin_notification.html", context)

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[support_email],
            reply_to=[ticket.customer_email] if ticket.customer_email else [],
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)
        logger.info(f"Staff notification email dispatched for new Repair Ticket #{ticket.ticket_id} to {support_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending staff repair notification for #{getattr(ticket, 'ticket_id', 'unknown')}: {e}")
        return False


def send_admin_part_request_notification(part_request):
    """
    Dispatches a staff notification to support@compupartz.com 
    when a new parts sourcing request is submitted.
    """
    try:
        support_email = get_support_email()
        base_url = get_base_url()
        admin_url = f"{base_url}/admin/repair/partrequest/{part_request.id}/change/"
        
        clean_phone = format_whatsapp_phone(part_request.customer_phone)
        whatsapp_url = f"https://wa.me/{clean_phone}" if clean_phone else ""

        subject = f"[New Part Request] #{part_request.request_id} — {part_request.customer_name} ({part_request.part_needed})"

        context = {
            "notification_type": "part_request",
            "part_request": part_request,
            "admin_url": admin_url,
            "whatsapp_url": whatsapp_url,
            "domain": get_site_domain(),
        }

        html_content = render_to_string("emails/admin_notification.html", context)

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[support_email],
            reply_to=[part_request.customer_email] if part_request.customer_email else [],
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)
        logger.info(f"Staff notification email dispatched for new Part Request #{part_request.request_id} to {support_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending staff part request notification for #{getattr(part_request, 'request_id', 'unknown')}: {e}")
        return False


def send_admin_testimonial_notification(testimonial):
    """
    Dispatches a staff notification to support@compupartz.com 
    when a new client testimonial review is submitted.
    """
    try:
        support_email = get_support_email()
        base_url = get_base_url()
        admin_url = f"{base_url}/admin/core/testimonial/{testimonial.id}/change/"
        
        subject = f"[New Review] {testimonial.rating}★ from {testimonial.name} — {testimonial.service_rendered or 'Compupartz'}"

        reply_to = []
        if testimonial.user and testimonial.user.email:
            reply_to.append(testimonial.user.email)

        context = {
            "notification_type": "testimonial",
            "testimonial": testimonial,
            "admin_url": admin_url,
            "domain": get_site_domain(),
        }

        html_content = render_to_string("emails/admin_notification.html", context)

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[support_email],
            reply_to=reply_to,
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)
        logger.info(f"Staff notification email dispatched for new Testimonial from {testimonial.name} to {support_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending staff testimonial notification for {getattr(testimonial, 'id', 'unknown')}: {e}")
        return False


def build_quote_approved_context(item):
    """One normalized set of fields so repair and part approvals render through the identical layout."""
    from django.utils.text import Truncator

    is_repair = hasattr(item, "ticket_id")
    if is_repair:
        specifics = {
            "kind": "Repair",
            "service_type": "Device Repair",
            "reference": item.ticket_id,
            "card_label": "Approved Repair",
            "card_title": item.device,
            "device_target": " ".join(filter(None, [item.manufacturer, item.get_device_category_display()])),
            "work_requested": Truncator(item.issue_description or "").chars(120),
            "device_model": item.device,
            "extra_label": "Drop-off Method",
            "extra_value": item.get_logistics_preference_display(),
            "timing_label": "Turnaround",
            "timing_value": item.estimated_turnaround,
            "approval_sentence": "The client has authorized this repair from their tracking page.",
            "record_noun": "ticket",
            "next_action": "bench work can begin",
            "admin_path": "repairticket",
        }
    else:
        specifics = {
            "kind": "Part",
            "service_type": "Part Sourcing",
            "reference": item.request_id,
            "card_label": "Approved Component",
            "card_title": item.part_needed,
            "device_target": item.device_model,
            "work_requested": item.part_needed,
            "device_model": item.device_model,
            "extra_label": "Condition",
            "extra_value": item.get_condition_preference_display(),
            "timing_label": "Estimated Delivery",
            "timing_value": item.estimated_delivery,
            "approval_sentence": "The client has confirmed this quote from their tracking page.",
            "record_noun": "request",
            "next_action": "procurement can begin",
            "admin_path": "partrequest",
        }
    return {"notification_type": "quote_approved", "quote_item": item, "is_repair": is_repair, **specifics}


def send_admin_quote_approved_notification(item):
    """Alert support when a CLIENT approves a repair or part quote."""
    try:
        ctx = build_quote_approved_context(item)
        support_email = get_support_email()
        clean_phone = format_whatsapp_phone(item.customer_phone)
        ctx.update({
            "admin_url": f"{get_base_url()}/admin/repair/{ctx['admin_path']}/{item.id}/change/",
            "whatsapp_url": f"https://wa.me/{clean_phone}" if clean_phone else "",
            "domain": get_site_domain(),
        })
        email = EmailMessage(
            subject=f"[Quote Approved] #{ctx['reference']} — {item.customer_name} (GH\u20b5 {item.quoted_price})",
            body=render_to_string("emails/admin_notification.html", ctx),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[support_email],
            reply_to=[item.customer_email] if item.customer_email else [],
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)
        logger.info(f"Quote-approved alert dispatched for #{ctx['reference']} to {support_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending quote-approved alert for {getattr(item, 'pk', 'unknown')}: {e}")
        return False
