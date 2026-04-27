from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, Review, Wishlist

# ⭐ Wishlist logic initialized

def store_home(request):
    query = request.GET.get("q")
    category = request.GET.get("category")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    in_stock = request.GET.get("in_stock")

    products = Product.objects.filter(available=True)

    # 🔍 SEARCH
    if query:
        products = products.filter(name__icontains=query)

    # 📦 CATEGORY
    if category and category != "all":
        products = products.filter(category=category)

    # 💰 PRICE FILTER
    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    # ✅ STOCK FILTER
    if in_stock == "1":
        products = products.filter(available=True)

    # If user is logged in, get their wishlist IDs for UI
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    return render(request, "store/store_home.html", {
        "laptops": products,
        "query": query,
        "wishlist_ids": wishlist_ids
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, id=pk)
    reviews = product.reviews.all().order_by("-created_at")

    avg_rating = product.get_average_rating()
    
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    return render(request, "store/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "in_wishlist": in_wishlist
    })

@login_required
def add_review(request, pk):
    product = get_object_or_404(Product, id=pk)

    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment")

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )

    return redirect("product_detail", pk=pk)

@login_required
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, id=pk)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if not created:
        wishlist_item.delete()
        status = "removed"
    else:
        status = "added"

    return JsonResponse({"status": status})

@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user)
    return render(request, "store/wishlist.html", {"wishlist_items": items})