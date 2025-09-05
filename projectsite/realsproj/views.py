from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from realsproj.forms import ProductsForm, RawMaterialsForm, HistoryLogForm, SalesForm, ExpensesForm, ProductBatchForm, ProductInventoryForm, RawMaterialBatchForm, RawMaterialInventoryForm
from realsproj.models import Products, RawMaterials, HistoryLog, Sales, Expenses, ProductBatches, ProductInventory, RawMaterialBatches, RawMaterialInventory
from django.db.models import Q

class HomePageView(ListView):
    model = Products
    context_object_name = 'home'
    template_name = "home.html"

class ProductsList(ListView):
    model = Products
    context_object_name = 'products'
    template_name = "prod_list.html"
    paginate_by = 10
    

    def get_queryset(self):
        # Preload related FKs for performance
        queryset = (
            super()
            .get_queryset()
            .select_related("product_type", "variant", "size", "size_unit", "unit_price", "srp_price")
        )

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(description__icontains=query) |
                Q(product_type__name__icontains=query) |
                Q(variant__name__icontains=query)   # assuming ProductVariants also has "name"
            )

        return queryset



class ProductCreateView(CreateView):
    model = Products
    form_class = ProductsForm
    template_name = 'prod_add.html'
    success_url = reverse_lazy('products')

class ProductsUpdateView(UpdateView):
    model = Products
    form_class = ProductsForm
    template_name = 'prod_edit.html'
    success_url = reverse_lazy('products')

class ProductsDeleteView(DeleteView):
    model = Products
    template_name = 'prod_delete.html'
    success_url = reverse_lazy('products')

class RawMaterialsList(ListView):
    model = RawMaterials
    context_object_name = 'rawmaterials'
    template_name = "rawmaterial_list.html"
    paginate_by = 10

class RawMaterialsCreateView(CreateView):
    model = RawMaterials
    form_class = RawMaterialsForm
    template_name = 'rawmaterial_add.html'
    success_url = reverse_lazy('rawmaterials')

class RawMaterialsUpdateView(UpdateView):
    model = RawMaterials
    form_class = RawMaterialsForm
    template_name = 'rawmaterial_edit.html'
    success_url = reverse_lazy('rawmaterials')

class RawMaterialsDeleteView(DeleteView):
    model = RawMaterials
    template_name = 'rawmaterial_delete.html'
    success_url = reverse_lazy('rawmaterials')

class HistoryLogList(ListView):
    model = HistoryLog
    context_object_name = 'historylog'
    template_name = "historylog_list.html"
    paginate_by = 10

    def get_queryset(self):
        return HistoryLog.objects.all().order_by('-id')  # or '-log_date'
    
class SalesList(ListView):
    model = Sales
    context_object_name = 'sales'
    template_name = "sales_list.html"
    paginate_by = 10

class SalesCreateView(CreateView):
    model = Sales
    form_class = SalesForm
    template_name = 'sales_add.html'
    success_url = reverse_lazy('sales')

class SalesUpdateView(UpdateView):
    model = Sales
    form_class = SalesForm
    template_name = 'sales_edit.html'
    success_url = reverse_lazy('sales')

class SalesDeleteView(DeleteView):
    model = Sales
    template_name = 'sales_delete.html'
    success_url = reverse_lazy('sales')

class ExpensesList(ListView):
    model = Expenses
    context_object_name = 'expenses'
    template_name = "expenses_list.html"
    paginate_by = 10

class ExpensesCreateView(CreateView):
    model = Expenses
    form_class = ExpensesForm
    template_name = 'expenses_add.html'
    success_url = reverse_lazy('expenses')

class ExpensesUpdateView(UpdateView):
    model = Expenses
    form_class = ExpensesForm
    template_name = 'expenses_edit.html'
    success_url = reverse_lazy('expenses')

class ExpensesDeleteView(DeleteView):
    model = Expenses
    template_name = 'expenses_delete.html'
    success_url = reverse_lazy('expenses')

class ProductBatchList(ListView):
    model = ProductBatches
    context_object_name = 'product_batch'
    template_name = "prodbatch_list.html"
    paginate_by = 10

    def get_queryset(self):
        return ProductBatches.objects.all().order_by('-id')
    
class ProductBatchCreateView(CreateView):
    model = ProductBatches
    form_class = ProductBatchForm
    template_name = 'prodbatch_add.html'
    success_url = reverse_lazy('product-batch')

