from django.core.management.base import BaseCommand
from api.models import Product


class Command(BaseCommand):
    help = "Seed demo products for the shop"

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write(self.style.WARNING("Products already exist. Skipping seed."))
            return
        items = [
            {"name": "Ocean Breeze Tee", "sku": "TEE-OCEAN-001", "description": "Soft cotton tee with ocean vibes.", "price": 24.99, "image_url": "https://picsum.photos/seed/tee/600/400"},
            {"name": "Amber Glow Hoodie", "sku": "HOOD-AMBER-002", "description": "Cozy hoodie with amber accents.", "price": 49.00, "image_url": "https://picsum.photos/seed/hood/600/400"},
            {"name": "Blue Wave Bottle", "sku": "BOTTLE-BLUE-003", "description": "Insulated bottle for all adventures.", "price": 19.95, "image_url": "https://picsum.photos/seed/bottle/600/400"},
            {"name": "Seaside Backpack", "sku": "BAG-SEA-004", "description": "Durable backpack with modern design.", "price": 79.50, "image_url": "https://picsum.photos/seed/bag/600/400"},
        ]
        created = 0
        for it in items:
            Product.objects.create(**it)
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} products."))
