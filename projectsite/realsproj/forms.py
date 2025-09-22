from django.forms import ModelForm
from django import forms
from datetime import timedelta
from .models import Expenses, Products, RawMaterials, HistoryLog, Sales, ProductBatches, ProductInventory, RawMaterialBatches, RawMaterialInventory, ProductTypes, ProductVariants, Sizes, SizeUnits, UnitPrices, SrpPrices, Notifications, StockChanges
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError


class ProductsForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = '__all__'
        widgets = {
            'date_created': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance and self.instance.pk:
                self.fields['date_created'].initial = self.instance.date_created.strftime('%Y-%m-%dT%H:%M')

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
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ExpensesForm(ModelForm):
    class Meta:
        model = Expenses
        fields = "__all__"
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


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

class ProductTypesForm(ModelForm):
    class Meta:
        model = ProductTypes
        fields = "__all__"

class ProductVariantsForm(ModelForm):
    class Meta:
        model = ProductVariants
        fields = "__all__"

class SizesForm(ModelForm):
    class Meta:
        model = Sizes
        fields = "__all__"

class SizeUnitsForm(ModelForm):
    class Meta:
        model = SizeUnits
        fields = "__all__"

class UnitPricesForm(ModelForm):
    class Meta:
        model = UnitPrices
        fields = "__all__"

class SrpPricesForm(ModelForm):
    class Meta:
        model = SrpPrices
        fields = "__all__"

class WithdrawForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label='Quantity to Withdraw')

class UnifiedWithdrawForm(forms.Form):
    ITEM_TYPE_CHOICES = [
        ('PRODUCT', 'Product'),
        ('RAW_MATERIAL', 'Raw Material'),
    ]

    item_type = forms.ChoiceField(choices=ITEM_TYPE_CHOICES, required=True)
    item = forms.ChoiceField(choices=[], required=True)
    quantity = forms.DecimalField(min_value=0.01, required=True, decimal_places=2)
    reason = forms.CharField(max_length=255, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['item'].choices = [(p.id, str(p)) for p in Products.objects.all()]


class NotificationsForm(forms.Form):
    class Meta:
        model = Notifications
        fields = "__all__"

class BulkProductBatchForm(forms.Form):
    batch_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    manufactured_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    expiration_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products = []
        for product in Products.objects.all():
            field_name = f'product_{product.id}_qty'
            self.fields[field_name] = forms.DecimalField(
                required=False,
                min_value=0,
                label=str(product),
                widget=forms.NumberInput(attrs={'class': 'product-qty', 'style': 'width:100px;'})
            )
            self.products.append({
                "product": product,
                "qty_field": self[field_name],
            })

class BulkRawMaterialBatchForm(forms.Form):
    batch_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    received_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    expiration_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rawmaterials = []
        for rawmaterial in RawMaterials.objects.all():
            field_name = f'rawmaterial_{rawmaterial.id}_qty'
            self.fields[field_name] = forms.DecimalField(
                required=False,
                min_value=0,
                label=str(rawmaterial),
                widget=forms.NumberInput(attrs={'class': 'product-qty', 'style': 'width:100px;'})
            )
            self.rawmaterials.append({
                "rawmaterial": rawmaterial,
                "qty_field": self[field_name],
            })



class StockChangesForm(ModelForm):
    class Meta:
        model = StockChanges
        fields = "__all__"

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise ValidationError("Passwords do not match.")
        return password2
    
class CustomUserChangeForm(UserChangeForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Check if email is already taken by another user (excluding the current user)
        if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
            raise ValidationError("This email address is already in use by another account.")

        return email