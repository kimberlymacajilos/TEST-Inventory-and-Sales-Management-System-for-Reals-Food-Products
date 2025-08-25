"""
URL configuration for projectsite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from realsproj import views as a

urlpatterns = [
    path('admin/', admin.site.urls),
    path("admin/", admin.site.urls),
    path('', a.HomePageView.as_view(), name='home'),

    path('products/', a.ProductsList.as_view(), name='products'),
    path('products/add', a.ProductCreateView.as_view(), name='product-add'),
    path('products/<pk>', a.ProductsUpdateView.as_view(), name='product-edit'),
    path('products/<pk>/delete', a.ProductsDeleteView.as_view(), name='product-delete'),

    path('rawmaterials/', a.RawMaterialsList.as_view(), name='rawmaterials'),
    path('rawmaterials/add', a.RawMaterialsCreateView.as_view(), name='rawmaterials-add'),
    path('rawmaterials/<pk>', a.RawMaterialsUpdateView.as_view(), name='rawmaterials-edit'),
    path('rawmaterials/<pk>/delete', a.RawMaterialsDeleteView.as_view(), name='rawmaterials-delete'),

    path('historylog/', a.HistoryLogList.as_view(), name='historylog'),

    path('sales/', a.SalesList.as_view(), name='sales'),
    path('sales/add', a.SalesCreateView.as_view(), name='sales-add'),
    path('sales/<pk>', a.SalesUpdateView.as_view(), name='sales-edit'),
    path('sales/<pk>/delete', a.SalesDeleteView.as_view(), name='sales-delete'),

    path('expenses/', a.ExpensesList.as_view(), name='expenses'),
    path('expenses/add', a.ExpensesCreateView.as_view(), name='expenses-add'),
    path('expenses/<pk>', a.ExpensesUpdateView.as_view(), name='expenses-edit'),
    path('expenses/<pk>/delete', a.ExpensesDeleteView.as_view(), name='expenses-delete'),

    path('prodbatch/', a.ProductBatchList.as_view(), name='product-batch'),
    path('prodbatch/add', a.ProductBatchCreateView.as_view(), name='product-batch-add'),
    path('prodbatch/<pk>', a.ProductBatchUpdateView.as_view(), name='product-batch-edit'),
    path('prodbatch/<pk>/delete', a.ProductBatchDeleteView.as_view(), name='product-batch-delete'),

    path('product-inventory/', a.ProductInventoryList.as_view(), name='product-inventory'),
    path('product-inventory/add', a.ProductInventoryCreateView.as_view(), name='product-inventory-add'),
    path('product-inventory/<pk>', a.ProductInventoryUpdateView.as_view(), name='product-inventory-edit'),
    path('product-inventory/<pk>/delete', a.ProductInventoryDeleteView.as_view(), name='product-inventory-delete'),

    path('rawmatbatch/', a.RawMaterialBatchList.as_view(), name='rawmaterial-batch'),
    path('rawmatbatch/add', a.RawMaterialBatchCreateView.as_view(), name='rawmaterial-batch-add'),
    path('rawmatbatch/<pk>', a.RawMaterialBatchUpdateView.as_view(), name='rawmaterial-batch-edit'),
    path('rawmatbatch/<pk>/delete', a.RawMaterialBatchDeleteView.as_view(), name='rawmaterial-batch-delete'),

    path('rawmatinvent/', a.RawMaterialInventoryList.as_view(), name='rawmaterial-inventory'),
    path('rawmatinvent/add', a.RawMaterialInventoryCreateView.as_view(), name='rawmaterial-inventory-add'),
    path('rawmatinvent/<pk>', a.RawMaterialInventoryUpdateView.as_view(), name='rawmaterial-inventory-edit'), 
    path('rawmatinvent/<pk>/delete', a.RawMaterialInventoryDeleteView.as_view(), name='rawmaterial-inventory-delete'),

    path('producttypes/add', a.ProductTypeCreateView.as_view(), name='product-types-add'),
    path('productvariants/add', a.ProductVariantCreateView.as_view(), name='product-variants-add'),
    path('sizes/add', a.SizesCreateView.as_view(), name='sizes-add'),
    path('sizeunits/add', a.SizeUnitsCreateView.as_view(), name='size-units-add'),
    path('unirprices/add', a.UnitPricesCreateView.as_view(), name='unit-prices-add'),
    path('srpprices/add', a.SrpPricesCreateView.as_view(), name='srp-prices-add'),
]