from django.forms import ModelForm
from django import forms
from datetime import timedelta
from .models import Expenses, Products, RawMaterials, HistoryLog, Sales, ProductBatches, ProductInventory, RawMaterialBatches, RawMaterialInventory

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

    def clean(self):
        cleaned_data = super().clean()
        manufactured_date = cleaned_data.get("manufactured_date")
        expiration_date = cleaned_data.get("expiration_date")

        if manufactured_date and not expiration_date:
            cleaned_data["expiration_date"] = manufactured_date + timedelta(days=365)

        return cleaned_data

class ProductInventoryForm(ModelForm):
    class Meta:
        model = ProductInventory
        fields = ['product', 'total_stock', 'restock_threshold']
        widgets = {
            'total_stock': forms.NumberInput(attrs={'min': 0}),
            'restock_threshold': forms.NumberInput(attrs={'min': 0}),
        }

class RawMaterialBatchForm(ModelForm):
    class Meta:
        model = RawMaterialBatches
        fields = "__all__"
        widgets = {
            'batch_date': forms.DateInput(attrs={'type': 'date'}),
            'received_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }

class RawMaterialInventoryForm(ModelForm):
    class Meta:
        model = RawMaterialInventory
        fields = ['material', 'total_stock', 'reorder_threshold']
        widgets = {
            'total_stock': forms.NumberInput(attrs={'min': 0}),
            'reorder_threshold': forms.NumberInput(attrs={'min': 0}),
        }