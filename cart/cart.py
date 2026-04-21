from .models import CartItem
from store.models import Product, Variation

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
            # Create a unique key based on product ID and sorted variation IDs
            variation_ids = sorted([v.id for v in db_item.variations.all()])
            item_key = f"{db_item.product.id}_{'-'.join(map(str, variation_ids))}"

            if item_key not in self.cart:
                # Calculate modified price
                base_price = float(db_item.product.price)
                modifiers = sum(float(v.price_modifier) for v in db_item.variations.all())
                total_unit_price = base_price + modifiers

                self.cart[item_key] = {
                    "product_id": str(db_item.product.id),
                    "name": db_item.product.name,
                    "price": total_unit_price,
                    "quantity": db_item.quantity,
                    "image": db_item.product.image.url if db_item.product.image else "",
                    "variation_ids": variation_ids,
                    "variation_names": [f"{v.category.name}: {v.value}" for v in db_item.variations.all()],
                }
                changes = True
        
        if changes:
            self.save()

    def add(self, product, quantity=1, override_quantity=False, variations=None):
        """
        variations: a list of Variation objects
        """
        variation_ids = sorted([v.id for v in variations]) if variations else []
        item_key = f"{product.id}_{'-'.join(map(str, variation_ids))}"

        if item_key not in self.cart:
            # Calculate modified price
            base_price = float(product.price)
            modifiers = sum(float(v.price_modifier) for v in variations) if variations else 0
            total_unit_price = base_price + modifiers

            self.cart[item_key] = {
                "product_id": str(product.id),
                "name": product.name,
                "price": total_unit_price,
                "quantity": 0,
                "image": product.image.url if product.image else "",
                "variation_ids": variation_ids,
                "variation_names": [f"{v.category.name}: {v.value}" for v in variations] if variations else [],
            }

        if override_quantity:
            self.cart[item_key]["quantity"] = quantity
        else:
            self.cart[item_key]["quantity"] += quantity

        self.save()

        # ✅ SYNC TO DB
        if self.request.user.is_authenticated:
            # Find item with EXACT variations
            # This istricky in Django with ManyToMany, so we filter by product and user, 
            # then check the variations set.
            items = CartItem.objects.filter(user=self.request.user, product=product)
            found_item = None
            for item in items:
                item_var_ids = sorted([v.id for v in item.variations.all()])
                if item_var_ids == variation_ids:
                    found_item = item
                    break
            
            if found_item:
                if override_quantity:
                    found_item.quantity = quantity
                else:
                    found_item.quantity += quantity
                found_item.save()
            else:
                new_item = CartItem.objects.create(
                    user=self.request.user,
                    product=product,
                    quantity=quantity
                )
                if variations:
                    new_item.variations.set(variations)
                    new_item.save()

    def remove(self, product_key):
        """Removes an item using its unique key (id_vars)"""
        if product_key in self.cart:
            if self.request.user.is_authenticated:
                # Find DB item to delete
                cart_item_data = self.cart[product_key]
                p_id = cart_item_data["product_id"]
                var_ids = cart_item_data["variation_ids"]
                
                items = CartItem.objects.filter(user=self.request.user, product_id=p_id)
                for item in items:
                    if sorted([v.id for v in item.variations.all()]) == var_ids:
                        item.delete()
                        break

            del self.cart[product_key]
            self.save()

    def decrease(self, product_key):
        if product_key in self.cart:
            self.cart[product_key]["quantity"] -= 1

            if self.cart[product_key]["quantity"] <= 0:
                self.remove(product_key)
            else:
                if self.request.user.is_authenticated:
                    cart_item_data = self.cart[product_key]
                    items = CartItem.objects.filter(user=self.request.user, product_id=cart_item_data["product_id"])
                    for item in items:
                        if sorted([v.id for v in item.variations.all()]) == cart_item_data["variation_ids"]:
                            item.quantity = self.cart[product_key]["quantity"]
                            item.save()
                            break
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
        """
        Loop through cart items in session and fetch products if needed.
        We return variation names so templates can display them.
        """
        for item_key, item in self.cart.items():
            yield {
                "key": item_key,
                "id": item["product_id"],
                "name": item["name"],
                "price": item["price"],
                "quantity": item["quantity"],
                "image": item.get("image", ""),
                "variations": item.get("variation_names", []),
                "total": item["price"] * item["quantity"],
            }

    def get_total_price(self):
        return sum(
            item["price"] * item["quantity"]
            for item in self.cart.values()
        )

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())
    
    