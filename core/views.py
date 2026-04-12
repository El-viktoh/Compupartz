from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from store.models import Product
from .models import FAQ, Profile
from blog.models import Post
from media_hub.models import Video

# =========================
# HOME
# =========================
def home(request):
    featured_products = Product.objects.filter(available=True)[:6]
    faqs = FAQ.objects.filter(is_published=True)
    latest_posts = Post.objects.filter(status='published').order_by('-created_at')[:3]
    featured_videos = Video.objects.filter(is_featured=True)

    # ✅ attach rating data
    for product in featured_products:
        product.avg_rating = product.get_average_rating()
        product.review_count = product.get_review_count()

    return render(request, "home.html", {
        "featured_products": featured_products,
        "faqs": faqs,
        "latest_posts": latest_posts,
        "featured_videos": featured_videos
    })


from .forms import RegistrationForm

# =========================
# SIGNUP
# =========================
def signup(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")

    else:
        form = RegistrationForm()

    return render(request, "registration/signup.html", {
        "form": form
    })


from customer_orders.models import Order
from repair.models import RepairTicket
from .forms import UserUpdateForm, ProfileUpdateForm

# =========================
# DASHBOARD
# =========================
@login_required
def dashboard(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    repairs = RepairTicket.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    # ✅ attach product image from first order item
    for order in orders:
        first_item = order.items.first()

        if first_item and hasattr(first_item, "product") and first_item.product and first_item.product.image:
            order.image = first_item.product.image.url
        else:
            order.image = None

    # ✅ ENSURE PROFILE EXISTS (Fixes crash for existing users)
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # ✅ GET FORMS FOR MODAL
    u_form = UserUpdateForm(instance=request.user)
    p_form = ProfileUpdateForm(instance=profile)

    return render(request, "account/dashboard.html", {
        "orders": orders,
        "repairs": repairs,
        "u_form": u_form,
        "p_form": p_form,
    })


# =========================
# UPDATE PROFILE
# =========================
@login_required
def update_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        
        # ✅ ENSURE PROFILE EXISTS
        profile, created = Profile.objects.get_or_create(user=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('dashboard')

    return redirect('dashboard')
# TERMS & PRIVACY
# =========================
def terms(request):
    return render(request, "core/terms.html")

def privacy_policy(request):
    return render(request, "core/privacy.html")
    
    return redirect('dashboard')