from django.forms import ModelForm
from django import forms
from datetime import timedelta
from .models import Expenses, Products, RawMaterials, HistoryLog, Sales, ProductRecipes, ProductBatches, ProductInventory, RawMaterialBatches, RawMaterialInventory, ProductTypes, ProductVariants, Sizes, SizeUnits, UnitPrices, SrpPrices, Notifications, StockChanges, Discounts, ProductRecipes
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory


class ProductsForm(forms.ModelForm):
    product_type = forms.CharField(
        widget=forms.TextInput(attrs={'list': 'product_type-options'}))
    variant = forms.CharField(
        widget=forms.TextInput(attrs={'list': 'variant-options'}))
    size = forms.CharField(
        widget=forms.TextInput(attrs={'list': 'size-options'}), required=False)
    size_unit = forms.ModelChoiceField(
        queryset=SizeUnits.objects.all(), empty_label="Select unit")
    unit_price = forms.CharField(
        widget=forms.TextInput(attrs={'list': 'unit_price-options'}))
    srp_price = forms.CharField(
        widget=forms.TextInput(attrs={'list': 'srp_price-options'}))
    description = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
            model = Products
            exclude = ['created_by_admin', 'date_created']
            widgets = {
                'size_unit': forms.Select(attrs={'class': 'form-control'}),
            }
            
    def __init__(self, *args, **kwargs):
        self.created_by_admin = kwargs.pop('created_by_admin', None)
        super().__init__(*args, **kwargs)

        if self.instance.pk:  
            self.fields['product_type'].initial = self.instance.product_type.name
            self.fields['variant'].initial = self.instance.variant.name
            self.fields['size'].initial = self.instance.size.size_label if self.instance.size else ''
            self.fields['unit_price'].initial = self.instance.unit_price.unit_price
            self.fields['srp_price'].initial = self.instance.srp_price.srp_price

            self.initial['product_type'] = self.fields['product_type'].initial
            self.initial['variant'] = self.fields['variant'].initial
            self.initial['size'] = self.fields['size'].initial
            self.initial['unit_price'] = self.fields['unit_price'].initial
            self.initial['srp_price'] = self.fields['srp_price'].initial

    def clean_product_type(self):
        name = self.cleaned_data['product_type'].strip()
        obj, created = ProductTypes.objects.get_or_create(
            name=name,
            defaults={'created_by_admin': self.created_by_admin}
        )
        return obj

    def clean_variant(self):
        name = self.cleaned_data['variant'].strip()
        obj, created = ProductVariants.objects.get_or_create(
            name=name,
            defaults={'created_by_admin': self.created_by_admin}
        )
        return obj

    def clean_size(self):
        name = self.cleaned_data['size'].strip()
        obj, created = Sizes.objects.get_or_create(
            size_label=name,
            defaults={'created_by_admin': self.created_by_admin}
        )
        return obj

    def clean_unit_price(self):
        price = self.cleaned_data['unit_price'].strip()
        obj, created = UnitPrices.objects.get_or_create(
            unit_price=price,
            defaults={'created_by_admin': self.created_by_admin}
        )
        return obj

    def clean_srp_price(self):
        price = self.cleaned_data['srp_price'].strip()
        obj, created = SrpPrices.objects.get_or_create(
            srp_price=price,
            defaults={'created_by_admin': self.created_by_admin}
        )
        return obj

class ProductRecipeForm(forms.ModelForm):
    class Meta:
        model = ProductRecipes
        fields = ["material", "quantity_needed", "yield_factor"]

class RawMaterialsForm(ModelForm):
    class Meta:
        model = RawMaterials
        exclude = ['created_by_admin', 'date_created', 'is_archived'] 
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }

class HistoryLogForm(ModelForm):
    class Meta:
        model = HistoryLog
        fields = "__all__"

class SalesForm(ModelForm):
    class Meta:
        model = Sales
        exclude = ['created_by_admin', 'is_archived'] 
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ExpensesForm(ModelForm):
    class Meta:
        model = Expenses
        exclude = ['created_by_admin', 'is_archived'] 
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class ProductBatchForm(ModelForm):
    deduct_raw_material = forms.BooleanField(
        required=False,
        label="Deduct raw material"
    )
    
    class Meta:
        model = ProductBatches
        fields = "__all__"   
        exclude = ['created_by_admin', 'is_archived'] 
        widgets = {
            "batch_date": forms.DateInput(attrs={"type": "date"}),
            "manufactured_date": forms.DateInput(attrs={"type": "date"}),
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
        exclude = ['created_by_admin', 'is_archived'] 
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
    SALES_CHANNEL_CHOICES = [
        ('ORDER', 'Order'),
        ('CONSIGNMENT', 'Consignment'),
        ('RESELLER', 'Reseller'),
        ('PHYSICAL_STORE', 'Physical Store'),
    ]
    PRICE_TYPE_CHOICES = [
        ('UNIT', 'Unit Price'),
        ('SRP', 'Suggested Retail Price'),
    ]
    REASON_CHOICES = [
        ('SOLD', 'Sold'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
        ('RETURNED', 'Returned'),
        ('OTHERS', 'Others'),
    ]

    item_type = forms.ChoiceField(choices=ITEM_TYPE_CHOICES, required=True)
    item = forms.ChoiceField(choices=[], required=True)
    quantity = forms.DecimalField(min_value=0.01, required=True, decimal_places=2)
    reason = forms.ChoiceField(choices=REASON_CHOICES, required=True)

    sales_channel = forms.ChoiceField(choices=SALES_CHANNEL_CHOICES, required=False)
    price_type = forms.ChoiceField(choices=PRICE_TYPE_CHOICES, required=False)

    # NEW: discount fields
    discount = forms.ModelChoiceField(queryset=Discounts.objects.all(), required=False)
    custom_discount_value = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, label="Custom Discount"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].choices = [(p.id, str(p)) for p in Products.objects.all()]

    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get("reason")

        if reason == "SOLD":
            if not cleaned_data.get("sales_channel"):
                self.add_error("sales_channel", "This field is required when reason is SOLD.")
            if not cleaned_data.get("price_type"):
                self.add_error("price_type", "This field is required when reason is SOLD.")

            if not cleaned_data.get("discount") and not cleaned_data.get("custom_discount_value"):
                self.add_error("discount", "Select a discount or enter a custom discount.")

        return cleaned_data

class NotificationsForm(forms.Form):
    class Meta:
        model = Notifications
        fields = "__all__"

class BulkProductBatchForm(forms.Form):
    manufactured_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    deduct_raw_material = forms.BooleanField(
        required=False,
        initial=True,
        label="Deduct Raw Materials",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products = []
        for product in Products.objects.all().order_by('id'):
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
    received_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rawmaterials = []
        for rawmaterial in RawMaterials.objects.all():
            qty_field_name = f'rawmaterial_{rawmaterial.id}_qty'
            exp_field_name = f'rawmaterial_{rawmaterial.id}_exp'

            self.fields[qty_field_name] = forms.DecimalField(
                required=False,
                min_value=0,
                label=str(rawmaterial),
                widget=forms.NumberInput(attrs={'class': 'product-qty', 'style': 'width:100px;'})
            )

            self.fields[exp_field_name] = forms.DateField(
                required=False,
                widget=forms.DateInput(attrs={'type': 'date'})
            )

            self.rawmaterials.append({
                "rawmaterial": rawmaterial,
                "qty_field": self[qty_field_name],
                "exp_field": self[exp_field_name],
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
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
        
class CustomUserChangeForm(UserChangeForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
            raise ValidationError("This email address is already in use by another account.")

        return email