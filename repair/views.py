from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
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
        form = RepairBookingForm()

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
        form = PartRequestForm()

    return render(request, "repair/request_part.html", {"form": form})


def part_request_success(request, request_id):
    part_request = get_object_or_404(PartRequest, id=request_id)
    return render(request, "repair/part_request_success.html", {"part_request": part_request})


# ===========================
# ✅ ACCESS CONTROL
# ===========================
# A ticket is visible to: its owner, staff, or a browser session that has
# proven it knows the ticket ID + phone number via track_repair_lookup.
# This keeps the no-account booking + guest tracking flow working while
# closing off tracking-by-guessing-the-URL.
def _can_access_ticket(request, ticket):
    if request.user.is_authenticated and (request.user.is_staff or ticket.user_id == request.user.id):
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

    if request.method != "POST" or message.sender_is_admin or not _can_access_ticket(request, message.ticket):
        raise PermissionDenied

    new_text = request.POST.get("message", "").strip()
    if new_text:
        message.message = new_text
        message.save()
        messages.success(request, "Message updated successfully.")

    return redirect("track_repair", ticket_id=message.ticket.ticket_id)


def delete_repair_message(request, message_id):
    message = get_object_or_404(RepairMessage, id=message_id)

    if request.method != "POST" or message.sender_is_admin or not _can_access_ticket(request, message.ticket):
        raise PermissionDenied

    ticket_id = message.ticket.ticket_id
    message.delete()
    messages.success(request, "Message deleted successfully.")

    return redirect("track_repair", ticket_id=ticket_id)
