from django.urls import path
from .views import (
    health,
    list_products,
    product_detail,
    get_cart,
    add_cart_item,
    update_cart_item,
    remove_cart_item,
    checkout,
)

urlpatterns = [
    path('health/', health, name='Health'),

    # Products
    path('products/', list_products, name='ProductList'),
    path('products/<int:pk>/', product_detail, name='ProductDetail'),

    # Cart
    path('cart/', get_cart, name='CartGet'),
    path('cart/items/', add_cart_item, name='CartItemAdd'),
    path('cart/items/<int:item_id>/', update_cart_item, name='CartItemUpdate'),
    path('cart/items/<int:item_id>/remove/', remove_cart_item, name='CartItemRemove'),

    # Orders
    path('orders/checkout/', checkout, name='Checkout'),
]
