# unified-shopping-platform-42590-42600

Backend (Django REST) and Frontend (Vue) shopping app.

- Backend runs on port 3001 and exposes REST endpoints:
  - GET /api/products/
  - GET /api/products/{id}/
  - GET /api/cart/?cart_id=...
  - POST /api/cart/items/
  - PATCH /api/cart/items/{item_id}/
  - DELETE /api/cart/items/{item_id}/remove/?cart_id=...
  - POST /api/orders/checkout/

Frontend (separate container) expects env var:
- VITE_API_BASE pointing to the backend base (e.g., https://...:3001/api)

Seed demo products:
- python manage.py migrate
- python manage.py seed_products
