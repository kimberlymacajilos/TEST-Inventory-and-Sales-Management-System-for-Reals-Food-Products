from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F, Sum, Q
from django.db import transaction
from collections import defaultdict
from realsproj.models import (
    ProductBatches, Products, ProductInventory,
    RawMaterialBatches, RawMaterials, RawMaterialInventory,
    Notifications, Withdrawals, AuthUser
)

class Command(BaseCommand):
    help = "Check expired and about-to-expire products/raw materials, create notifications, and deduct expired quantities."

    def handle(self, *args, **options):
        today = timezone.localdate()
        
        # Get existing expiration notifications to track what's already been notified
        existing_notifications = set(
            Notifications.objects.filter(
                notification_type="EXPIRATION_ALERT"
            ).values_list('item_type', 'item_id')
        )
        
        # Dictionaries to group notifications by product/material and expiration status
        product_notifications = defaultdict(lambda: defaultdict(list))
        material_notifications = defaultdict(lambda: defaultdict(list))
        
        # Get system user for auto-withdrawals (use first admin or create system user)
        try:
            system_user = AuthUser.objects.filter(is_superuser=True).first()
            if not system_user:
                system_user = AuthUser.objects.first()
        except:
            system_user = None

        # Process Product Batches
        product_batches = ProductBatches.objects.select_related(
            "product__product_type",
            "product__variant",
            "product__size_unit",
            "product__size"
        ).filter(
            is_archived=False,
            expiration_date__isnull=False,
            quantity__gt=0
        )
        
        for batch in product_batches:
            product = batch.product
            delta_days = (batch.expiration_date - today).days
            qty = int(batch.quantity or 0)
            
            # Determine notification type
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
            
            # Check if this batch was already notified
            batch_key = ('PRODUCT', batch.id)
            if batch_key in existing_notifications:
                continue
            
            # Group by product and notification type
            product_key = str(product)
            product_notifications[product_key][note_type].append({
                'batch': batch,
                'qty': qty,
                'exp_date': batch.expiration_date
            })
        
        # Create grouped notifications and handle expired items
        with transaction.atomic():
            for product_name, status_dict in product_notifications.items():
                for note_type, items in status_dict.items():
                    total_qty = sum(item['qty'] for item in items)
                    exp_dates = sorted(set(item['exp_date'] for item in items))
                    
                    # Create notification for each batch
                    for item in items:
                        Notifications.objects.create(
                            item_type="PRODUCT",
                            item_id=item['batch'].id,
                            notification_type="EXPIRATION_ALERT",
                            notification_timestamp=timezone.now(),
                            is_read=False,
                        )
                    
                    # Handle expired items - create withdrawal and deduct from inventory
                    if note_type == "expired":
                        for item in items:
                            batch = item['batch']
                            qty = item['qty']
                            
                            # Create withdrawal record for financial loss tracking
                            if system_user:
                                Withdrawals.objects.create(
                                    item_type="PRODUCT",
                                    item_id=batch.product.id,
                                    quantity=qty,
                                    reason="EXPIRED",
                                    date=today,
                                    created_by_admin=system_user
                                )
                            
                            # Deduct from inventory
                            try:
                                ProductInventory.objects.filter(product=batch.product).update(
                                    total_stock=F('total_stock') - qty
                                )
                                self.stdout.write(f"Deducted {qty} from {batch.product} inventory")
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"Error deducting inventory for {batch.product}: {e}"))
                            
                            # Set batch quantity to 0 and archive
                            batch.quantity = 0
                            batch.is_archived = True
                            batch.save(update_fields=['quantity', 'is_archived'])
                        
                        self.stdout.write(self.style.SUCCESS(
                            f"{total_qty} {product_name} has expired ({', '.join(str(d) for d in exp_dates)})"
                        ))
                    elif note_type == "today":
                        self.stdout.write(f"{total_qty} {product_name} expires today")
                    elif note_type == "week":
                        self.stdout.write(f"{total_qty} {product_name} will expire in a week")
                    elif note_type == "month":
                        self.stdout.write(f"{total_qty} {product_name} will expire in a month")

        # Process Raw Material Batches
        material_batches = RawMaterialBatches.objects.select_related(
            "material"
        ).filter(
            is_archived=False,
            expiration_date__isnull=False,
            quantity__gt=0
        )
        
        for batch in material_batches:
            material = batch.material
            delta_days = (batch.expiration_date - today).days
            qty = float(batch.quantity or 0)
            
            # Determine notification type
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
            
            # Check if this batch was already notified
            batch_key = ('RAW_MATERIAL', batch.id)
            if batch_key in existing_notifications:
                continue
            
            # Group by material and notification type
            material_key = material.name
            material_notifications[material_key][note_type].append({
                'batch': batch,
                'qty': qty,
                'exp_date': batch.expiration_date
            })
        
        # Create grouped notifications and handle expired items
        with transaction.atomic():
            for material_name, status_dict in material_notifications.items():
                for note_type, items in status_dict.items():
                    total_qty = sum(item['qty'] for item in items)
                    exp_dates = sorted(set(item['exp_date'] for item in items))
                    
                    # Create notification for each batch
                    for item in items:
                        Notifications.objects.create(
                            item_type="RAW_MATERIAL",
                            item_id=item['batch'].id,
                            notification_type="EXPIRATION_ALERT",
                            notification_timestamp=timezone.now(),
                            is_read=False,
                        )
                    
                    # Handle expired items - create withdrawal and deduct from inventory
                    if note_type == "expired":
                        for item in items:
                            batch = item['batch']
                            qty = item['qty']
                            
                            # Create withdrawal record for financial loss tracking
                            if system_user:
                                Withdrawals.objects.create(
                                    item_type="RAW_MATERIAL",
                                    item_id=batch.material.id,
                                    quantity=qty,
                                    reason="EXPIRED",
                                    date=today,
                                    created_by_admin=system_user
                                )
                            
                            # Deduct from inventory
                            try:
                                RawMaterialInventory.objects.filter(material=batch.material).update(
                                    total_stock=F('total_stock') - qty
                                )
                                self.stdout.write(f"Deducted {qty} from {batch.material.name} inventory")
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"Error deducting inventory for {batch.material.name}: {e}"))
                            
                            # Set batch quantity to 0 and archive
                            batch.quantity = 0
                            batch.is_archived = True
                            batch.save(update_fields=['quantity', 'is_archived'])
                        
                        self.stdout.write(self.style.SUCCESS(
                            f"{total_qty} {material_name} has expired ({', '.join(str(d) for d in exp_dates)})"
                        ))
                    elif note_type == "today":
                        self.stdout.write(f"{total_qty} {material_name} expires today")
                    elif note_type == "week":
                        self.stdout.write(f"{total_qty} {material_name} will expire in a week")
                    elif note_type == "month":
                        self.stdout.write(f"{total_qty} {material_name} will expire in a month")
        
        self.stdout.write(self.style.SUCCESS("Expiration check complete."))
