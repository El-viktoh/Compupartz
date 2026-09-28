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

    LOGISTICS_CHOICES = [
        ('drop_off', 'Lab Drop-off'),
        ('courier', 'Courier Pickup'),
    ]

    DEVICE_CATEGORIES = [
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile Device'),
        ('tablet', 'Tablet'),
        ('other', 'Other'),
    ]

    # ✅ USER (linked to account)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # ✅ SIMPLE TRACKING ID (R-1001, R-1002...)
    # null=True (not just blank) so two concurrent inserts can both go through
    # with no ticket_id yet without tripping the unique constraint on "" — see save().
    ticket_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        null=True
    )

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)

    device_category = models.CharField(max_length=50, choices=DEVICE_CATEGORIES, default='laptop')
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    device = models.CharField(max_length=255, verbose_name="Model Identifier / Serial Number")
    
    issue_description = models.TextField()
    diagnostic_image = models.ImageField(upload_to='diagnostics/', blank=True, null=True)

    contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHODS,
        default='form'
    )

    logistics_preference = models.CharField(
        max_length=20,
        choices=LOGISTICS_CHOICES,
        default='drop_off'
    )
    in_person = models.BooleanField(default=False) # Kept for backward compatibility if needed

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ AUTO GENERATE SIMPLE ID
    # Derived from the auto-incrementing PK (assigned atomically by the DB on
    # insert) instead of "last id + 1", so concurrent bookings can't compute
    # the same ticket_id and collide on the unique constraint.
    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating:
            self.ticket_id = None

        super().save(*args, **kwargs)

        if creating:
            self.ticket_id = f"R-{self.pk}"
            super().save(update_fields=["ticket_id"])

    def __str__(self):
        return self.ticket_id

class PartRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('quoted', 'Quoted'),
        ('fulfilled', 'Fulfilled'),
        ('declined', 'Declined'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('refurbished', 'Refurbished'),
        ('used', 'Used'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Simple tracking ID (P-1001, P-1002...) — same collision-safe pattern as RepairTicket.ticket_id
    request_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        null=True
    )

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20)

    part_needed = models.CharField(max_length=255, verbose_name="Part Needed")
    device_model = models.CharField(max_length=255, verbose_name="Device / Model")
    condition_preference = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='new'
    )
    additional_details = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    quoted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Quoted Price (GH₵)"
    )
    admin_notes = models.TextField(
        blank=True,
        verbose_name="Technician / Bench Notes"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating:
            self.request_id = None

        super().save(*args, **kwargs)

        if creating:
            self.request_id = f"P-{self.pk}"
            super().save(update_fields=["request_id"])

    def __str__(self):
        return self.request_id


class RepairMessage(models.Model):
    ticket = models.ForeignKey(RepairTicket, on_delete=models.CASCADE, related_name='messages')
    sender_is_admin = models.BooleanField(default=False)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message on {self.ticket.ticket_id} at {self.created_at}"
