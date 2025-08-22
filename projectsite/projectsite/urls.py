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
from realsproj.views import HomePageView, ProductsList, ProductCreateView, ProductsUpdateView, ProductsDeleteView
from realsproj.views import RawMaterialsList, RawMaterialsCreateView, RawMaterialsUpdateView, RawMaterialsDeleteView
from realsproj.views import HistoryLogList, SalesList
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
]