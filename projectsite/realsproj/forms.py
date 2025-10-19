from django.forms import ModelForm
from django import forms
from datetime import timedelta
from .models import Expenses, Products, RawMaterials, HistoryLog, Sales, ProductBatches, ProductInventory, RawMaterialBatches, RawMaterialInventory, ProductTypes, ProductVariants, Sizes, SizeUnits, UnitPrices, SrpPrices, Notifications, StockChanges, Discounts, ProductRecipes, Withdrawals
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory


class ProductsForm(forms.ModelForm):
    # ADD THIS - Barcode field
    barcode = forms.CharField(
        required=False,  # Optional, in case manual entry
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Scan or enter barcode',
            'id': 'barcode-input'  # Important for WebSocket
        })
    )
    
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
            # ADD THIS - for edit mode
            self.fields['barcode'].initial = self.instance.barcode

            self.initial['product_type'] = self.fields['product_type'].initial
            self.initial['variant'] = self.fields['variant'].initial
            self.initial['size'] = self.fields['size'].initial
            self.initial['unit_price'] = self.fields['unit_price'].initial
            self.initial['srp_price'] = self.fields['srp_price'].initial
            # ADD THIS
            self.initial['barcode'] = self.fields['barcode'].initial

    # ADD THIS - Clean barcode method
    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode', '').strip()
        
        # If empty on edit, keep existing barcode instead of clearing it
        if not barcode:
            if self.instance and self.instance.pk:
                return self.instance.barcode
            return barcode
        
        # Check for duplicate barcode (exclude current instance if editing)
        qs = Products.objects.filter(barcode=barcode)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError(
                f"Barcode '{barcode}' is already used by another product."
            )
        
        return barcode

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
    field_order = ["name", "size", "unit", "price_per_unit"]

    class Meta:
        model = RawMaterials
        field_order = ["name", "size", "unit", "price_per_unit"]
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
        initial=True,
        label="Deduct Raw Materials",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input show-checkbox',
        })
    )
    
    class Meta:
        model = ProductBatches
        fields = [
            'product',
            'quantity',
            'batch_date',
            'manufactured_date',
            'deduct_raw_material',
        ]
        widgets = {
            'batch_date': forms.DateInput(attrs={'type': 'date'}),
            'manufactured_date': forms.DateInput(attrs={'type': 'date'}),
            'deduct_raw_material': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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

class WithdrawEditForm(forms.ModelForm):
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

    item_type = forms.ChoiceField(choices=ITEM_TYPE_CHOICES, required=True, label="Item Type")
    item_id = forms.ChoiceField(choices=[], required=True, label="Item")
    quantity = forms.DecimalField(min_value=0.01, required=True, decimal_places=2)
    reason = forms.ChoiceField(choices=REASON_CHOICES, required=True)
    sales_channel = forms.ChoiceField(choices=SALES_CHANNEL_CHOICES, required=False)
    price_type = forms.ChoiceField(choices=PRICE_TYPE_CHOICES, required=False)

    discount = forms.ModelChoiceField(
        queryset=Discounts.objects.all(),
        required=False,
        empty_label="No Discount",
        label="Select Discount"
    )
    custom_discount_value = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        label="Custom Discount (%)"
    )

    class Meta:
        model = Withdrawals
        fields = [
            'item_type', 'item_id', 'quantity', 'reason',
            'sales_channel', 'price_type', 'discount', 'custom_discount_value'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        products = [(p.id, str(p)) for p in Products.objects.all()]
        materials = [(m.id, str(m)) for m in RawMaterials.objects.all()]
        self.fields['item_id'].choices = products + materials

        if self.instance.pk:
            if self.instance.item_type == 'PRODUCT':
                self.fields['item_id'].choices = products
            elif self.instance.item_type == 'RAW_MATERIAL':
                self.fields['item_id'].choices = materials

    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get("reason")

        if reason == "SOLD":
            if not cleaned_data.get("sales_channel"):
                self.add_error("sales_channel", "This field is required when reason is SOLD.")
            if not cleaned_data.get("price_type"):
                self.add_error("price_type", "This field is required when reason is SOLD.")

            discount = cleaned_data.get("discount")
            custom_discount = cleaned_data.get("custom_discount_value")

            if discount and custom_discount:
                self.add_error("custom_discount_value", "You cannot select and enter a discount at the same time.")

        return cleaned_data

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
    custom_price = forms.DecimalField(required=False, min_value=0, decimal_places=2)

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
        sales_channel = cleaned_data.get("sales_channel")
        custom_price = cleaned_data.get("custom_price")

        if reason == "SOLD":
            if not cleaned_data.get("sales_channel"):
                self.add_error("sales_channel", "This field is required when reason is SOLD.")
            if not cleaned_data.get("price_type") and sales_channel != "CONSIGNMENT":
                self.add_error("price_type", "Price type is required unless it's a consignment sale.")

            if sales_channel == "CONSIGNMENT":
                if not custom_price:
                    self.add_error("custom_price", "Custom price is required for consignment sales.")

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