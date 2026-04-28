from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Product, Wishlist

@receiver(user_logged_in)
def merge_session_wishlist_on_login(sender, user, request, **kwargs):
    """
    When a guest logs in or registers, check their session for a wishlist.
    If they saved items as a guest, automatically add them to their permanent Wishlist.
    """
    session_wishlist = request.session.get('wishlist', [])
    
    if session_wishlist:
        for product_id in session_wishlist:
            try:
                product = Product.objects.get(id=product_id)
                Wishlist.objects.get_or_create(user=user, product=product)
            except Product.DoesNotExist:
                continue
                
        # Clear the session wishlist after merging
        request.session['wishlist'] = []
        request.session.modified = True
