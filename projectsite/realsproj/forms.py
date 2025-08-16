from django.forms import ModelForm
from django import forms
from .models import Products, RawMaterials, HistoryLog

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