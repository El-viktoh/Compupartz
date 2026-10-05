from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import RepairBookingForm, PartRequestForm
from .models import RepairTicket, RepairMessage, PartRequest
from .utils import (
    send_repair_email,
    send_part_request_email,
    send_formal_repair_quote_email,
    send_formal_part_quote_email,
    send_admin_repair_notification,
    send_admin_part_request_notification,
)


def repair_home(request):
    from core.models import Testimonial
    testimonials = Testimonial.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')[:12]
    return render(request, "repair/repair_home.html", {
        "testimonials": testimonials,
    })


def reviews_redirect(request):
    return redirect('reviews')


def book_repair(request):
    if request.method == "POST":
        form = RepairBookingForm(request.POST, request.FILES)

        if form.is_valid():
            ticket = form.save(commit=False)

            # ✅ LINK TO LOGGED-IN USER
            if request.user.is_authenticated:
                ticket.user = request.user

            ticket.save()

            _grant_ticket_access(request, ticket)

            # ✅ SEND EMAIL
            send_repair_email(ticket)
            send_admin_repair_notification(ticket)

            return redirect("repair_success", ticket_id=ticket.id)

    else:
        initial = {}
        if request.user.is_authenticated:
            full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            initial["customer_name"] = full_name
            if request.user.email:
                initial["customer_email"] = request.user.email
            if hasattr(request.user, "profile") and getattr(request.user.profile, "phone", None):
                initial["customer_phone"] = request.user.profile.phone
        form = RepairBookingForm(initial=initial)

    return render(request, "repair/book_repair.html", {"form": form})


def repair_success(request, ticket_id):
    ticket = get_object_or_404(RepairTicket, id=ticket_id)
    return render(request, "repair/repair_success.html", {"ticket": ticket})


def request_part(request):
    if request.method == "POST":
        form = PartRequestForm(request.POST)

        if form.is_valid():
            part_request = form.save(commit=False)

            if request.user.is_authenticated:
                part_request.user = request.user

            part_request.save()

            send_part_request_email(part_request)
            send_admin_part_request_notification(part_request)

            return redirect("part_request_success", request_id=part_request.id)

    else:
        initial = {}
        if request.user.is_authenticated:
            full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            initial["customer_name"] = full_name
            if request.user.email:
                initial["customer_email"] = request.user.email
            if hasattr(request.user, "profile") and getattr(request.user.profile, "phone", None):
                initial["customer_phone"] = request.user.profile.phone
        form = PartRequestForm(initial=initial)

    return render(request, "repair/request_part.html", {"form": form})


def part_request_success(request, request_id):
    part_request = get_object_or_404(PartRequest, id=request_id)
    return render(request, "repair/part_request_success.html", {"part_request": part_request})


# ===========================
# ✅ ACCESS CONTROL: REPAIRS
# ===========================
def _can_access_ticket(request, ticket):
    if request.user.is_authenticated:
        if request.user.is_staff or ticket.user_id == request.user.id:
            return True
        if ticket.user_id is None and request.user.email and ticket.customer_email and ticket.customer_email.strip().lower() == request.user.email.strip().lower():
            return True

    verified_tickets = request.session.get("verified_repair_tickets", [])
    return ticket.ticket_id in verified_tickets


def _grant_ticket_access(request, ticket):
    verified_tickets = request.session.setdefault("verified_repair_tickets", [])
    if ticket.ticket_id not in verified_tickets:
        verified_tickets.append(ticket.ticket_id)
        request.session.modified = True


# ===========================
# ✅ ACCESS CONTROL: PARTS
# ===========================
def _can_access_part_request(request, part_request):
    if request.user.is_authenticated:
        if request.user.is_staff or part_request.user_id == request.user.id:
            return True
        if part_request.user_id is None and request.user.email and part_request.customer_email and part_request.customer_email.strip().lower() == request.user.email.strip().lower():
            return True

    verified_part_requests = request.session.get("verified_part_requests", [])
    return part_request.request_id in verified_part_requests


