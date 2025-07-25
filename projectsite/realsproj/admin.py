from django.contrib import admin
from .models import Admins, Expenses, HistoryLog, HistoryLogTypes, ProductBatches, ProductInventory, ProductRecipes, ProductTypes, ProductVariants, Products, RawMaterialBatches, RawMaterialInventory, RawMaterials, Sales, SizeUnits, Sizes, SrpPrices, UnitPrices, StockChanges
# Register your models here.

admin.site.register(Admins)
admin.site.register(Expenses)
admin.site.register(HistoryLog)
admin.site.register(HistoryLogTypes)
admin.site.register(ProductBatches)
admin.site.register(ProductInventory)
admin.site.register(ProductRecipes)
admin.site.register(ProductTypes)
admin.site.register(ProductVariants)
admin.site.register(Products)
admin.site.register(RawMaterialBatches)
admin.site.register(RawMaterialInventory)
admin.site.register(RawMaterials)
admin.site.register(Sales)
admin.site.register(SizeUnits)
admin.site.register(Sizes)
admin.site.register(SrpPrices)
admin.site.register(UnitPrices)
admin.site.register(StockChanges)
