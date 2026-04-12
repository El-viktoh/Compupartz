import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail

from .models import Order
from repair.models import RepairTicket
from cart.cart import Cart
from .utils import send_order_email


def verify_payment(request, reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    result = response.json()

    if result.get("status") and result["data"]["status"] == "success":
        order = get_object_or_404(Order, payment_reference=reference)

        # ✅ Update order
        order.payment_status = "paid"
        order.status = "processing"
        order.paid_at = timezone.now()
        order.save()

        # ✅ Send confirmation email
        send_order_email(order)

        # ✅ Clear cart
        cart = Cart(request)
        cart.session.flush()

        # ✅ Redirect to tracking page
        return render(request, "customer_orders/payment_success.html", {
            "order": order
        })

    return render(request, "customer_orders/payment_failed.html")


def track_lookup(request):
    error = None

    if request.method == "POST":
        tracking_id = request.POST.get("tracking_id")
        phone = request.POST.get("phone")

        # Try store order first (numeric ID)
        if tracking_id and tracking_id.isdigit():
            order = Order.objects.filter(id=tracking_id, phone=phone).first()
            if order:
                return redirect("track_order", order.id)

        # Try repair ticket (e.g. R-6)
        from repair.models import RepairTicket
        ticket = RepairTicket.objects.filter(ticket_id=tracking_id).first()

        if ticket and ticket.customer_phone == phone:
            return redirect("track_repair", ticket_id=ticket.ticket_id)

        # ❌ If we reach here — nothing matched
        error = "No matching order or repair ticket found. Please check your ID and phone number."

    return render(request, "customer_orders/track_lookup.html", {
        "error": error
    })

def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    return render(request, "customer_orders/track_order.html", {
        "order": order
    })