def _grant_part_request_access(request, part_request):
    verified_part_requests = request.session.setdefault("verified_part_requests", [])
    if part_request.request_id not in verified_part_requests:
        verified_part_requests.append(part_request.request_id)
        request.session.modified = True


# ===========================
# ✅ TRACK REPAIR (LOOKUP)
# ===========================
def track_repair_lookup(request):
    if request.method == "POST":
        ticket_id = request.POST.get("ticket_id")
        phone = request.POST.get("phone")

        ticket = RepairTicket.objects.filter(
            ticket_id=ticket_id,
            customer_phone=phone
        ).first()

        if ticket:
            _grant_ticket_access(request, ticket)
            return redirect("track_repair", ticket_id=ticket.ticket_id)

        messages.error(
            request,
            "Ticket not found. Check your Ticket ID and phone number."
        )

    return render(request, "repair/track_repair_lookup.html")


# ===========================
# ✅ TRACK REPAIR (RESULT)
# ===========================
def track_repair(request, ticket_id):
    ticket = get_object_or_404(RepairTicket, ticket_id=ticket_id)

    if not _can_access_ticket(request, ticket):
        messages.error(request, "Please verify your Ticket ID and phone number to view this ticket.")
        return redirect("track_repair_lookup")

    if request.method == "POST" and "message" in request.POST:
        message_text = request.POST.get("message", "").strip()
        if message_text:
            RepairMessage.objects.create(
                ticket=ticket,
                message=message_text,
                sender_is_admin=request.user.is_authenticated and request.user.is_staff
            )
            messages.success(request, "Message sent successfully.")

        referer = request.META.get('HTTP_REFERER')
        if referer and 'dashboard' in referer:
            return redirect(f"/dashboard/?tab=communications&ticket={ticket.id}#comms-ticket-{ticket.id}")
        return redirect("track_repair", ticket_id=ticket.ticket_id)

    return render(request, "repair/track_repair.html", {
        "ticket": ticket
    })


# ===========================
# 🎯 STAFF QUOTE CREATION: REPAIRS (STAFF ONLY)
# ===========================
@login_required
def staff_create_repair_quote(request, ticket_id):
    if not request.user.is_staff:
        raise PermissionDenied

    ticket = get_object_or_404(RepairTicket, ticket_id=ticket_id)

    if request.method == "POST":
        price_raw = request.POST.get("quoted_price", "").strip()
        diagnostic_notes = request.POST.get("diagnostic_notes", "").strip()
        estimated_turnaround = request.POST.get("estimated_turnaround", "24 - 48 Hours").strip()
        warranty_period = request.POST.get("warranty_period", "90-Day Compupartz Warranty").strip()

        try:
            price = Decimal(price_raw)
            if price <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, "Please provide a valid quote price greater than zero.")
            return redirect("track_repair", ticket_id=ticket.ticket_id)

        ticket.quoted_price = price
        ticket.diagnostic_notes = diagnostic_notes
        ticket.estimated_turnaround = estimated_turnaround
        ticket.warranty_period = warranty_period
        ticket.status = "quoted"
        ticket.quote_status = "sent"
        ticket.quote_sent_at = timezone.now()
        ticket.save()

        # Send formal quotation email
        send_formal_repair_quote_email(ticket)

        # Record in message thread
        RepairMessage.objects.create(
            ticket=ticket,
            sender_is_admin=True,
            message=(
                f"📋 Formal Repair Quote Dispatched: GH₵ {ticket.quoted_price}. "
                f"Diagnostic Scope: {ticket.diagnostic_notes or 'Comprehensive board-level restoration'}. "
                f"Turnaround: {ticket.estimated_turnaround}. Warranty: {ticket.warranty_period}."
            )
        )

        messages.success(
            request,
            f"Formal repair quote of GH₵ {ticket.quoted_price} generated and emailed to {ticket.customer_email}."
        )

    return redirect("track_repair", ticket_id=ticket.ticket_id)


