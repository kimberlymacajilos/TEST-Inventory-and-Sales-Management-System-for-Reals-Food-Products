from django.urls import path
from . import views

urlpatterns = [
    path('sales/archive-old/', views.SaleArchiveOldView.as_view(), name='sales-archive-old'),
    path('sales/archived/', views.ArchivedSalesListView.as_view(), name='sales-archived-list'),
    path('sales/<int:pk>/unarchive/', views.SaleUnarchiveView.as_view(), name='sales-unarchive'),
]