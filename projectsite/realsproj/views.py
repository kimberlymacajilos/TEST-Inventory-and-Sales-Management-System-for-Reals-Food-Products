from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from realsproj.forms import ProductsForm, RawMaterialsForm, HistoryLogForm
from realsproj.models import Products, RawMaterials, HistoryLog

class HomePageView(ListView):
    model = Products
    context_object_name = 'home'
    template_name = "home.html"

class ProductsList(ListView):
    model = Products
    context_object_name = 'products'
    template_name = "prod_list.html"
    paginate_by = 10

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

# Create your views here.