# ===========================
# 🛠️ STAFF STATUS UPDATE: REPAIRS (STAFF ONLY)
# ===========================
@login_required
def staff_update_repair_status(request, ticket_id):
    if not request.user.is_staff:
        raise PermissionDenied

    ticket = get_object_or_404(RepairTicket, ticket_id=ticket_id)

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        if new_status == 'cancelled':
            new_status = 'no_fix'
        status_note = request.POST.get("status_note", "").strip()

        valid_statuses = dict(RepairTicket.STATUS_CHOICES)
        if new_status in valid_statuses:
            ticket.status = new_status
            ticket.save()

            if status_note:
                RepairMessage.objects.create(
                    ticket=ticket,
                    sender_is_admin=True,
                    message=f"🔧 Bench Note ({ticket.get_status_display()}): {status_note}"
                )

            messages.success(
                request,
                f"Ticket #{ticket.ticket_id} status updated to '{ticket.get_status_display()}'. Real-time email dispatched to {ticket.customer_email}."
            )
        else:
            messages.error(request, "Invalid status choice selected.")

    referer = request.META.get('HTTP_REFERER')
    if referer and 'dashboard' in referer:
        return redirect('/dashboard/?tab=staff-workshop')
    return redirect("track_repair", ticket_id=ticket.ticket_id)


def customer_approve_repair_quote(request, ticket_id):
    ticket = get_object_or_404(RepairTicket, ticket_id=ticket_id)

    if not _can_access_ticket(request, ticket):
        raise PermissionDenied

    if request.method == "POST":
        if ticket.quote_status != "sent":
            messages.error(request, "There is no active quote awaiting your approval on this ticket.")
            return redirect("track_repair", ticket_id=ticket.ticket_id)
        ticket.quote_status = "approved"
        ticket.status = "in_progress"
        ticket.save()

        RepairMessage.objects.create(
            ticket=ticket,
            sender_is_admin=False,
            message=(
                f"✅ Quote Approved: Client {ticket.customer_name} approved the repair estimate "
                f"of GH₵ {ticket.quoted_price}. Bench restoration is authorized."
            )
        )

        messages.success(
            request,
            "Quote approved! Our certified technicians have been authorized and are initiating bench restoration."
        )

    return redirect("track_repair", ticket_id=ticket.ticket_id)


def customer_decline_repair_quote(request, ticket_id):
    ticket = get_object_or_404(RepairTicket, ticket_id=ticket_id)

    if not _can_access_ticket(request, ticket):
        raise PermissionDenied

    if request.method == "POST":
        if ticket.quote_status != "sent":
            messages.error(request, "There is no active quote awaiting your response on this ticket.")
            return redirect("track_repair", ticket_id=ticket.ticket_id)
        ticket.quote_status = "declined"
        ticket.save()

        RepairMessage.objects.create(
            ticket=ticket,
            sender_is_admin=False,
            message=f"❌ Client {ticket.customer_name} declined the current repair quote."
        )

        messages.info(request, "Quote declined. Our technicians have been notified.")

    return redirect("track_repair", ticket_id=ticket.ticket_id)


# ===========================
# 🎯 STAFF QUOTE CREATION: PARTS (STAFF ONLY)
# ===========================
@login_required
def staff_create_part_quote(request, request_id):
    if not request.user.is_staff:
        raise PermissionDenied

    part_request = get_object_or_404(PartRequest, request_id=request_id)

    if request.method == "POST":
        price_raw = request.POST.get("quoted_price", "").strip()
        admin_notes = request.POST.get("admin_notes", "").strip()
        estimated_delivery = request.POST.get("estimated_delivery", "24 - 48 Hours").strip()
        warranty_period = request.POST.get("warranty_period", "90-Day OEM Replacement Warranty").strip()

        try:
            price = Decimal(price_raw)
            if price <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, "Please enter a valid price greater than zero.")
            return redirect("track_part", request_id=part_request.request_id)

        part_request.quoted_price = price
        part_request.admin_notes = admin_notes
        part_request.estimated_delivery = estimated_delivery
        part_request.warranty_period = warranty_period
        part_request.status = "quoted"
        part_request.quote_status = "sent"
        part_request.quote_sent_at = timezone.now()
        part_request.save()

        send_formal_part_quote_email(part_request)

        messages.success(
            request,
            f"Hardware sourcing quote of GH₵ {part_request.quoted_price} generated and emailed to {part_request.customer_email}."
        )

    return redirect("track_part", request_id=part_request.request_id)


