from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import CartItem
from store.models import Product

@receiver(user_logged_in)
def merge_cart_on_login(sender, user, request, **kwargs):
    """
    When a user logs in, take items from the guest session cart 
    and save them to the persistent CartItem model.
    """
    session_cart = request.session.get('cart', {})
    
    if session_cart:
        for product_id, item_data in session_cart.items():
            try:
                product = Product.objects.get(id=int(product_id))
                cart_item, created = CartItem.objects.get_or_create(
                    user=user,
                    product=product
                )
                
                if created:
                    cart_item.quantity = item_data['quantity']
                else:
                    # Merge quantities
                    cart_item.quantity += item_data['quantity']
                
                cart_item.save()
            except Product.DoesNotExist:
                continue
        
        # Optionally clear session cart or let it be 'synced' by the Cart class later
        # We'll clear it so that Cart.__init__ loads a fresh state from DB
        request.session['cart'] = {}
        request.session.modified = True