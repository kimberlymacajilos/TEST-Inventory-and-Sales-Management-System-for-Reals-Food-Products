from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils import timezone
from django.views import View
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from decimal import InvalidOperation
from decimal import Decimal
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth import get_user_model
from realsproj.forms import (
    ProductsForm,
    RawMaterialsForm,
    HistoryLogForm,
    SalesForm,
    ExpensesForm,
    ProductBatchForm,
    ProductInventoryForm,
    RawMaterialBatchForm,
    RawMaterialInventoryForm,
    ProductTypesForm,
    ProductVariantsForm,
    SizesForm,
    SizeUnitsForm,
    UnitPricesForm,
    SrpPricesForm, 
    NotificationsForm,
    BulkProductBatchForm,
    StockChangeForm
)

from realsproj.models import (
    Products,
    RawMaterials,
    HistoryLog,
    Sales,
    Expenses,
    ProductBatches,
    ProductInventory,
    RawMaterialBatches,
    RawMaterialInventory,
    ProductTypes,
    ProductVariants,
    Sizes,
    SizeUnits,
    UnitPrices,
    SrpPrices,
    Withdrawals,
    Notifications,
    AuthUser,
    StockChanges
)

from django.db.models import Q
from decimal import Decimal, InvalidOperation
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .forms import CustomUserCreationForm

@method_decorator(login_required, name='dispatch')

class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

def sales_vs_expenses(request):
    sales_data = (
        Sales.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    expenses_data = (
        Expenses.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    months = sorted(
        set([s['month'].strftime("%Y-%m") for s in sales_data] +
            [e['month'].strftime("%Y-%m") for e in expenses_data])
    )

    sales_totals = []
    expenses_totals = []

    for m in months:
        sales_totals.append(
            next((float(s['total']) for s in sales_data if s['month'].strftime("%Y-%m") == m), 0)
        )
        expenses_totals.append(
            next((float(e['total']) for e in expenses_data if e['month'].strftime("%Y-%m") == m), 0)
        )

    return JsonResponse({
        "months": months,
        "sales": sales_totals,
        "expenses": expenses_totals,
    })

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
        queryset = super().get_queryset().select_related("admin", "log_type").order_by("-log_date")

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(admin__username__icontains=query) |
                Q(log_type__category__icontains=query) |   # adjust if field is different
                Q(log_date__icontains=query)
            )

        return queryset
    
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
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related("created_by_admin").order_by("-date")

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(category__icontains=query) |
                Q(amount__icontains=query) |
                Q(date__icontains=query) |
                Q(description__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )

        return queryset

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
        queryset = super().get_queryset().select_related("product", "created_by_admin").order_by('-id')
        query = self.request.GET.get("q", "").strip()

        if query:
            queryset = queryset.filter(
                Q(product__description__icontains=query) |   # product description from Products
                Q(batch_date__icontains=query) |             # batch_date
                Q(manufactured_date__icontains=query) |      # manufactured_date
                Q(expiration_date__icontains=query) |        # expiration_date
                Q(quantity__icontains=query) |               # quantity
                Q(created_by_admin__username__icontains=query)  # admin username
            )

        return queryset
    
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

    def get_queryset(self):
        queryset = super().get_queryset().select_related("product")

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(product__description__icontains=query) |  # comes from Products
                Q(total_stock__icontains=query) |           # comes from ProductInventory
                Q(restock_threshold__icontains=query)       # comes from ProductInventory
            )

        return queryset.order_by("-product_id")


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
        queryset = (
            super()
            .get_queryset()
            .select_related("material", "created_by_admin")  # preload FKs for performance
            .order_by("-id")
        )

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(material__name__icontains=query) |        # material name
                Q(material__size__name__icontains=query) | # size (from Sizes)
                Q(material__unit__name__icontains=query) | # unit (from SizeUnits)
                Q(batch_date__icontains=query) |           # batch date
                Q(received_date__icontains=query) |        # received date
                Q(expiration_date__icontains=query) |      # expiration date
                Q(created_by_admin__username__icontains=query)
            )

        return queryset
    
class RawMaterialBatchCreateView(CreateView):
    model = RawMaterialBatches
    form_class = RawMaterialBatchForm
    template_name = 'rawmatbatch_add.html'
    success_url = reverse_lazy('rawmaterial-batch')  

class RawMaterialBatchUpdateView(UpdateView):
    model = RawMaterialBatches
    form_class = RawMaterialBatchForm
    template_name = 'rawmatbatch_edit.html'
    success_url = reverse_lazy('rawmaterial-batch') 
class RawMaterialBatchDeleteView(DeleteView):
    model = RawMaterialBatches
    template_name = 'rawmatbatch_delete.html'
    success_url = reverse_lazy('rawmaterial-batch')


class RawMaterialInventoryList(ListView):
    model = RawMaterialInventory
    context_object_name = 'rawmatinvent'
    template_name = "rawmatinvent_list.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("material", "material__size", "material__unit", "material__created_by_admin")
            .order_by("material__id")   # since `RawMaterialInventory` primary key = material
        )

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(material__name__icontains=query) |
                Q(material__size__name__icontains=query) |
                Q(material__unit__name__icontains=query) |
                Q(material__price_per_unit__icontains=query) |
                Q(material__created_by_admin__username__icontains=query)
            )

        return queryset
    
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