# ===========================
# 🛠️ STAFF STATUS UPDATE: PARTS (STAFF ONLY)
# ===========================
@login_required
def staff_update_part_status(request, request_id):
    if not request.user.is_staff:
        raise PermissionDenied

    part_request = get_object_or_404(PartRequest, request_id=request_id)

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
        admin_notes = request.POST.get("admin_notes", "").strip()

        valid_statuses = dict(PartRequest.STATUS_CHOICES)
        if new_status in valid_statuses:
            part_request.status = new_status
            if admin_notes:
                part_request.admin_notes = admin_notes
            part_request.save()

            messages.success(
                request,
                f"Part Request #{part_request.request_id} status updated to '{part_request.get_status_display()}'. Real-time email dispatched to {part_request.customer_email}."
            )
        else:
            messages.error(request, "Invalid status choice selected.")

    referer = request.META.get('HTTP_REFERER')
    if referer and 'dashboard' in referer:
        return redirect('/dashboard/?tab=staff-workshop')
    return redirect("track_part", request_id=part_request.request_id)


def customer_approve_part_quote(request, request_id):
    part_request = get_object_or_404(PartRequest, request_id=request_id)

    if not _can_access_part_request(request, part_request):
        raise PermissionDenied

    if request.method == "POST":
        if part_request.quote_status != "sent":
            messages.error(request, "There is no active quote awaiting your approval on this request.")
            return redirect("track_part", request_id=part_request.request_id)
        part_request.quote_status = "approved"
        part_request.save()

        messages.success(
            request,
            "Part quote confirmed! Our procurement desk is securing your component."
        )

    return redirect("track_part", request_id=part_request.request_id)


# ===========================
# ✅ TRACK PART REQUEST
# ===========================
def track_part_lookup(request):
    if request.method == "POST":
        request_id = request.POST.get("request_id", "").strip()
        phone = request.POST.get("phone", "").strip()

        part_request = PartRequest.objects.filter(
            request_id__iexact=request_id,
            customer_phone=phone
        ).first()

        if part_request:
            _grant_part_request_access(request, part_request)
            return redirect("track_part", request_id=part_request.request_id)

        messages.error(
            request,
            "Part request not found. Check your Request ID (e.g. P-1) and phone number."
        )

    return render(request, "repair/track_part_lookup.html")


def track_part(request, request_id):
    part_request = get_object_or_404(PartRequest, request_id=request_id)

    if not _can_access_part_request(request, part_request):
        messages.error(request, "Please verify your Request ID and phone number to view this request.")
        return redirect("track_part_lookup")

    return render(request, "repair/track_part.html", {
        "part_request": part_request
    })


@login_required
def my_repairs(request):
    repairs = RepairTicket.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "repair/my_repairs.html", {
        "repairs": repairs
    })


def edit_repair_message(request, message_id):
    message = get_object_or_404(RepairMessage, id=message_id)

    is_owner = False
    if request.user.is_authenticated:
        if request.user.is_staff and message.sender_is_admin:
            is_owner = True
        elif not message.sender_is_admin and _can_access_ticket(request, message.ticket):
            is_owner = True
    elif not message.sender_is_admin and _can_access_ticket(request, message.ticket):
        is_owner = True

    if request.method != "POST" or not is_owner:
        raise PermissionDenied

    new_text = request.POST.get("message", "").strip()
    if new_text:
        message.message = new_text
        message.save()
        messages.success(request, "Message updated successfully.")

    referer = request.META.get('HTTP_REFERER')
    if referer and 'dashboard' in referer:
        return redirect(f"/dashboard/?tab=communications&ticket={message.ticket.id}#comms-ticket-{message.ticket.id}")
    return redirect("track_repair", ticket_id=message.ticket.ticket_id)


