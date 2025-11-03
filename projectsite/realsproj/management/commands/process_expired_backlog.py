from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F
from django.db import transaction
from realsproj.models import (
    ProductBatches, ProductInventory,
    RawMaterialBatches, RawMaterialInventory,
    Notifications, Withdrawals, AuthUser
)

class Command(BaseCommand):
    help = "One-time command to process already-expired batches that were notified but not deducted from inventory"

    def handle(self, *args, **options):
        today = timezone.localdate()

        try:
            system_user = AuthUser.objects.filter(is_superuser=True).first()
            if not system_user:
                system_user = AuthUser.objects.first()
        except:
            system_user = None
            self.stdout.write(self.style.ERROR("No system user found. Cannot create withdrawals."))
            return

        expired_product_batches = ProductBatches.objects.filter(
            is_archived=False,
            expiration_date__lt=today,
            quantity__gt=0
        ).select_related('product')
        
        product_count = 0
        product_qty_total = 0
        
        with transaction.atomic():
            for batch in expired_product_batches:
                qty = int(batch.quantity or 0)
                
                existing_withdrawal = Withdrawals.objects.filter(
                    item_type="PRODUCT",
                    item_id=batch.product.id,
                    quantity=qty,
                    reason="EXPIRED",
                    date__date=batch.expiration_date
                ).exists()
                
                if existing_withdrawal:
                    self.stdout.write(f"Skipping {batch.product} - withdrawal already exists")
                    continue

                Withdrawals.objects.create(
                    item_type="PRODUCT",
                    item_id=batch.product.id,
                    quantity=qty,
                    reason="EXPIRED",
                    date=batch.expiration_date,
                    created_by_admin=system_user
                )

                try:
                    ProductInventory.objects.filter(product=batch.product).update(
                        total_stock=F('total_stock') - qty
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Processed {qty} {batch.product} (expired {batch.expiration_date})"
                    ))
                    product_count += 1
                    product_qty_total += qty
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"✗ Error processing {batch.product}: {e}"
                    ))
                    continue

                batch.quantity = 0
                batch.is_archived = True
                batch.save(update_fields=['quantity', 'is_archived'])

        expired_material_batches = RawMaterialBatches.objects.filter(
            is_archived=False,
            expiration_date__lt=today,
            quantity__gt=0
        ).select_related('material')
        
        material_count = 0
        material_qty_total = 0
        
        with transaction.atomic():
            for batch in expired_material_batches:
                qty = float(batch.quantity or 0)

                existing_withdrawal = Withdrawals.objects.filter(
                    item_type="RAW_MATERIAL",
                    item_id=batch.material.id,
                    quantity=qty,
                    reason="EXPIRED",
                    date__date=batch.expiration_date
                ).exists()
                
                if existing_withdrawal:
                    self.stdout.write(f"Skipping {batch.material.name} - withdrawal already exists")

                Withdrawals.objects.create(
                    item_type="RAW_MATERIAL",
                    item_id=batch.material.id,
                    quantity=qty,
                    reason="EXPIRED",
                    date=batch.expiration_date,
                    created_by_admin=system_user
                )

                try:
                    RawMaterialInventory.objects.filter(material=batch.material).update(
                        total_stock=F('total_stock') - qty
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Processed {qty} {batch.material.name} (expired {batch.expiration_date})"
                    ))
                    material_count += 1
                    material_qty_total += qty
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"✗ Error processing {batch.material.name}: {e}"
                    ))
                    continue
                
                batch.quantity = 0
                batch.is_archived = True
                batch.save(update_fields=['quantity', 'is_archived'])
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("BACKLOG PROCESSING COMPLETE"))
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(f"Products processed: {product_count} batches ({product_qty_total} units)")
        self.stdout.write(f"Raw materials processed: {material_count} batches ({material_qty_total} units)")
        self.stdout.write(self.style.SUCCESS("="*60))
