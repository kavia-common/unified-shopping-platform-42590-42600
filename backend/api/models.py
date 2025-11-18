from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base with created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(TimeStampedModel):
    """A product available for sale."""
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"


class Cart(TimeStampedModel):
    """A shopping cart identified by a client-side cart_id (UUID string)."""
    cart_id = models.CharField(max_length=64, unique=True)

    def __str__(self) -> str:
        return f"Cart {self.cart_id}"

    @property
    def total_amount(self):
        return sum([item.subtotal for item in self.items.all()])


class CartItem(TimeStampedModel):
    """An item within a cart referring to a product and quantity."""
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

    @property
    def subtotal(self):
        return float(self.product.price) * self.quantity


class Order(TimeStampedModel):
    """A placed order derived from a cart."""
    order_number = models.CharField(max_length=32, unique=True)
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2)
    postal_code = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"Order #{self.order_number}"


class OrderItem(TimeStampedModel):
    """Line item of an order with captured price and quantity."""
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=64)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return float(self.unit_price) * self.quantity