def delete_repair_message(request, message_id):
    message = get_object_or_404(RepairMessage, id=message_id)

    is_owner = False
    if request.user.is_authenticated:
        if request.user.is_staff and message.sender_is_admin:
            is_owner = True
        elif not message.sender_is_admin and _can_access_ticket(request, message.ticket):
            is_owner = True
    elif not message.sender_is_admin and _can_access_ticket(request, message.ticket):
        is_owner = True

    if request.method != "POST" or not is_owner:
        raise PermissionDenied

    ticket_id = message.ticket.ticket_id
    ticket_pk = message.ticket.id
    message.delete()
    messages.success(request, "Message deleted successfully.")

    referer = request.META.get('HTTP_REFERER')
    if referer and 'dashboard' in referer:
        return redirect(f"/dashboard/?tab=communications&ticket={ticket_pk}#comms-ticket-{ticket_pk}")
    return redirect("track_repair", ticket_id=ticket_id)


# ===========================
# 📧 LIVE EMAIL PREVIEWS (DEV / DEMO)
# ===========================
@staff_member_required
def preview_repair_quote_email(request):
    """Live preview of the formal repair quotation email sent to customers."""
    ticket = RepairTicket.objects.filter(quoted_price__isnull=False).first()
    if not ticket:
        ticket = RepairTicket(
            ticket_id="R-108",
            customer_name="Kwame Mensah",
            customer_email="kwame@example.com",
            customer_phone="+233 54 123 4567",
            device="MacBook Pro 16\" M1 Pro (A2485)",
            quoted_price=Decimal("850.00"),
            diagnostic_notes="Shorted 3.3V power management rail restored, micro-soldered replacement capacitors, renewed thermal paste, and passed benchmark testing.",
            estimated_turnaround="24 - 48 Hours",
            warranty_period="90-Day Compupartz Warranty",
            status="quoted",
            quote_status="sent",
        )

    tracking_url = request.build_absolute_uri(f"/accounts/login/?next=/repair/track/{ticket.ticket_id}/")
    return render(request, "emails/formal_repair_quote.html", {
        "ticket": ticket,
        "tracking_url": tracking_url,
    })


@staff_member_required
def preview_part_quote_email(request):
    """Live preview of the formal part request quotation email sent to customers."""
    part_request = PartRequest.objects.filter(quoted_price__isnull=False).first()
    if not part_request:
        part_request = PartRequest(
            request_id="P-42",
            customer_name="Akosua Agyeman",
            customer_email="akosua@example.com",
            customer_phone="+233 20 987 6543",
            part_needed="Original OEM 96W USB-C Power Adapter + Type-C Braided Cable",
            device_model="Apple MacBook Pro 16-inch",
            quoted_price=Decimal("480.00"),
            admin_notes="Verified original OEM inventory in stock with authorized distributor. Grade-A certified with Compupartz warranty seal.",
            estimated_delivery="Same Day / 24 Hours",
            warranty_period="90-Day OEM Replacement Warranty",
            status="quoted",
            quote_status="sent",
        )

    login_url = request.build_absolute_uri("/accounts/login/?next=/dashboard/?tab=parts")
    return render(request, "emails/formal_part_quote.html", {
        "part_request": part_request,
        "tracking_url": login_url,
        "login_url": login_url,
    })


@staff_member_required
def preview_repair_intake_email(request):
    """Live preview of the initial intake confirmation email sent with tracking ID upon repair booking."""
    ticket = RepairTicket.objects.first()
    if not ticket:
        ticket = RepairTicket(
            ticket_id="R-108",
            customer_name="Kwame Mensah",
            customer_email="kwame@example.com",
            customer_phone="+233 54 123 4567",
            device="MacBook Pro 16\" M1 Pro (A2485)",
            issue_description="Logic board power issue, device will not boot or display charge indicator.",
            status="submitted",
        )

    tracking_url = request.build_absolute_uri(f"/accounts/login/?next=/repair/track/{ticket.ticket_id}/")
    status_message = "Your repair booking has been registered on our intake bench. Our certified technicians are reviewing your fault diagnostic details and will initiate bench testing shortly."

    return render(request, "emails/repair_status_update.html", {
        "ticket": ticket,
        "status_display": ticket.get_status_display(),
        "status_message": status_message,
        "tracking_url": tracking_url,
    })


