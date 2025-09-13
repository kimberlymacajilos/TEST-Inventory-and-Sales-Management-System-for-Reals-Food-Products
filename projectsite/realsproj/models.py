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
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'expenses'

    def __str__(self):
        return f"{self.category} - ₱{self.amount} on {self.date.strftime('%Y-%m-%d')}"


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
    ITEM_TYPE_CHOICES = [
        ('product', 'Product'),
        ('raw_material', 'Raw Material'),
    ]
    item_type = models.CharField(max_length=12, choices=ITEM_TYPE_CHOICES)
    item_id = models.BigIntegerField()
    notification_type = models.CharField(max_length=20)
    notification_timestamp = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'notifications'

    @property
    def formatted_message(self):
        notif_type = self.notification_type.lower()

        if self.item_type.lower() == "product":
            try:
                product = Products.objects.get(pk=self.item_id)
                product_name = str(product)
            except Products.DoesNotExist:
                product_name = "Unknown Product"

            if notif_type in ["out_of_stock"]:
                return f"{product_name} is out of stock"
            elif notif_type in ["stock_alert", "low_stock"]:
                return f"{product_name} is low in stock"

        elif self.item_type.lower() == "raw_material":
            try:
                material = RawMaterials.objects.get(pk=self.item_id)
                material_name = str(material)
            except RawMaterials.DoesNotExist:
                material_name = "Unknown Raw Material"

            if notif_type in ["out_of_stock"]:
                return f"{material_name} is out of stock"
            elif notif_type in ["stock_alert", "low_stock"]:
                return f"{material_name} is low in stock"

        if notif_type == "expiration_alert":
            return f"{self.item_type.capitalize()} (ID {self.item_id}) is nearing expiration"

        return f"{self.notification_type} ({self.item_type})"


class ProductBatches(models.Model):
    id = models.BigAutoField(primary_key=True)
    batch_date = models.DateField()
    product = models.ForeignKey('Products', models.DO_NOTHING)
    quantity = models.IntegerField()
    manufactured_date = models.DateField()
    expiration_date = models.DateField()
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_batches'


class ProductInventory(models.Model):
    product = models.OneToOneField('Products', models.DO_NOTHING, primary_key=True)
    total_stock = models.DecimalField(max_digits=10, decimal_places=2)
    restock_threshold = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'product_inventory'


class ProductRecipes(models.Model):
    id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey('Products', models.DO_NOTHING)
    material = models.ForeignKey('RawMaterials', models.DO_NOTHING)
    quantity_needed = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

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
    size = models.ForeignKey('Sizes', models.DO_NOTHING)
    size_unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    unit_price = models.ForeignKey('UnitPrices', models.DO_NOTHING)
    srp_price = models.ForeignKey('SrpPrices', models.DO_NOTHING)
    date_created = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products'

    def __str__(self):
        return f"{self.product_type.name} - {self.variant.name} ({self.size.size_label} {self.size_unit.unit_name})"

class RawMaterialBatches(models.Model):
    id = models.BigAutoField(primary_key=True)
    batch_date = models.DateField()
    material = models.ForeignKey('RawMaterials', models.DO_NOTHING)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    received_date = models.DateField()
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
    size = models.ForeignKey('Sizes', models.DO_NOTHING)
    unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)
    expiration_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_materials'

    def __str__(self):
        return f"{self.name} ({self.size} {self.unit}) - ₱{self.price_per_unit}"

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


class UnitPrices(models.Model):
    id = models.BigAutoField(primary_key=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by_admin = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'unit_prices'

    def __str__(self):
        return f"₱{self.unit_price}"

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
