# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Admins(models.Model):
    username = models.CharField(max_length=255)
    password_hash = models.TextField()
    email = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'admins'
        verbose_name_plural = "Admins"


class Expenses(models.Model):
    category = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'expenses'
        verbose_name_plural = "Expenses"


class HistoryLog(models.Model):
    admin = models.ForeignKey(Admins, models.DO_NOTHING)
    log_type = models.ForeignKey('HistoryLogTypes', models.DO_NOTHING)
    log_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'history_log'


class HistoryLogTypes(models.Model):
    category = models.CharField(max_length=100)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'history_log_types'
        verbose_name_plural = "History Log Types"


class ProductBatches(models.Model):
    batch_date = models.DateField()
    product = models.ForeignKey('Products', models.DO_NOTHING)
    quantity = models.IntegerField()
    manufactured_date = models.DateField()
    expiration_date = models.DateField()
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_batches'
        verbose_name_plural = "Product Batches"


class ProductInventory(models.Model):
    product = models.OneToOneField('Products', models.DO_NOTHING, primary_key=True)
    total_stock = models.DecimalField(max_digits=10, decimal_places=2)
    restock_threshold = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'product_inventory'


class ProductRecipes(models.Model):
    product = models.ForeignKey('Products', models.DO_NOTHING)
    material = models.ForeignKey('RawMaterials', models.DO_NOTHING)
    quantity_needed = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_recipes'
        verbose_name_plural = "Product Recipes"


class ProductTypes(models.Model):
    name = models.CharField(max_length=255)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_types'
        verbose_name_plural = "Product Types"


class ProductVariants(models.Model):
    name = models.CharField(max_length=255)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_variants'
        verbose_name_plural = "Product Variants"


class Products(models.Model):
    product_type = models.ForeignKey(ProductTypes, models.DO_NOTHING)
    variant = models.ForeignKey(ProductVariants, models.DO_NOTHING)
    size = models.ForeignKey('Sizes', models.DO_NOTHING)
    size_unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    unit_price = models.ForeignKey('UnitPrices', models.DO_NOTHING)
    srp_price = models.ForeignKey('SrpPrices', models.DO_NOTHING)
    description = models.TextField(blank=True, null=True)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products'
        verbose_name_plural = "Products"


class RawMaterialBatches(models.Model):
    batch_date = models.DateField()
    material = models.ForeignKey('RawMaterials', models.DO_NOTHING)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    received_date = models.DateField()
    expiration_date = models.DateField(blank=True, null=True)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'raw_material_batches'
        verbose_name_plural = "Raw Material Batches"


class RawMaterialInventory(models.Model):
    material = models.OneToOneField('RawMaterials', models.DO_NOTHING, primary_key=True)
    total_stock = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_threshold = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'raw_material_inventory'


class RawMaterials(models.Model):
    name = models.CharField(max_length=45)
    size = models.ForeignKey('Sizes', models.DO_NOTHING)
    unit = models.ForeignKey('SizeUnits', models.DO_NOTHING)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    expiration_data = models.DateField(blank=True, null=True)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'raw_materials'
        verbose_name_plural = "Raw Materials"


class Sales(models.Model):
    category = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'sales'
        verbose_name_plural = "Sales"


class SizeUnits(models.Model):
    unit_name = models.CharField(max_length=45)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'size_units'
        verbose_name_plural = "Size Units"


class Sizes(models.Model):
    size_label = models.CharField(max_length=255)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'sizes'
        verbose_name_plural = "Sizes"


class SrpPrices(models.Model):
    srp_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'srp_prices'
        verbose_name_plural = "SRP Prices"


class StockChanges(models.Model):
    item_type = models.CharField(max_length=12)
    item_id = models.IntegerField()
    quantity_change = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.TextField()
    date = models.DateTimeField()
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'stock_changes'
        verbose_name_plural = "Stock Changes"


class UnitPrices(models.Model):
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by_admin = models.ForeignKey(Admins, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'unit_prices'
        verbose_name_plural = "Unit Prices"
