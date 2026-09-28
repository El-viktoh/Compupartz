import logging
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver
from .models import Order
from .utils import send_order_status_email

logger = logging.getLogger(__name__)


@receiver(post_init, sender=Order)
def track_order_original_status(sender, instance, **kwargs):
    instance._original_status = instance.status


@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_original_status'):
        if instance._original_status != instance.status:
            logger.info(
                f"Order #{instance.id} status changed from "
                f"{instance._original_status} to {instance.status}. Dispatching email notification..."
            )
            send_order_status_email(instance, instance._original_status, instance.status)
            instance._original_status = instance.status
