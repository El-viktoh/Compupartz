from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from .models import FAQ, Profile
from blog.models import Post
from media_hub.models import Video
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, url_has_allowed_host_and_scheme
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.contrib import messages

# =========================
# HOME
# =========================
def home(request):
    faqs = FAQ.objects.filter(is_published=True)
    latest_posts = Post.objects.filter(status='published').order_by('-created_at')[:3]
    featured_videos = Video.objects.filter(is_featured=True)
    if not featured_videos.exists():
        featured_videos = Video.objects.all()[:6]

    return render(request, "home.html", {
        "faqs": faqs,
        "latest_posts": latest_posts,
        "featured_videos": featured_videos,
    })

from .forms import RegistrationForm

from django.db import transaction
from .utils import send_activation_email
from .notifications import send_admin_testimonial_notification
import logging

logger = logging.getLogger(__name__)

# =========================
# SIGNUP
# =========================
def signup(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False  # ✅ Deactivate account until email confirmation
                    user.save()

                    # ✅ SEND ACTIVATION EMAIL
                    domain = request.get_host()
                    if not send_activation_email(user, domain):
                        raise Exception("Failed to send email")

                # If we reach here, email was sent successfully
                return render(request, "registration/account_activation_sent.html")

            except Exception as e:
                # ❌ LOG THE ERROR ON SERVER
                logger.error(f"Signup Email Error: {str(e)}")
                
                # ❌ Inform user and allow them to fix email/try again
                messages.error(request, "We couldn't send the activation email. Please check your email address or try again later.")
                # The transaction.atomic() handles the rollback of the user creation automatically

    else:
        form = RegistrationForm()

    return render(request, "registration/signup.html", {
        "form": form
    })

# =========================
# ACTIVATE ACCOUNT
# =========================
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
    else:
        return render(request, "registration/account_activation_invalid.html")


from django.db.models import Q
from repair.models import RepairTicket, PartRequest, RepairMessage
from customer_orders.models import Order
from .models import FAQ, Profile, Testimonial
from .forms import UserUpdateForm, ProfileUpdateForm

# =========================
# ⭐ USER DASHBOARD & PROFILE
# =========================
@login_required
def dashboard(request):
    # ✅ ENSURE PROFILE EXISTS (Fixes crash for existing users)
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Link unassigned anonymous tickets, part requests, and orders booked with user's email
    if request.user.email:
        user_email = request.user.email.strip()
        RepairTicket.objects.filter(
            customer_email__iexact=user_email,
            user__isnull=True
        ).update(user=request.user)
        PartRequest.objects.filter(
            customer_email__iexact=user_email,
            user__isnull=True
        ).update(user=request.user)
        Order.objects.filter(
            email__iexact=user_email,
            user__isnull=True
        ).update(user=request.user)

    # Strictly tickets entered / raised by this logged-in user
    user_tickets = RepairTicket.objects.filter(
        user=request.user
    ).prefetch_related('messages').order_by('-created_at')

    active_repairs = user_tickets.filter(status__in=['pending', 'in_progress'])
    past_repairs = user_tickets.filter(status='completed')

    # All tickets raised by user for the lab communications center
    user_all_raised_tickets = user_tickets
    total_user_messages = RepairMessage.objects.filter(ticket__user=request.user).count()

    # Hardware Parts requested & bought by this user
    user_part_requests = PartRequest.objects.filter(user=request.user).order_by('-created_at')
    user_orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    total_parts_and_orders = user_part_requests.count() + user_orders.count()

    # User's submitted testimonials
    user_testimonials = Testimonial.objects.filter(user=request.user).order_by('-created_at')

    # For staff users: workshop queue for tickets and hardware part requests
    staff_bench_repairs = None
    staff_part_requests = None
    if request.user.is_staff:
        staff_bench_repairs = RepairTicket.objects.all().prefetch_related('messages').order_by('-created_at')[:40]
        staff_part_requests = PartRequest.objects.all().order_by('-created_at')[:40]

    # ✅ GET FORMS FOR MODAL
    u_form = UserUpdateForm(instance=request.user)
    p_form = ProfileUpdateForm(instance=profile)

    return render(request, "account/dashboard.html", {
        "active_repairs": active_repairs,
        "past_repairs": past_repairs,
        "user_all_raised_tickets": user_all_raised_tickets,
        "total_user_messages": total_user_messages,
        "user_part_requests": user_part_requests,
        "user_orders": user_orders,
        "total_parts_and_orders": total_parts_and_orders,
        "user_testimonials": user_testimonials,
        "staff_bench_repairs": staff_bench_repairs,
        "staff_part_requests": staff_part_requests,
        "u_form": u_form,
        "p_form": p_form,
    })


# =========================
# REVIEWS & TESTIMONIALS
# =========================
def reviews_list(request):
    from .models import Testimonial
    testimonials = Testimonial.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')
    return render(request, "core/reviews.html", {
        "testimonials": testimonials,
    })


# =========================
# SUBMIT TESTIMONIAL
# =========================
def submit_testimonial(request):
    if request.method == 'POST':
        quote = request.POST.get('quote', '').strip()
        rating = request.POST.get('rating', '5')
        service_rendered = request.POST.get('service_rendered', '').strip()
        role_or_title = request.POST.get('role_or_title', '').strip()
        client_name = request.POST.get('name', '').strip()

        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                rating_val = 5
        except (ValueError, TypeError):
            rating_val = 5

        if quote:
            if request.user.is_authenticated:
                user_obj = request.user
                if not client_name:
                    client_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            else:
                user_obj = None
                if not client_name:
                    client_name = "Verified Client"

            testimonial = Testimonial.objects.create(
                user=user_obj,
                name=client_name,
                role_or_title=role_or_title or "Verified Client",
                quote=quote,
                rating=rating_val,
                service_rendered=service_rendered or "Hardware Diagnostics & Restoration",
                is_approved=False,
                is_featured=False
            )
            send_admin_testimonial_notification(testimonial)
            messages.success(request, "Thank you! Your review has been submitted and will appear on the site once our team has approved it.")
        else:
            messages.error(request, "Please enter your review feedback before submitting.")

    candidate = request.POST.get('next') or request.META.get('HTTP_REFERER') or ''
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(candidate)
    return redirect('reviews')


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
            messages.success(request, "Your profile was updated successfully.")
        else:
            for form in (u_form, p_form):
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)

    return redirect('dashboard')

# =========================
# TERMS & PRIVACY
# =========================
def terms(request):
    return render(request, "core/terms.html")

def privacy_policy(request):
    return render(request, "core/privacy.html")

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        subject = request.POST.get("subject", "").strip()
        message_body = request.POST.get("message", "").strip()

        if name and email and subject and message_body:
            try:
                body_content = f"From: {name} <{email}>\n"
                if phone:
                    body_content += f"Phone / WhatsApp: {phone}\n"
                body_content += f"\n{message_body}"

                EmailMessage(
                    subject=f"[Contact Form] {subject}",
                    body=body_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.SERVER_EMAIL],
                    reply_to=[email],
                ).send(fail_silently=False)
                messages.success(request, "Your message has been sent. We'll get back to you shortly.")
            except Exception as e:
                logger.error(f"Contact form email error: {str(e)}")
                messages.error(request, "We couldn't send your message right now. Please try again later.")
            return redirect("contact")

        messages.error(request, "Please fill in all fields.")

    return render(request, "core/contact.html")