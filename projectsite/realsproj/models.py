# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db.models import Sum
from django.db.models import Q
from datetime import timedelta


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'

    def __str__(self):
        return self.username


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Expenses(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'expenses'

    def __str__(self):
        return f"{self.category} - ₱{self.amount} on {self.date.strftime('%Y-%m-%d')}"


class ExpensesSummary(models.Model):
    id = models.BigIntegerField(primary_key=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'expenses_summary'


class HistoryLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(AuthUser, models.DO_NOTHING)
    log_type = models.ForeignKey('HistoryLogTypes', models.DO_NOTHING)
    log_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'history_log'


class HistoryLogTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.CharField(max_length=100)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'history_log_types'

    def __str__(self):
        return self.category

class Notifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    item_type = models.CharField(max_length=12)
    item_id = models.BigIntegerField()
    notification_type = models.CharField(max_length=20)
    notification_timestamp = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) 
    
    class Meta:
        managed = False
        db_table = 'notifications'

    @property
    def css_class(self):
        notif_type = self.notification_type.upper()
        if notif_type == "LOW_STOCK":
            return "notif-warning"
        return "notif-info"

    @property
    def icon_class(self):
        notif_type = self.notification_type.upper()
        if notif_type == "LOW_STOCK":
            return "la la-exclamation-circle"
        return "la la-info-circle"

    @property
    def formatted_message(self):
        notif_type = self.notification_type.upper()

        if self.item_type.upper() == "PRODUCT":
            try:
                product = Products.objects.get(pk=self.item_id)
                product_name = str(product)
            except Products.DoesNotExist:
                product_name = "Unknown Product"

            if notif_type == "LOW_STOCK":
                return f"LOW STOCK: {product_name}"
            elif notif_type == "OUT_OF_STOCK":
                return f"OUT OF STOCK: {product_name}"
            elif notif_type == "STOCK_HEALTHY":
                return f"Stock back to healthy: {product_name}"

        elif self.item_type.upper() == "RAW_MATERIAL":
            try:
                material = RawMaterials.objects.get(pk=self.item_id)
                material_name = str(material)
            except RawMaterials.DoesNotExist:
                material_name = "Unknown Raw Material"

            if notif_type == "LOW_STOCK":
                return f"LOW STOCK: {material_name}"
            elif notif_type == "OUT_OF_STOCK":
                return f"OUT OF STOCK: {material_name}"
            elif notif_type == "STOCK_HEALTHY":
                return f"Stock back to healthy: {material_name}"

        # fallback
        return f"{self.notification_type.upper()} ({self.item_type.title()})"


class ProductBatches(models.Model):
    id = models.BigAutoField(primary_key=True)
    batch_date = models.DateTimeField(default=timezone.now)
    product = models.ForeignKey('Products', models.DO_NOTHING)
    quantity = models.IntegerField()
    manufactured_date = models.DateTimeField(default=timezone.now)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)
    expiration_date = models.DateField(blank=True, null=True)
    deduct_raw_material = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'product_batches'


class ProductInventory(models.Model):
    product = models.OneToOneField('Products', models.DO_NOTHING, primary_key=True)
    total_stock = models.DecimalField(max_digits=10, decimal_places=2)
    restock_threshold = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_inventory'


class ProductRecipes(models.Model):
    id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey('Products', models.DO_NOTHING)
    material_id = models.BigIntegerField()
    quantity_needed = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)
    yield_factor = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_recipes'


class ProductTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_types'

    def __str__(self):
        return self.name


class ProductVariants(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_variants'

    def __str__(self):
        return self.name


class Products(models.Model):
    id = models.BigAutoField(primary_key=True)
    product_type = models.ForeignKey(ProductTypes, models.DO_NOTHING)
    variant = models.ForeignKey(ProductVariants, models.DO_NOTHING)
    size_unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    unit_price = models.ForeignKey('UnitPrices', models.DO_NOTHING)
    srp_price = models.ForeignKey('SrpPrices', models.DO_NOTHING)
    description = models.TextField(blank=True, null=True)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)
    date_created = models.DateTimeField(default=timezone.now)
    size = models.ForeignKey('Sizes', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'

    def __str__(self):
        return f"{self.product_type.name} - {self.variant.name} ({self.size} {self.size_unit.unit_name})"


class RawMaterialBatches(models.Model):
    id = models.BigAutoField(primary_key=True)
    material = models.ForeignKey('RawMaterials', models.DO_NOTHING)
    batch_date = models.DateTimeField(default=timezone.now)
    received_date = models.DateTimeField(default=timezone.now)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    expiration_date = models.DateField(blank=True, null=True)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'raw_material_batches'


class RawMaterialInventory(models.Model):
    material = models.OneToOneField('RawMaterials', models.DO_NOTHING, primary_key=True)
    total_stock = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_threshold = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'raw_material_inventory'


class RawMaterials(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=45)
    unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)
    expiration_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_materials'

    def __str__(self):
        return f"{self.name} ({self.unit}) - ₱{self.price_per_unit}"


