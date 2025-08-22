from django.forms import ModelForm
from django import forms
from .models import Expenses, Products, RawMaterials, HistoryLog, Sales, ProductBatches, ProductInventory

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

class ProductBatchForm(ModelForm):
    class Meta:
        model = ProductBatches
        fields = "__all__"
        widgets = {
            'batch_date': forms.DateInput(attrs={'type': 'date'}),
            'manufactured_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ProductInventoryForm(ModelForm):
    class Meta:
        model = ProductInventory
        fields = ['product', 'total_stock', 'restock_threshold']
        widgets = {
            'total_stock': forms.NumberInput(attrs={'min': 0}),
            'restock_threshold': forms.NumberInput(attrs={'min': 0}),
        }