class WithdrawSuccessView(ListView):
    model = Withdrawals
    context_object_name = 'withdrawals'
    template_name = "withdrawn.html"
    paginate_by = 10

    def get_queryset(self):
        return Withdrawals.objects.all().order_by('-date')
    

class WithdrawItemView(View):
    template_name = "withdraw_item.html"

    def get(self, request):
        products = Products.objects.all()
        rawmaterials = RawMaterials.objects.all()
        return render(request, self.template_name, {
            "products": products,
            "rawmaterials": rawmaterials
        })

    def post(self, request):
        # Convert form input to uppercase to match DB constraints
        item_type = request.POST.get("item_type", "").strip().upper()
        item_id = request.POST.get("item_id")
        reason = request.POST.get("reason", "").strip().upper()
        quantity_input = request.POST.get("quantity")

        # Validate quantity
        try:
            quantity = Decimal(quantity_input)
        except (InvalidOperation, TypeError):
            messages.error(request, "Invalid quantity format.")
            return redirect("withdraw-item")

        # Determine models based on item_type
        if item_type == "PRODUCT":
            model = Products
            inventory_model = ProductInventory
            field_name = "product_id"
        elif item_type == "RAW_MATERIAL":
            model = RawMaterials
            inventory_model = RawMaterialInventory
            field_name = "material_id"
        else:
            messages.error(request, "Invalid item type selected.")
            return redirect("withdraw-item")

        # Fetch item
        item = get_object_or_404(model, id=item_id)

        with transaction.atomic():
            inventory = get_object_or_404(inventory_model, **{field_name: item.id})

            if quantity <= 0:
                messages.error(request, "Quantity must be greater than zero.")
                return redirect("withdraw-item")
            elif quantity > inventory.total_stock:
                messages.error(request, "Not enough stock to withdraw.")
                return redirect("withdraw-item")

            # Deduct stock
            inventory.total_stock -= quantity
            inventory.save()

            # Record withdrawal with uppercase item_type and reason
            Withdrawals.objects.create(
                item_id=item.id,
                item_type=item_type,
                quantity=quantity,
                reason=reason,
                date=timezone.now(),
                created_by_admin=request.user,
            )

            messages.success(request, f"{quantity} withdrawn from {item} successfully.")
            return redirect("withdrawals")

        return redirect("withdraw-item")
    
    
@require_GET
def get_stock(request):
    item_type = request.GET.get("type")
    item_id = request.GET.get("id")

    if item_type == "PRODUCT":
        inventory = ProductInventory.objects.filter(product_id=item_id).first()
    elif item_type == "RAW_MATERIAL":
        inventory = RawMaterialInventory.objects.filter(material_id=item_id).first()
    else:
        return JsonResponse({"stock": None})

    return JsonResponse({"stock": inventory.total_stock if inventory else 0})

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")  # redirect after signup
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")  # redirect after login
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


class NotificationsList(ListView):
    model = Notifications
    context_object_name = 'notifications'
    template_name = "notification.html"
    paginate_by = 10

    def get_queryset(self):
        return Notifications.objects.order_by('-created_at')



class BulkProductBatchCreateView(LoginRequiredMixin, View):
    template_name = "prodbatch_add.html"

    def get(self, request):
        form = BulkProductBatchForm()
        products = [
            {"qty_field": form[f'product_{p.id}_qty'], "label": str(p)}
            for p in Products.objects.all()
        ]
        return render(request, self.template_name, {'form': form, 'products': products})

    def post(self, request):
        form = BulkProductBatchForm(request.POST)
        if form.is_valid():
            batch_date = form.cleaned_data['batch_date']
            manufactured_date = form.cleaned_data['manufactured_date']
            expiration_date = form.cleaned_data['expiration_date']

            from realsproj.models import AuthUser
            auth_user = AuthUser.objects.get(id=request.user.id)

            for product in Products.objects.all():
                qty = form.cleaned_data.get(f'product_{product.id}_qty')
                if qty:
                    ProductBatches.objects.create(
                        product=product,
                        quantity=qty,
                        batch_date=batch_date,
                        manufactured_date=manufactured_date,
                        expiration_date=expiration_date,
                        created_by_admin=auth_user 
                    )
            return redirect('product-batch')

        products = [
            {"qty_field": form[f'product_{p.id}_qty'], "label": str(p)}
            for p in Products.objects.all()
        ]
        return render(request, self.template_name, {'form': form, 'products': products})
    
class StockChangesList(ListView):
    model = StockChanges
    context_object_name = 'stock_changes'
    template_name = "stock_change.html"
    ordering = ['-date']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related("created_by_admin").order_by("-date")

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(item_type__icontains=query) |
                Q(item_id__icontains=query) |
                Q(category__icontains=query) |
                Q(quantity_change__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )

        return queryset
    
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # or redirect to dashboard
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})