class ProductBatchUpdateView(UpdateView):
    model = ProductBatches
    form_class = ProductBatchForm
    template_name = 'prodbatch_edit.html'
    success_url = reverse_lazy('product-batch')

class ProductBatchDeleteView(DeleteView):
    model = ProductBatches
    template_name = 'prodbatch_delete.html'
    success_url = reverse_lazy('product-batch')

class ProductInventoryList(ListView):
    model = ProductInventory
    context_object_name = 'product_inventory'
    template_name = "prodinvent_list.html"
    paginate_by = 10

class ProductInventoryCreateView(CreateView):
    model = ProductInventory
    form_class = ProductInventoryForm
    template_name = 'prodinvent_add.html'
    success_url = reverse_lazy('product-inventory')

class ProductInventoryUpdateView(UpdateView):
    model = ProductInventory
    form_class = ProductInventoryForm
    template_name = 'prodinvent_edit.html'
    success_url = reverse_lazy('product-inventory')

class ProductInventoryDeleteView(DeleteView):
    model = ProductInventory
    template_name = 'prodinvent_delete.html'
    success_url = reverse_lazy('product-inventory')

class RawMaterialBatchList(ListView):
    model = RawMaterialBatches
    context_object_name = 'rawmatbatch'
    template_name = "rawmatbatch_list.html"
    paginate_by = 10

    def get_queryset(self):
        return RawMaterialBatches.objects.all().order_by('-id')
    
class RawMaterialBatchCreateView(CreateView):
    model = RawMaterialBatches
    form_class = RawMaterialBatchForm
    template_name = 'rawmatbatch_add.html'
    success_url = reverse_lazy('rawmatbatch')

class RawMaterialBatchUpdateView(UpdateView):
    model = RawMaterialBatches
    form_class = RawMaterialBatchForm
    template_name = 'rawmatbatch_edit.html'
    success_url = reverse_lazy('rawmatbatch')

class RawMaterialBatchDeleteView(DeleteView):
    model = RawMaterialBatches
    template_name = 'rawmatbatch_delete.html'
    success_url = reverse_lazy('rawmatbatch')

class RawMaterialInventoryList(ListView):
    model = RawMaterialInventory
    context_object_name = 'rawmatinvent'
    template_name = "rawmatinvent_list.html"
    paginate_by = 10

    def get_queryset(self):
        return RawMaterialInventory.objects.all().order_by('-material__name')
    
class RawMaterialInventoryCreateView(CreateView):
    model = RawMaterialInventory
    form_class = RawMaterialInventoryForm
    template_name = 'rawmatinvent_add.html'
    success_url = reverse_lazy('rawmat-inventory')

class RawMaterialInventoryUpdateView(UpdateView):
    model = RawMaterialInventory
    form_class = RawMaterialInventoryForm
    template_name = 'rawmatinvent_edit.html'
    success_url = reverse_lazy('rawmat-inventory')

class RawMaterialInventoryDeleteView(DeleteView):
    model = RawMaterialInventory
    template_name = 'rawmatinvent_delete.html'
    success_url = reverse_lazy('rawmat-inventory')

class ProductTypeCreateView(CreateView):
    model = ProductTypes
    form_class = ProductTypesForm
    template_name = "prodtype_add.html"
    success_url = reverse_lazy("product-add")

class ProductVariantCreateView(CreateView):
    model = ProductVariants
    form_class = ProductVariantsForm
    template_name = "prodvar_add.html"
    success_url = reverse_lazy("product-add")

class SizesCreateView(CreateView):
    model = Sizes
    form_class = SizesForm
    template_name = "sizes_add.html"
    success_url = reverse_lazy("product-add")

class SizeUnitsCreateView(CreateView):
    model = SizeUnits
    form_class = SizeUnitsForm
    template_name = "sizeunits_add.html"
    success_url = reverse_lazy("product-add")

class UnitPricesCreateView(CreateView):
    model = UnitPrices
    form_class = UnitPricesForm
    template_name = "unitprices_add.html"
    success_url = reverse_lazy("product-add")

class SrpPricesCreateView(CreateView):
    model = SrpPrices
    form_class = SrpPricesForm
    template_name = "srpprices_add.html"
    success_url = reverse_lazy("product-add")

