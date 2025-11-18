from typing import List
import random
import string
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.renderers import JSONRenderer
from .models import Product, Cart, CartItem, Order, OrderItem


# PUBLIC_INTERFACE
@api_view(['GET'])
@renderer_classes([JSONRenderer])
def health(request):
    """Health check for the service.
    Returns:
        200 with {"message":"Server is up!"}
    """
    return Response({"message": "Server is up!"})


# Serializers

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product entity."""
    class Meta:
        model = Product
        fields = ["id", "name", "sku", "description", "price", "image_url", "created_at", "updated_at"]


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items including product nested summary."""
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )
    subtotal = serializers.SerializerMethodField()

    def get_subtotal(self, obj: CartItem) -> float:
        return obj.subtotal

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart with items and computed total."""
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    def get_total_amount(self, obj: Cart) -> float:
        return obj.total_amount

    class Meta:
        model = Cart
        fields = ["cart_id", "items", "total_amount", "created_at", "updated_at"]


class CheckoutItemInputSerializer(serializers.Serializer):
    """Item input for checkout."""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    """Checkout input serializer for creating an order."""
    cart_id = serializers.CharField(max_length=64)
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=2)
    postal_code = serializers.CharField(max_length=20)


def _get_or_create_cart(cart_id: str) -> Cart:
    """Internal helper to fetch or create a cart."""
    cart, _ = Cart.objects.get_or_create(cart_id=cart_id)
    return cart


# PUBLIC_INTERFACE
@api_view(["GET"])
def list_products(request):
    """List products
    ---
    summary: List all products
    description: Returns a list of products available for sale.
    tags:
      - products
    responses:
      200:
        description: List of products
    """
    qs = Product.objects.all().order_by("-created_at")
    serializer = ProductSerializer(qs, many=True)
    return Response(serializer.data)


# PUBLIC_INTERFACE
@api_view(["GET"])
def product_detail(request, pk: int):
    """Retrieve product detail
    ---
    summary: Get a single product
    description: Returns details for a product by id.
    tags:
      - products
    parameters:
      - name: id
        in: path
        description: Product ID
        required: true
        type: integer
    responses:
      200:
        description: Product detail
    """
    obj = get_object_or_404(Product, pk=pk)
    serializer = ProductSerializer(obj)
    return Response(serializer.data)


# PUBLIC_INTERFACE
@api_view(["GET"])
def get_cart(request):
    """Get cart by cart_id
    ---
    summary: Get cart
    description: Returns the current cart by `cart_id` query parameter.
    tags:
      - cart
    parameters:
      - name: cart_id
        in: query
        description: Client cart id (uuid-like string)
        required: true
        type: string
    responses:
      200:
        description: Cart object
      400:
        description: Missing cart_id
    """
    cart_id = request.query_params.get("cart_id")
    if not cart_id:
        return Response({"detail": "cart_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    cart = _get_or_create_cart(cart_id)
    return Response(CartSerializer(cart).data)


# PUBLIC_INTERFACE
@api_view(["POST"])
def add_cart_item(request):
    """Add item to cart
    ---
    summary: Add item to cart
    description: Adds a product to the cart or increases quantity if it exists.
    tags:
      - cart
    requestBody:
      required: true
    responses:
      200:
        description: Updated cart
      400:
        description: Validation error
    """
    class AddItemSerializer(serializers.Serializer):
        cart_id = serializers.CharField(max_length=64)
        product_id = serializers.IntegerField()
        quantity = serializers.IntegerField(min_value=1, default=1)

    serializer = AddItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    cart = _get_or_create_cart(serializer.validated_data["cart_id"])
    product = get_object_or_404(Product, id=serializer.validated_data["product_id"])
    qty = serializer.validated_data["quantity"]

    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": qty})
    if not created:
        item.quantity += qty
        item.save(update_fields=["quantity", "updated_at"])

    return Response(CartSerializer(cart).data)


# PUBLIC_INTERFACE
@api_view(["PATCH"])
def update_cart_item(request, item_id: int):
    """Update a cart item quantity
    ---
    summary: Update cart item
    description: Updates the quantity of a cart item.
    tags:
      - cart
    parameters:
      - name: item_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Updated cart
    """
    class UpdateItemSerializer(serializers.Serializer):
        cart_id = serializers.CharField(max_length=64)
        quantity = serializers.IntegerField(min_value=1)

    serializer = UpdateItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    cart_id = serializer.validated_data["cart_id"]
    cart = _get_or_create_cart(cart_id)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.quantity = serializer.validated_data["quantity"]
    item.save(update_fields=["quantity", "updated_at"])
    return Response(CartSerializer(cart).data)


# PUBLIC_INTERFACE
@api_view(["DELETE"])
def remove_cart_item(request, item_id: int):
    """Remove item from cart
    ---
    summary: Remove cart item
    description: Removes an item from the cart by item id.
    tags:
      - cart
    parameters:
      - name: item_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Updated cart
    """
    cart_id = request.query_params.get("cart_id")
    if not cart_id:
        return Response({"detail": "cart_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    cart = _get_or_create_cart(cart_id)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return Response(CartSerializer(cart).data)


def _generate_order_number() -> str:
    return ''.join(random.choices(string.digits, k=8))


# PUBLIC_INTERFACE
@api_view(["POST"])
@transaction.atomic
def checkout(request):
    """Create an order from the cart
    ---
    summary: Checkout
    description: Creates an order from the cart and clears the cart.
    tags:
      - orders
    requestBody:
      required: true
    responses:
      201:
        description: Order created
    """
    serializer = CheckoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    cart = _get_or_create_cart(data["cart_id"])
    if cart.items.count() == 0:
        return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    total = sum([item.product.price * item.quantity for item in cart.items.all()])
    order = Order.objects.create(
        order_number=_generate_order_number(),
        email=data["email"],
        full_name=data["full_name"],
        address_line1=data["address_line1"],
        address_line2=data.get("address_line2", ""),
        city=data["city"],
        country=data["country"],
        postal_code=data["postal_code"],
        total_amount=total,
    )
    # Create order items
    order_items: List[OrderItem] = []
    for item in cart.items.select_related("product").all():
        order_items.append(OrderItem(
            order=order,
            product=item.product,
            product_name=item.product.name,
            product_sku=item.product.sku,
            unit_price=item.product.price,
            quantity=item.quantity,
        ))
    OrderItem.objects.bulk_create(order_items)

    # clear cart
    cart.items.all().delete()

    return Response({
        "order_number": order.order_number,
        "total_amount": str(order.total_amount),
        "items": [{
            "product_name": oi.product_name,
            "sku": oi.product_sku,
            "unit_price": str(oi.unit_price),
            "quantity": oi.quantity,
            "subtotal": oi.quantity * float(oi.unit_price),
        } for oi in order.items.all()]
    }, status=status.HTTP_201_CREATED)