@staff_member_required
def preview_part_intake_email(request):
    """Live preview of the initial intake confirmation email sent with request ID upon part request."""
    part_request = PartRequest.objects.first()
    if not part_request:
        part_request = PartRequest(
            request_id="PR-042",
            customer_name="Akosua Agyeman",
            customer_email="akosua@example.com",
            customer_phone="+233 20 987 6543",
            part_needed="Original OEM 96W USB-C Power Adapter + Type-C Braided Cable",
            device_model="Apple MacBook Pro 16-inch",
            condition_preference="brand_new",
            status="submitted",
        )

    login_url = request.build_absolute_uri("/accounts/login/?next=/dashboard/?tab=parts")
    status_message = "Your hardware part sourcing request has been received. Our parts desk is contacting verified OEM distributors to verify component availability and compute your quote."

    return render(request, "emails/part_request_status_update.html", {
        "part_request": part_request,
        "status_display": part_request.get_status_display(),
        "status_message": status_message,
        "login_url": login_url,
        "dashboard_url": login_url,
    })


@staff_member_required
def preview_admin_repair_email(request):
    """Live preview of staff notification email for new repair ticket."""
    ticket = RepairTicket.objects.first()
    if not ticket:
        ticket = RepairTicket(
            ticket_id="R-108",
            customer_name="Kwame Mensah",
            customer_email="kwame@example.com",
            customer_phone="+233 54 123 4567",
            device_category="laptop",
            manufacturer="Apple",
            device="MacBook Pro 16\" M1 Pro (A2485)",
            issue_description="Liquid spill on keyboard, logic board power rail shorted, no display and won't turn on.",
            contact_method="whatsapp",
            logistics_preference="drop_off",
            status="pending",
        )
    admin_url = request.build_absolute_uri(f"/admin/repair/repairticket/{ticket.id or 1}/change/")
    whatsapp_url = "https://wa.me/233541234567"
    return render(request, "emails/admin_notification.html", {
        "notification_type": "repair_ticket",
        "ticket": ticket,
        "admin_url": admin_url,
        "whatsapp_url": whatsapp_url,
        "domain": "compupartz.com",
    })


@staff_member_required
def preview_admin_part_email(request):
    """Live preview of staff notification email for new part sourcing request."""
    part_request = PartRequest.objects.first()
    if not part_request:
        part_request = PartRequest(
            request_id="P-042",
            customer_name="Akosua Agyeman",
            customer_email="akosua@example.com",
            customer_phone="+233 20 987 6543",
            part_needed="Original OEM 96W USB-C Power Adapter + Type-C Braided Cable",
            device_model="Apple MacBook Pro 16-inch (A2485)",
            condition_preference="new",
            additional_details="Need genuine OEM brick with GH 3-pin plug adapter if available.",
            status="pending",
        )
    admin_url = request.build_absolute_uri(f"/admin/repair/partrequest/{part_request.id or 1}/change/")
    whatsapp_url = "https://wa.me/233209876543"
    return render(request, "emails/admin_notification.html", {
        "notification_type": "part_request",
        "part_request": part_request,
        "admin_url": admin_url,
        "whatsapp_url": whatsapp_url,
        "domain": "compupartz.com",
    })


@staff_member_required
def preview_admin_testimonial_email(request):
    """Live preview of staff notification email for new testimonial review."""
    from core.models import Testimonial
    testimonial = Testimonial.objects.first()
    if not testimonial:
        testimonial = Testimonial(
            name="Emmanuel Osei",
            role_or_title="Software Developer",
            service_rendered="MacBook Logic Board Micro-Soldering",
            rating=5,
            quote="Compupartz revived my MacBook Pro logic board in less than 24 hours when other shops told me to buy a new machine! Incredible craftsmanship and transparency.",
            is_approved=True,
            is_featured=False,
        )
    admin_url = request.build_absolute_uri(f"/admin/core/testimonial/{testimonial.id or 1}/change/")
    return render(request, "emails/admin_notification.html", {
        "notification_type": "testimonial",
        "testimonial": testimonial,
        "admin_url": admin_url,
        "domain": "compupartz.com",
    })






