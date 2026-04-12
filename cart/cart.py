from .models import CartItem
from store.models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        cart = self.session.get("cart")

        if not cart:
            cart = self.session["cart"] = {}
        
        self.cart = cart

        # ✅ SYNC DB TO SESSION IF LOGGED IN
        if request.user.is_authenticated:
            self.sync_db_to_session()

    def sync_db_to_session(self):
        """Load items from DB into session if they are not already there."""
        db_items = CartItem.objects.filter(user=self.request.user)
        changes = False
        
        for db_item in db_items:
            product_id = str(db_item.product.id)
            if product_id not in self.cart:
                self.cart[product_id] = {
                    "name": db_item.product.name,
                    "price": float(db_item.product.price),
                    "quantity": db_item.quantity,
                    "image": db_item.product.image.url if db_item.product.image else "",
                }
                changes = True
            else:
                # If quantity in session is different from DB, we might want to sync, 
                # but usually the session is the "active" state.
                # However, for the very first load, we trust the DB.
                pass
        
        if changes:
            self.save()

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {
                "name": product.name,
                "price": float(product.price),
                "quantity": 0,
                "image": product.image.url if product.image else "",
            }

        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity

        self.save()

        # ✅ SYNC TO DB
        if self.request.user.is_authenticated:
            item, created = CartItem.objects.get_or_create(
                user=self.request.user,
                product=product
            )
            if override_quantity:
                item.quantity = quantity
            else:
                item.quantity = self.cart[product_id]["quantity"]
            item.save()

    def remove(self, product):
        product_id = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

        # ✅ SYNC TO DB
        if self.request.user.is_authenticated:
            CartItem.objects.filter(user=self.request.user, product=product).delete()

    def decrease(self, product):
        product_id = str(product.id)

        if product_id in self.cart:
            self.cart[product_id]["quantity"] -= 1

            if self.cart[product_id]["quantity"] <= 0:
                del self.cart[product_id]
                if self.request.user.is_authenticated:
                    CartItem.objects.filter(user=self.request.user, product=product).delete()
            else:
                if self.request.user.is_authenticated:
                    item = CartItem.objects.get(user=self.request.user, product=product)
                    item.quantity = self.cart[product_id]["quantity"]
                    item.save()

            self.save()

    def clear(self):
        """Remove cart from session and DB."""
        if self.request.user.is_authenticated:
            CartItem.objects.filter(user=self.request.user).delete()
        
        self.session["cart"] = {}
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        for product_id, item in self.cart.items():
            yield {
                "id": product_id,
                "name": item["name"],
                "price": item["price"],
                "quantity": item["quantity"],
                "image": item.get("image", ""),
                "total": item["price"] * item["quantity"],
            }

    def get_total_price(self):
        return sum(
            item["price"] * item["quantity"]
            for item in self.cart.values()
        )

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())
    
    