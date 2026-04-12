from django.shortcuts import render, get_object_or_404
from .models import Product
from .models import Product, Review
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

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

    return render(request, "store/store_home.html", {
        "laptops": products,
        "query": query
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})

def product_detail(request, pk):
    product = Product.objects.get(id=pk)

    reviews = product.reviews.all().order_by("-created_at")

    avg_rating = (
        sum(r.rating for r in reviews) / reviews.count()
        if reviews.count() > 0 else 0
    )

    return render(request, "store/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "avg_rating": round(avg_rating, 1),
    })

@login_required
def add_review(request, pk):
    product = Product.objects.get(id=pk)

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