from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from realsproj.models import (
    ProductBatches, Products,
    RawMaterialBatches, RawMaterials,
    Notifications
)

class Command(BaseCommand):
    help = "Check expired and about-to-expire products/raw materials and create notifications."

    def handle(self, *args, **options):
        today = date.today()

        Notifications.objects.filter(notification_type="EXPIRATION_ALERT").delete()

        for batch in ProductBatches.objects.select_related(
            "product__product_type",
            "product__variant",
            "product__size_unit",
            "product__size"
        ):
            if not batch.expiration_date:
                continue

            product = batch.product
            delta_days = (batch.expiration_date - today).days
            qty = int(batch.quantity or 0)

            if delta_days < 0:
                note_type = "expired"
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

        for batch in RawMaterialBatches.objects.select_related("material"):
            if not batch.expiration_date:
                continue

            material = batch.material
            delta_days = (batch.expiration_date - today).days
            qty = int(batch.quantity or 0)

            if delta_days < 0:
                note_type = "expired"
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
