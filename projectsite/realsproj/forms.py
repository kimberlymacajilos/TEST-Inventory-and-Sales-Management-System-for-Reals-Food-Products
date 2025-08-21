from django.forms import ModelForm
from django import forms
from .models import Expenses, Products, RawMaterials, HistoryLog, Sales

class ProductsForm(ModelForm):
    class Meta:
        model = Products
        fields = "__all__"

class RawMaterialsForm(ModelForm):
    class Meta:
        model = RawMaterials
        fields = "__all__"

class HistoryLogForm(ModelForm):
    class Meta:
        model = HistoryLog
        fields = "__all__"

class SalesForm(ModelForm):
    class Meta:
        model = Sales
        fields = "__all__"

class ExpensesForm(ModelForm):
    class Meta:
        model = Expenses
        fields = "__all__"