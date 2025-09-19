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
from django.contrib.auth import views as auth_views
from django.urls import path, re_path, include



urlpatterns = [
    path('admin/', admin.site.urls),
    path("admin/", admin.site.urls),
    path('', a.HomePageView.as_view(), name='home'),
    re_path(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),

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
    path('prodbatch/add', a.BulkProductBatchCreateView.as_view(), name='product-batch-add'),
    path('prodbatch/<pk>', a.ProductBatchUpdateView.as_view(), name='product-batch-edit'),
    path('prodbatch/<pk>/delete', a.ProductBatchDeleteView.as_view(), name='product-batch-delete'),

    path('product-inventory/', a.ProductInventoryList.as_view(), name='product-inventory'),

    path('rawmatbatch/', a.RawMaterialBatchList.as_view(), name='rawmaterial-batch'),
    path('rawmatbatch/add', a.RawMaterialBatchCreateView.as_view(), name='rawmaterial-batch-add'),
    path('rawmatbatch/<pk>', a.RawMaterialBatchUpdateView.as_view(), name='rawmaterial-batch-edit'),
    path('rawmatbatch/<pk>/delete', a.RawMaterialBatchDeleteView.as_view(), name='rawmaterial-batch-delete'),

    path('rawmaterial-inventory/', a.RawMaterialInventoryList.as_view(), name='rawmaterial-inventory'),

    path('producttypes/add', a.ProductTypeCreateView.as_view(), name='product-types-add'),
    path('productvariants/add', a.ProductVariantCreateView.as_view(), name='product-variants-add'),
    path('sizes/add', a.SizesCreateView.as_view(), name='sizes-add'),
    path('sizeunits/add', a.SizeUnitsCreateView.as_view(), name='size-units-add'),
    path('unirprices/add', a.UnitPricesCreateView.as_view(), name='unit-prices-add'),
    path('srpprices/add', a.SrpPricesCreateView.as_view(), name='srp-prices-add'),

    path('withdrawals/', a.WithdrawSuccessView.as_view(), name='withdrawals'),
    path("withdraw-item/", a.WithdrawItemView.as_view(), name="withdraw-item"),
    path("api/get-stock/", a.get_stock, name="get-stock"),

    path("login/", a.login_view, name="login"),
    path("signup/", a.signup_view, name="signup"),

    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name="password_reset.html"), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
    
    path("api/sales-vs-expenses/", a.sales_vs_expenses, name="sales-vs-expenses"),

    path('notifications/', a.NotificationsList.as_view(), name='notifications'),
    
    path("register/", a.register, name="register"),

    path("api/best-sellers/", a.best_sellers_api, name="best_sellers_api"),

    path('notifications/<int:pk>/read/', a.mark_notification_read, name='notification_read'),

    path("profile/", a.profile_view, name="profile"),
    path('stock-changes/', a.StockChangesList.as_view(), name='stock-changes'),

    path("revenue-x-recent_sales", a.HomePageView.as_view(), name="home"),
    path("product-inventory/", a.ProductInventoryList.as_view(), name="product_inventory_list"),    
]