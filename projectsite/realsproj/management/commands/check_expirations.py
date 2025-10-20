from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from django.db.models import F
from realsproj.models import (
    ProductBatches, Products, ProductInventory,
    RawMaterialBatches, RawMaterials, RawMaterialInventory,
    Notifications
)

class Command(BaseCommand):
    help = "Check expired and about-to-expire products/raw materials, create notifications, and deduct expired quantities."

    def handle(self, *args, **options):
        today = date.today()

        processed_product_batches = set(
            Notifications.objects.filter(
                notification_type="EXPIRATION_ALERT",
                item_type="PRODUCT"
            ).values_list('item_id', flat=True)
        )
        processed_material_batches = set(
            Notifications.objects.filter(
                notification_type="EXPIRATION_ALERT",
                item_type="RAW_MATERIAL"
            ).values_list('item_id', flat=True)
        )

        Notifications.objects.filter(notification_type="EXPIRATION_ALERT").delete()

        for batch in ProductBatches.objects.select_related(
            "product__product_type",
            "product__variant",
            "product__size_unit",
            "product__size"
        ).filter(is_archived=False):
            if not batch.expiration_date:
                continue

            product = batch.product
            delta_days = (batch.expiration_date - today).days
            qty = int(batch.quantity or 0)

            if qty <= 0:
                continue

            if delta_days < 0:
                note_type = "expired"

                if batch.id not in processed_product_batches:
                    try:
                        inventory = ProductInventory.objects.get(product=product)
                        inventory.total_stock = F('total_stock') - qty
                        inventory.save(update_fields=["total_stock"])
                        print(f"Deducted {qty} from {product} inventory")
                    except ProductInventory.DoesNotExist:
                        print(f"Warning: No inventory record for {product}")
                else:
                    print(f"Batch {batch.id} already processed, skipping deduction")
            elif delta_days == 0:
                note_type = "today"
            elif delta_days <= 7:
                note_type = "week"
            elif delta_days <= 30:
                note_type = "month"
            else:
                continue

            Notifications.objects.create(
                item_type="PRODUCT",
                item_id=batch.id,
                notification_type="EXPIRATION_ALERT",
                notification_timestamp=timezone.now(),
                is_read=False,
            )


            if note_type == "expired":
                print(f"{qty} {product} has expired ({batch.expiration_date})")
            elif note_type == "today":
                print(f"{qty} {product} expires today")
            elif note_type == "week":
                print(f"{qty} {product} will expire in a week ({batch.expiration_date})")
            elif note_type == "month":
                print(f"{qty} {product} will expire in a month ({batch.expiration_date})")

        for batch in RawMaterialBatches.objects.select_related("material").filter(is_archived=False):
            if not batch.expiration_date:
                continue

            material = batch.material
            delta_days = (batch.expiration_date - today).days
            qty = float(batch.quantity or 0)

            if qty <= 0:
                continue

            if delta_days < 0:
                note_type = "expired"

                if batch.id not in processed_material_batches:
                    try:
                        inventory = RawMaterialInventory.objects.get(material=material)
                        inventory.total_stock = F('total_stock') - qty
                        inventory.save(update_fields=["total_stock"])
                        print(f"Deducted {qty} from {material.name} inventory")
                    except RawMaterialInventory.DoesNotExist:
                        print(f"Warning: No inventory record for {material.name}")
                else:
                    print(f"Batch {batch.id} already processed, skipping deduction")
            elif delta_days == 0:
                note_type = "today"
            elif delta_days <= 7:
                note_type = "week"
            elif delta_days <= 30:
                note_type = "month"
            else:
                continue

            Notifications.objects.create(
                item_type="RAW_MATERIAL",
                item_id=batch.id,
                notification_type="EXPIRATION_ALERT",
                notification_timestamp=timezone.now(),
                is_read=False,
            )


            if note_type == "expired":
                print(f"{qty} {material.name} has expired ({batch.expiration_date})")
            elif note_type == "today":
                print(f"{qty} {material.name} expires today")
            elif note_type == "week":
                print(f"{qty} {material.name} will expire in a week ({batch.expiration_date})")
            elif note_type == "month":
                print(f"{qty} {material.name} will expire in a month ({batch.expiration_date})")

        self.stdout.write("Expiration check complete.")
