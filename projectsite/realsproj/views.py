from django.shortcuts import render
from django.views.generic.list import ListView
from realsproj.models import Products

class HomePageView(ListView):
    model = Products
    context_object_name = 'home'
    template_name = "home.html"

class ProductsList(ListView):
    model = Products
    context_object_name = 'products'
    template_name = "prod_list.html"
    paginate_by = 10
# Create your views here.
