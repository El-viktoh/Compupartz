import logging
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver
from .models import RepairTicket, PartRequest, RepairMessage
from .utils import (
    send_repair_status_email,
    send_part_request_status_email,
    send_technician_message_email,
)

logger = logging.getLogger(__name__)


# ==========================================
# REPAIR TICKET STATUS TRACKING
# ==========================================
@receiver(post_init, sender=RepairTicket)
def track_repair_ticket_original_status(sender, instance, **kwargs):
    instance._original_status = instance.status


@receiver(post_save, sender=RepairTicket)
def notify_repair_ticket_status_change(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_original_status'):
        if instance._original_status != instance.status:
            logger.info(
                f"Repair ticket {instance.ticket_id} status changed from "
                f"{instance._original_status} to {instance.status}. Sending email notification..."
            )
            send_repair_status_email(instance, instance._original_status, instance.status)
            if instance.status != 'quoted':
                RepairMessage.objects.create(
                    ticket=instance,
                    sender_is_admin=True,
                    message=f"🔧 Repair Status Updated to: {instance.get_status_display()}."
                )
            instance._original_status = instance.status


# ==========================================
# PART REQUEST STATUS TRACKING
# ==========================================
@receiver(post_init, sender=PartRequest)
def track_part_request_original_status(sender, instance, **kwargs):
    instance._original_status = instance.status


@receiver(post_save, sender=PartRequest)
def notify_part_request_status_change(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_original_status'):
        if instance._original_status != instance.status:
            logger.info(
                f"Part request {instance.request_id} status changed from "
                f"{instance._original_status} to {instance.status}. Sending email notification..."
            )
            send_part_request_status_email(instance, instance._original_status, instance.status)
            instance._original_status = instance.status


# ==========================================
# TECHNICIAN DIRECT MESSAGE NOTIFICATION
# ==========================================
@receiver(post_save, sender=RepairMessage)
def notify_technician_message_sent(sender, instance, created, **kwargs):
    if created and instance.sender_is_admin:
        # Don't send double email if this is an automated system note
        if any(instance.message.startswith(prefix) for prefix in ("📋", "🔧", "✅", "❌")):
            return
        logger.info(
            f"Technician sent note on Ticket {instance.ticket.ticket_id}. "
            "Dispatching email notification to client..."
        )
        send_technician_message_email(instance)
