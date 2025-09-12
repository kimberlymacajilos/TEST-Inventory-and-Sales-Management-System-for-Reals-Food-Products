from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProductInventory, RawMaterialInventory, Notifications
from django.utils.timezone import now

@receiver(post_save, sender=ProductInventory)
def check_product_stock(sender, instance, **kwargs):
    if instance.total_stock <= instance.restock_threshold:
        Notifications.objects.create(
            item_type="PRODUCT",
            item_id=instance.product.id,
            notification_type="LOW_STOCK",
            notification_timestamp=now()
        )

@receiver(post_save, sender=RawMaterialInventory)
def check_raw_material_stock(sender, instance, **kwargs):
    if instance.total_stock <= instance.reorder_threshold:
        Notifications.objects.create(
            item_type="RAW_MATERIAL",
            item_id=instance.material.id,
            notification_type="LOW_STOCK",
            notification_timestamp=now()
        )
