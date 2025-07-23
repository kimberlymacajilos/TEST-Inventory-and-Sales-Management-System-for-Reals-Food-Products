from django.contrib import admin
from .models import Admins, Batches, Expenses, HistoryLog, HistoryLogTypes, ProductInventories, ProductRecipes, ProductTypes, Products, RawMaterialInventory, RawMaterialStockLog, RawMaterials, Sales, SizeUnits, Sizes, SrpPrices, UnitPrices, Variants
# Register your models here.

admin.site.register(Admins)
admin.site.register(Batches)
admin.site.register(Expenses)
admin.site.register(HistoryLog)
admin.site.register(HistoryLogTypes)
admin.site.register(ProductInventories)
admin.site.register(ProductRecipes)
admin.site.register(ProductTypes)
admin.site.register(Products)
admin.site.register(RawMaterialInventory)
admin.site.register(RawMaterialStockLog)
admin.site.register(RawMaterials)
admin.site.register(Sales)
admin.site.register(SizeUnits)
admin.site.register(Sizes)
admin.site.register(SrpPrices)
admin.site.register(UnitPrices)
admin.site.register(Variants)
