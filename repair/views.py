from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .forms import RepairBookingForm
from .models import RepairTicket
from .utils import send_repair_email


def repair_home(request):
    return render(request, "repair/repair_home.html")


def book_repair(request):
    if request.method == "POST":
        form = RepairBookingForm(request.POST)

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

    return render(request, "repair/track_repair.html", {
        "ticket": ticket
    })

from django.contrib.auth.decorators import login_required

@login_required
def my_repairs(request):
    repairs = RepairTicket.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "repair/my_repairs.html", {
        "repairs": repairs
    })