from django.db import models
from django.contrib.auth.models import User


class RepairTicket(models.Model):
    CONTACT_METHODS = [
        ('form', 'Form'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    # ✅ USER (linked to account)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # ✅ SIMPLE TRACKING ID (R-1001, R-1002...)
    ticket_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True
    )

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)

    device = models.CharField(max_length=255)
    issue_description = models.TextField()

    contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHODS,
        default='form'
    )

    in_person = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ AUTO GENERATE SIMPLE ID
    def save(self, *args, **kwargs):
        if not self.ticket_id:
            last_ticket = RepairTicket.objects.order_by("-id").first()
            next_number = (last_ticket.id + 1) if last_ticket else 1000
            self.ticket_id = f"R-{next_number}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_id
