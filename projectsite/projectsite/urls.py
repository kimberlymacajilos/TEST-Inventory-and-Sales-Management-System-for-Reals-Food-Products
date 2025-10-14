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
from django.contrib.auth.forms import AuthenticationForm
from realsproj.views import profile_view, edit_profile
from django.conf import settings
from django.conf.urls.static import static





urlpatterns = [
    path("admin/", admin.site.urls),
    path('', a.HomePageView.as_view(), name='home'),
    re_path(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),

    path('products/', a.ProductsList.as_view(), name='products'),
    path('products/add', a.ProductCreateView.as_view(), name='product-add'),
    path('products/<pk>', a.ProductsUpdateView.as_view(), name='product-edit'),
    path('products/<pk>/delete', a.ProductsDeleteView.as_view(), name='product-delete'),
    path("products/scan-phone/", a.product_scan_phone, name="product-scan-phone"),
   

    path('rawmaterials/', a.RawMaterialsList.as_view(), name='rawmaterials-list'),
    path('rawmaterials/', a.RawMaterialsList.as_view(), name='rawmaterials'),
    path('rawmaterials/add', a.RawMaterialsCreateView.as_view(), name='rawmaterials-add'),
    path('rawmaterials/<pk>', a.RawMaterialsUpdateView.as_view(), name='rawmaterials-edit'),
    path('rawmaterials/<pk>/delete', a.RawMaterialsDeleteView.as_view(), name='rawmaterials-delete'),
    path('rawmaterials/<int:pk>/archive/', a.RawMaterialArchiveView.as_view(), name='rawmaterials-archive'),
    path('rawmaterials/archive-old/', a.RawMaterialArchiveOldView.as_view(), name='rawmaterials-archive-old'),
    path('rawmaterials/archived/', a.ArchivedRawMaterialsListView.as_view(), name='rawmaterials-archived-list'),
    path('rawmaterials/<int:pk>/unarchive/', a.RawMaterialUnarchiveView.as_view(), name='rawmaterials-unarchive'),

    path('historylog/', a.HistoryLogList.as_view(), name='historylog'),

    path('sales/', a.SalesList.as_view(), name='sales'),
    path('sales/add', a.SalesCreateView.as_view(), name='sales-add'),
    path('sales/<pk>', a.SalesUpdateView.as_view(), name='sales-edit'),
    path('sales/<pk>/delete', a.SalesDeleteView.as_view(), name='sales-delete'),
    path('sales/<int:pk>/archive/', a.SaleArchiveView.as_view(), name='sales-archive'),
    path('sales/archive-old/', a.SaleArchiveOldView.as_view(), name='sales-archive-old'),
    path('sales/archived/', a.ArchivedSalesListView.as_view(), name='sales-archived-list'),
    path('sales/<int:pk>/unarchive/', a.SaleUnarchiveView.as_view(), name='sales-unarchive'),

    path('expenses/', a.ExpensesList.as_view(), name='expenses'),
    path('expenses/add', a.ExpensesCreateView.as_view(), name='expenses-add'),
    path('expenses/<pk>', a.ExpensesUpdateView.as_view(), name='expenses-edit'),
    path('expenses/<pk>/delete', a.ExpensesDeleteView.as_view(), name='expenses-delete'),
    path('expenses/<int:pk>/archive/', a.ExpenseArchiveView.as_view(), name='expenses-archive'),
    path('expenses/archive-old/', a.ExpenseArchiveOldView.as_view(), name='expenses-archive-old'),
    path('expenses/archived/', a.ArchivedExpensesListView.as_view(), name='expenses-archived-list'),
    path('expenses/<int:pk>/unarchive/', a.ExpenseUnarchiveView.as_view(), name='expenses-unarchive'),

    path('prodbatch/', a.ProductBatchList.as_view(), name='product-batch'),
    path('prodbatch/add', a.BulkProductBatchCreateView.as_view(), name='product-batch-add'),
    path('prodbatch/<pk>', a.ProductBatchUpdateView.as_view(), name='product-batch-edit'),
    path('prodbatch/<pk>/delete', a.ProductBatchDeleteView.as_view(), name='product-batch-delete'),
    path('prodbatch/<int:pk>/archive/', a.ProductBatchArchiveView.as_view(), name='product-batch-archive'),
    path('prodbatch/archived/', a.ArchivedProductBatchListView.as_view(), name='product-batch-archived-list'),
    path('prodbatch/<int:pk>/unarchive/', a.ProductBatchUnarchiveView.as_view(), name='product-batch-unarchive'),
    path('prodbatch/archive-old/', a.ProductBatchArchiveOldView.as_view(), name='product-batch-archive-old'),
    path('prodbatch/', a.ProductBatchList.as_view(), name='product-batch-list'),

    path('product-inventory/', a.ProductInventoryList.as_view(), name='product-inventory'),

    path('rawmatbatch/', a.RawMaterialBatchList.as_view(), name='rawmaterial-batch'),
    path('rawmatbatch/add', a.BulkRawMaterialBatchCreateView.as_view(), name='rawmaterial-batch-add'),
    path('rawmatbatch/<pk>', a.RawMaterialBatchUpdateView.as_view(), name='rawmaterial-batch-edit'),
    path('rawmatbatch/<pk>/delete', a.RawMaterialBatchDeleteView.as_view(), name='rawmaterial-batch-delete'),
    path('rawmatbatch/<int:pk>/archive/', a.RawMaterialBatchArchiveView.as_view(), name='rawmaterial-batch-archive'),
    path('rawmatbatch/archived/', a.ArchivedRawMaterialBatchListView.as_view(), name='rawmaterial-batch-archived-list'),
    path('rawmatbatch/<int:pk>/unarchive/', a.RawMaterialBatchUnarchiveView.as_view(), name='rawmaterial-batch-unarchive'),
    path('rawmatbatch/archive-old/', a.RawMaterialBatchArchiveOldView.as_view(), name='rawmaterial-batch-archive-old'),

    path('rawmaterial-inventory/', a.RawMaterialInventoryList.as_view(), name='rawmaterial-inventory'),

    path('producttypes/add', a.ProductTypeCreateView.as_view(), name='product-types-add'),
    path('productvariants/add', a.ProductVariantCreateView.as_view(), name='product-variants-add'),
    path('sizes/add', a.SizesCreateView.as_view(), name='sizes-add'),
    path('sizeunits/add', a.SizeUnitsCreateView.as_view(), name='size-units-add'),
    path('unirprices/add', a.UnitPricesCreateView.as_view(), name='unit-prices-add'),
    path('srpprices/add', a.SrpPricesCreateView.as_view(), name='srp-prices-add'),

    path('withdrawals/', a.WithdrawSuccessView.as_view(), name='withdrawals'),
    path("withdraw-item/", a.WithdrawItemView.as_view(), name="withdraw-item"),
    path('withdrawals/<int:pk>/archive/', a.WithdrawalsArchiveView.as_view(), name='withdrawals-archive'),
    path('withdrawals/archived/', a.ArchivedWithdrawalsListView.as_view(), name='withdrawals-archived-list'),
    path('withdrawals/<int:pk>/unarchive/', a.WithdrawalsUnarchiveView.as_view(), name='withdrawals-unarchive'),
    path('withdrawals/archive-old/', a.WithdrawalsArchiveOldView.as_view(), name='withdrawals-archive-old'),
    path("api/get-stock/", a.get_stock, name="get-stock"),

    re_path(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path("login/", a.login_view, name="login"),

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

    path("api/revenue-change/", a.revenue_change_api, name="revenue-change"),

    path("api/best-sellers/", a.best_sellers_api, name="best_sellers_api"),

    path('notifications/<int:pk>/read/', a.mark_notification_read, name='notification_read'),

    path('stock-changes/', a.StockChangesList.as_view(), name='stock-changes'),
    path('stock-changes/<int:pk>/archive/', a.StockChangesArchiveView.as_view(), name='stock-changes-archive'),
    path('stock-changes/archived/', a.ArchivedStockChangesListView.as_view(), name='stock-changes-archived-list'),
    path('stock-changes/<int:pk>/unarchive/', a.StockChangesUnarchiveView.as_view(), name='stock-changes-unarchive'),
    path('stock-changes/archive-old/', a.StockChangesArchiveOldView.as_view(), name='stock-changes-archive-old'),

    path("revenue-x-recent_sales", a.HomePageView.as_view(), name="home"),
    path("product-inventory/", a.ProductInventoryList.as_view(), name="product_inventory_list"),    

    path('profile/', profile_view, name='profile'),
    path('profile/edit/', a.edit_profile, name='edit_profile'),

    path('products/', a.ProductsList.as_view(), name='product-list'),
    path('products/<int:pk>/archive/', a.ProductArchiveView.as_view(), name='product-archive'),
    path('products/archived/', a.ArchivedProductsListView.as_view(), name='products-archived-list'),
    path('products/<int:pk>/unarchive/', a.ProductUnarchiveView.as_view(), name='product-unarchive'),
    path('products/archive-old/', a.ProductArchiveOldView.as_view(), name='products-archive-old'),
    path("products/<int:product_id>/recipes/", a.ProductRecipeListView.as_view(), name="recipe-list"),
    path("products/<int:product_id>/recipes/add/", a.ProductRecipeBulkCreateView.as_view(), name="recipe-add"),
    path("recipes/<int:pk>/edit/", a.ProductRecipeUpdateView.as_view(), name="recipe-edit"),
    path("recipes/<int:pk>/delete/", a.ProductRecipeDeleteView.as_view(), name="recipe-delete"),
    path("report/", a.monthly_report, name="monthly-report"),
    path("report/export/", a.monthly_report_export, name="monthly-report-export"),

    path('export-sales/', a.export_sales, name='export_sales'),
    path('export-expenses/', a.export_expenses, name='export_expenses'),

    path('user-activity/', a.UserActivityList.as_view(), name='user-activity'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)