class Sales(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'sales'

    def __str__(self):
        return f"{self.category} - ₱{self.amount} on {self.date.strftime('%Y-%m-%d')}"


class SalesSummary(models.Model):
    id = models.BigIntegerField(primary_key=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'sales_summary'


class SizeUnits(models.Model):
    id = models.BigAutoField(primary_key=True)
    unit_name = models.CharField(max_length=45)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'size_units'

    def __str__(self):
        return self.unit_name


class Sizes(models.Model):
    id = models.BigAutoField(primary_key=True)
    size_label = models.CharField(max_length=255)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'sizes'

    def __str__(self):
        return self.size_label


class SrpPrices(models.Model):
    id = models.BigAutoField(primary_key=True)
    srp_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'srp_prices'

    def __str__(self):
        return f"₱{self.srp_price}"


class StockChanges(models.Model):
    id = models.BigAutoField(primary_key=True)
    item_type = models.CharField(max_length=12)
    item_id = models.BigIntegerField()
    quantity_change = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.TextField()
    date = models.DateTimeField()
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'stock_changes'

    def get_item(self):
        if not self.item_type:
            return None

        item_type = self.item_type.strip().lower()

        if item_type in ("raw", "raw_material", "rawmaterials"):
            return RawMaterials.objects.filter(id=self.item_id).first()
        elif item_type in ("product", "products"):
            return Products.objects.filter(id=self.item_id).first()
        return None

    @property
    def item_display(self):
        """Human-readable item representation."""
        item = self.get_item()
        if item:
            return str(item)
        return f"[{self.item_type}] Unknown Item (ID: {self.item_id})"

    def __str__(self):
        return self.item_display


class UnitPrices(models.Model):
    id = models.BigAutoField(primary_key=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'unit_prices'

    def __str__(self):
        return f"₱{self.unit_price}"


class UserProfile(models.Model):
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        default='profile_pics/default.png'
    )

    class Meta:
        managed = False
        db_table = 'user_profile' 


class Withdrawals(models.Model):
    id = models.BigAutoField(primary_key=True)
    ITEM_TYPE_CHOICES = [
        ('PRODUCT', 'Product'),
        ('RAW_MATERIAL', 'Raw Material'),
    ]
    item_type = models.CharField(max_length=12, choices=ITEM_TYPE_CHOICES)
    item_id = models.BigIntegerField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    REASON_CHOICES = [
        ('SOLD', 'Sold'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
        ('RETURNED', 'Returned'),
        ('OTHERS', 'Others'),
    ]
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    created_by_admin = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column="created_by_admin_id")
    class Meta:
        managed = False
        db_table = 'withdrawals'

    def __str__(self):
        return f"{self.item_type} {self.item_id} - {self.quantity}"

    def get_item_display(self):
        if self.item_type == "PRODUCT":
            from .models import Products  
            try:
                product = Products.objects.get(id=self.item_id)
                return str(product) 
            except Products.DoesNotExist:
                return f"Unknown Product (ID {self.item_id})"

        elif self.item_type == "RAW_MATERIAL":
            from .models import RawMaterials
            try:
                material = RawMaterials.objects.get(id=self.item_id)
                return str(material) 
            except RawMaterials.DoesNotExist:
                return f"Unknown Material (ID {self.item_id})"

        return f"Unknown Item (ID {self.item_id})"
    
    def compute_revenue(self):
        if self.item_type == "PRODUCT" and self.reason == "SOLD":
            from .models import Products
            try:
                product = Products.objects.get(id=self.item_id)
                return Decimal(self.quantity) * product.srp_price.srp_price
            except Products.DoesNotExist:
                return Decimal(0)
        return Decimal(0)