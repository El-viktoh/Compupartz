import uuid

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from store.models import Product, Variation
from customer_orders.models import Order, OrderItem
from customer_orders.utils import send_order_email

from .cart import Cart


# =========================
# CART DETAIL
# =========================
def cart_detail(request):
    cart = Cart(request)

    cart_items = list(cart)

    return render(request, "cart/cart_detail.html", {
        "cart": cart_items,
        "cart_total": cart.get_total_price(),
    })


# =========================
# ADD TO CART
# =========================
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    
    variations = []
    if request.method == 'POST':
        for key in request.POST:
            if key.startswith('variation_'):
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, id=value)
                    variations.append(variation)
                except:
                    pass
    
    cart.add(product, variations=variations)
    return redirect("cart_detail")


# =========================
# REMOVE FROM CART
# =========================
def remove_from_cart(request, product_key):
    cart = Cart(request)
    cart.remove(product_key)
    return redirect("cart_detail")


# =========================
# DECREASE ITEM
# =========================
def decrease_cart_item(request, product_key):
    cart = Cart(request)
    cart.decrease(product_key)
    return redirect("cart_detail")


# =========================
# CHECKOUT
# =========================
def checkout(request):
    cart = Cart(request)
    cart_items = list(cart)

    if not cart_items:
        return redirect("cart_detail")

    total_price = cart.get_total_price()

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        address = request.POST.get("address")
        action = request.POST.get("action")

        # ✅ CREATE ORDER
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=name,
            phone=phone,
            email=email,
            address=address,
            total_amount=total_price,
            payment_method="whatsapp" if action == "whatsapp" else "paystack",
            payment_status="unpaid",
            status="pending",
        )

        # ✅ SAVE ORDER ITEMS
        for item in cart_items:
            # Join variations into a clean string
            var_str = ", ".join(item.get("variations", []))
            
            OrderItem.objects.create(
                order=order,
                product_name=item["name"],
                variations_display=var_str,
                price=item["price"],
                quantity=item["quantity"],
                product=Product.objects.get(id=int(item["id"])) if "id" in item else None
            )

        # ✅ SEND EMAIL
        send_order_email(order)

        # ✅ CLEAR CART
        cart.clear()

        # =====================
        # WHATSAPP FLOW
        # =====================
        if action == "whatsapp":
            message = (
                f"New Order:%0A"
                f"Order ID: {order.id}%0A"
                f"Name: {name}%0A"
                f"Phone: {phone}%0A"
                f"Address: {address}%0A%0A"
            )

            for item in cart_items:
                var_info = ""
                if item.get("variations"):
                    var_info = f" ({', '.join(item['variations'])})"
                message += f"{item['name']}{var_info} x {item['quantity']}%0A"

            message += f"%0ATotal: GHS {total_price}"

            whatsapp_url = f"https://wa.me/233540322533?text={message}"
            return redirect(whatsapp_url)

        return redirect("paystack_payment", order_id=order.id)

    return render(request, "cart/checkout.html", {
        "cart": cart_items,
        "cart_total": total_price,
    })


# =========================
# PAYSTACK
# =========================
def paystack_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    reference = str(uuid.uuid4())
    order.payment_reference = reference
    order.payment_method = "paystack"
    order.save()

    return render(request, "cart/paystack.html", {
        "order": order,
        "paystack_public_key": settings.PAYSTACK_PUBLIC_KEY,
        "reference": reference,
    })


# =========================
# AJAX ADD TO CART
# =========================
@require_POST
def ajax_add_to_cart(request):
    product_id = request.POST.get("product_id")
    product = get_object_or_404(Product, id=product_id)

    variations = []
    for key in request.POST:
        if key.startswith('variation_'):
            value = request.POST[key]
            try:
                variation = Variation.objects.get(product=product, id=value)
                variations.append(variation)
            except:
                pass

    cart = Cart(request)
    cart.add(product, variations=variations)

    image = product.image.url if product.image else ""

    return JsonResponse({
        "success": True,
        "cart_count": len(cart),
        "total": cart.get_total_price(),
        "image": image,
        "name": product.name,
    })


# =========================
# AJAX UPDATE CART
# =========================
@require_POST
def ajax_update_cart(request):
    product_key = request.POST.get("product_id") # Note: we still use 'product_id' as the key name in JS for now
    action = request.POST.get("action")

    cart = Cart(request)

    if action == "increase":
        # For increase, we need to find the product and variations from the key
        # key format: productid_v1-v2-...
        try:
            p_id = int(product_key.split('_')[0])
            var_ids = []
            if '_' in product_key and product_key.split('_')[1]:
                var_ids = [int(v) for v in product_key.split('_')[1].split('-')]
            
            product = get_object_or_404(Product, id=p_id)
            variations = Variation.objects.filter(id__in=var_ids)
            cart.add(product, variations=variations)
        except:
            pass
    elif action == "decrease":
        cart.decrease(product_key)
    elif action == "remove":
        cart.remove(product_key)

    updated_item = cart.cart.get(product_key)

    return JsonResponse({
        "cart_count": len(cart),
        "item": {
            "quantity": updated_item["quantity"] if updated_item else 0,
            "price": updated_item["price"] if updated_item else 0,
        },
        "total": cart.get_total_price(),
        "product_id": product_key
    })


# =========================
# AJAX GET CART (SLIDE CART)
# =========================
def cart_ajax_get(request):
    cart = Cart(request)
    items = []

    for item in cart:
        items.append({
            "key": item["key"],
            "id": item["id"],
            "name": item["name"],
            "quantity": item["quantity"],
            "total": item["total"],
            "image": item["image"],
            "variations": item["variations"]
        })

    return JsonResponse({
        "items": items,
        "total": cart.get_total_price()
    })


# =========================
# AJAX CART COUNT (BADGE)
# =========================
def cart_count(request):
    cart = Cart(request)
    return JsonResponse({
        "count": len(cart)
    })
