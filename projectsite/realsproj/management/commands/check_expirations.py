from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F, Sum, Q
from django.db import transaction
from django.contrib.auth.models import User
from collections import defaultdict
from realsproj.models import (
    ProductBatches, Products, ProductInventory,
    RawMaterialBatches, RawMaterials, RawMaterialInventory,
    Notifications, Withdrawals
)

class Command(BaseCommand):
    help = "Check expired and about-to-expire products/raw materials, create notifications, and deduct expired quantities. Matches Supabase cron job logic."

    def handle(self, *args, **options):
        today = timezone.localdate()
        
        try:
            system_user = User.objects.filter(is_superuser=True).first()
            if not system_user:
                system_user = User.objects.first()
        except:
            system_user = None
        
        if not system_user:
            self.stdout.write(self.style.ERROR("No user found to create withdrawals"))
            return

        expired_products_count = 0
        expired_materials_count = 0

        self.stdout.write(self.style.WARNING("Checking product batches..."))
        
        product_batches = ProductBatches.objects.select_related(
            "product__product_type",
            "product__variant",
            "product__size_unit",
            "product__size"
        ).filter(
            Q(is_expired=False) | Q(is_expired__isnull=True),  
            expiration_date__lte=today  
        )
        
        with transaction.atomic():
            for batch in product_batches:
                product = batch.product
                qty = int(batch.quantity or 0)
                
                if qty <= 0:
                    continue

                batch.is_expired = True
                batch.save(update_fields=['is_expired'])
             
                inventory = ProductInventory.objects.filter(product=product).first()
                if inventory:
                    new_stock = max(float(inventory.total_stock) - qty, 0)
                    inventory.total_stock = new_stock
                    inventory.save(update_fields=['total_stock'])
                    self.stdout.write(f"  [OK] Deducted {qty} from {product} (new stock: {new_stock})")

                Withdrawals.objects.create(
                    item_type="PRODUCT",
                    item_id=product.id,
                    quantity=qty,
                    reason="EXPIRED",
                    date=timezone.now(),
                    created_by_admin=system_user
                )

                Notifications.objects.get_or_create(
                    item_type="PRODUCT",
                    item_id=batch.id,
                    notification_type="EXPIRATION_ALERT",
                    defaults={
                        'notification_timestamp': timezone.now(),
                        'is_read': False,
                    }
                )
                
                expired_products_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  [EXPIRED] {qty} {product} (Exp: {batch.expiration_date})"
                ))

        self.stdout.write(self.style.WARNING("\nChecking raw material batches..."))
        
        material_batches = RawMaterialBatches.objects.select_related(
            "material__unit"
        ).filter(
            Q(is_expired=False) | Q(is_expired__isnull=True),
            expiration_date__lte=today 
        )
        
        with transaction.atomic():
            for batch in material_batches:
                material = batch.material
                qty = float(batch.quantity or 0)
                
                if qty <= 0:
                    continue
                
                batch.is_expired = True
                batch.save(update_fields=['is_expired'])
                
                inventory = RawMaterialInventory.objects.filter(material=material).first()
                if inventory:
                    new_stock = max(float(inventory.total_stock) - qty, 0)
                    inventory.total_stock = new_stock
                    inventory.save(update_fields=['total_stock'])
                    self.stdout.write(f"  [OK] Deducted {qty} from {material.name} (new stock: {new_stock})")

                Withdrawals.objects.create(
                    item_type="RAW_MATERIAL",
                    item_id=material.id,
                    quantity=qty,
                    reason="EXPIRED",
                    date=timezone.now(),
                    created_by_admin=system_user
                )
                
                Notifications.objects.get_or_create(
                    item_type="RAW_MATERIAL",
                    item_id=batch.id,
                    notification_type="EXPIRATION_ALERT",
                    defaults={
                        'notification_timestamp': timezone.now(),
                        'is_read': False,
                    }
                )
                
                expired_materials_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  [EXPIRED] {qty} {material.name} (Exp: {batch.expiration_date})"
                ))
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("EXPIRATION CHECK COMPLETE"))
        self.stdout.write("="*70)
        self.stdout.write(f"  Products expired: {expired_products_count}")
        self.stdout.write(f"  Raw materials expired: {expired_materials_count}")
        self.stdout.write(f"  Total expired items: {expired_products_count + expired_materials_count}")
        self.stdout.write("="*70)
