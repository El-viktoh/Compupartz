from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import RepairBookingForm, PartRequestForm
from .models import RepairTicket, RepairMessage, PartRequest
from .utils import send_repair_email, send_part_request_email


def repair_home(request):
    return render(request, "repair/repair_home.html")


def book_repair(request):
    if request.method == "POST":
        form = RepairBookingForm(request.POST, request.FILES)

        if form.is_valid():
            ticket = form.save(commit=False)

            # ✅ LINK TO LOGGED-IN USER
            if request.user.is_authenticated:
                ticket.user = request.user

            ticket.save()

            # ✅ SEND EMAIL
            send_repair_email(ticket)

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
# ✅ ACCESS CONTROL
# ===========================
# A ticket is visible to: its owner, staff, matching registered email,
# or a browser session verified via track_repair_lookup.
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
# ✅ TRACK REPAIR (LOOKUP)
# ===========================

def track_repair_lookup(request):
    if request.method == "POST":
        ticket_id = request.POST.get("ticket_id")
        phone = request.POST.get("phone")

        # ✅ FIX: USE ticket_id FIELD (NOT id)
        ticket = RepairTicket.objects.filter(
            ticket_id=ticket_id,
            customer_phone=phone
        ).first()

        if ticket:
            _grant_ticket_access(request, ticket)
            return redirect("track_repair", ticket_id=ticket.ticket_id)

        # ❌ SHOW ERROR MESSAGE
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
