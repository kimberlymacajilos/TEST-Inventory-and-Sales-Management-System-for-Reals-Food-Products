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
from .forms import CustomUserCreationForm
from django.utils import timezone
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
    StockChangesForm,
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
    StockChanges,
    SalesSummary,
    ExpensesSummary,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sales_summary = SalesSummary.objects.first()
        total_sales = sales_summary.total_amount if sales_summary else 0

        expenses_summary = ExpensesSummary.objects.first()
        total_expenses = expenses_summary.total_amount if expenses_summary else 0

        context['total_revenue'] = total_sales - total_expenses

        context['total_stocks'] = ProductBatches.objects.aggregate(
            total=Sum('quantity')
        )['total'] or 0

        context['recent_sales'] = Withdrawals.objects.filter(
            item_type="PRODUCT", reason="SOLD"
        ).order_by('-date')[:6]

        return context


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
                Q(variant__name__icontains=query)  
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
    
from django.db.models import Sum, Avg, Count

class SalesList(ListView):
    model = Sales
    context_object_name = 'sales'
    template_name = "sales_list.html"
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
        self.filtered_queryset = queryset
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        summary = self.filtered_queryset.aggregate(
            total_sales=Sum("amount"),
            average_sales=Avg("amount"),
            sales_count=Count("id"),
        )
        context["sales_summary"] = summary
        return context

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

from django.db.models import Sum

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
        self.filtered_queryset = queryset
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        summary = self.filtered_queryset.aggregate(
            total_expenses=Sum("amount"),
            average_expenses=Avg("amount"),
            expenses_count=Count("id"),
        )
        context["expenses_summary"] = summary
        return context


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_expenses"] = Expenses.objects.aggregate(
            total=Sum("amount")
        )["total"] or 0
        return context

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

        return queryset.order_by("product_id")


class RawMaterialBatchList(ListView):
    model = RawMaterialBatches
    context_object_name = 'rawmatbatch'
    template_name = "rawmatbatch_list.html"
    paginate_by = 10
    
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
        selected_type = request.GET.get("item_type", "").upper()
        selected_expiration = request.GET.get("expiration_date", "")

        product_date_qs = (
            ProductBatches.objects
            .filter(expiration_date__isnull=False)
            .values_list("expiration_date", flat=True)
            .distinct()
            .order_by("expiration_date")
        )
        product_expirations = [{"value": d.isoformat(), "display": d.strftime("%b %d, %Y")} for d in product_date_qs]
        product_has_no_expiration = ProductBatches.objects.filter(expiration_date__isnull=True).exists()

        material_date_qs = (
            RawMaterialBatches.objects
            .filter(expiration_date__isnull=False)
            .values_list("expiration_date", flat=True)
            .distinct()
            .order_by("expiration_date")
        )
        material_expirations = [{"value": d.isoformat(), "display": d.strftime("%b %d, %Y")} for d in material_date_qs]
        material_has_no_expiration = RawMaterialBatches.objects.filter(expiration_date__isnull=True).exists()

        products = Products.objects.all().select_related(
            "product_type", "variant", "size", "size_unit", "productinventory"
        )
        rawmaterials = RawMaterials.objects.all().select_related(
            "unit", "rawmaterialinventory"
        )

        if selected_type == "PRODUCT" and selected_expiration:
            if selected_expiration == "NONE":
                batches = ProductBatches.objects.filter(expiration_date__isnull=True)
            else:
                batches = ProductBatches.objects.filter(expiration_date=selected_expiration)

            batches = batches.filter(quantity__gt=0)

            product_ids = batches.values_list("product_id", flat=True).distinct()
            products = Products.objects.filter(
                id__in=product_ids,
                productinventory__total_stock__gt=0
            ).select_related("product_type", "variant", "size", "size_unit", "productinventory")

            batch_sums = batches.values("product").annotate(total_stock=Sum("quantity"))
            stock_map = {int(b["product"]): b["total_stock"] or 0 for b in batch_sums}

            for p in products:
                p.filtered_stock = stock_map.get(p.id, 0)
        
        
        else:
            # not filtered: annotate with full inventory total_stock
            for p in products:
                inv = getattr(p, "productinventory", None)
                p.filtered_stock = inv.total_stock if inv else 0

        if selected_type == "RAW_MATERIAL" and selected_expiration:
            if selected_expiration == "NONE":
                mbatches = RawMaterialBatches.objects.filter(expiration_date__isnull=True)
            else:
                mbatches = RawMaterialBatches.objects.filter(expiration_date=selected_expiration)

            mbatches = mbatches.filter(quantity__gt=0)

            material_ids = mbatches.values_list("material_id", flat=True).distinct()
            rawmaterials = RawMaterials.objects.filter(
                id__in=material_ids,
                rawmaterialinventory__total_stock__gt=0
            ).select_related("unit", "rawmaterialinventory")

            mbatch_sums = mbatches.values("material").annotate(total_stock=Sum("quantity"))
            mstock_map = {int(b["material"]): b["total_stock"] or 0 for b in mbatch_sums}

            for m in rawmaterials:
                m.filtered_stock = Decimal(str(mstock_map.get(m.id, 0)))

        else:
            for m in rawmaterials:
                inv = getattr(m, "rawmaterialinventory", None)
                m.filtered_stock = inv.total_stock if inv else Decimal("0")

        return render(request, self.template_name, {
            "products": products,
            "rawmaterials": rawmaterials,
            "product_expirations": product_expirations,
            "product_has_no_expiration": product_has_no_expiration,
            "material_expirations": material_expirations,
            "material_has_no_expiration": material_has_no_expiration,
            "selected_type": selected_type,
            "selected_expiration": selected_expiration,
        })

    def post(self, request):
        item_type = request.POST.get("item_type", "").upper()
        reason = request.POST.get("reason", "").upper()
        expiration_date = request.POST.get("expiration_date", "")

        if item_type not in ["PRODUCT", "RAW_MATERIAL"]:
            messages.error(request, "Invalid item type.")
            return redirect("withdraw-item")

        model = Products if item_type == "PRODUCT" else RawMaterials
        prefix = "product_" if item_type == "PRODUCT" else "material_"

        withdrawals_made = 0
        errors = []

        with transaction.atomic():
            for key, value in request.POST.items():
                if not key.startswith(prefix):
                    continue
                if not value.strip():
                    continue

                try:
                    qty = Decimal(value)
                except (InvalidOperation, TypeError):
                    errors.append(f"Invalid quantity for {key}.")
                    continue

                if qty <= 0:
                    continue

                item_id = key.replace(prefix, "")
                item = get_object_or_404(model, id=item_id)

                if item_type == "PRODUCT":
                    inventory = getattr(item, "productinventory", None)
                else:
                    inventory = getattr(item, "rawmaterialinventory", None)

                if expiration_date:
                    if item_type == "PRODUCT":
                        if expiration_date == "NONE":
                            batch_sum = ProductBatches.objects.filter(product_id=item.id, expiration_date__isnull=True).aggregate(s=Sum("quantity"))["s"] or 0
                        else:
                            batch_sum = ProductBatches.objects.filter(product_id=item.id, expiration_date=expiration_date).aggregate(s=Sum("quantity"))["s"] or 0
                        available_stock = Decimal(str(batch_sum))
                    else:
                        if expiration_date == "NONE":
                            mbatch_sum = RawMaterialBatches.objects.filter(material_id=item.id, expiration_date__isnull=True).aggregate(s=Sum("quantity"))["s"] or 0
                        else:
                            mbatch_sum = RawMaterialBatches.objects.filter(material_id=item.id, expiration_date=expiration_date).aggregate(s=Sum("quantity"))["s"] or 0
                        available_stock = Decimal(str(mbatch_sum))
                else:
                    available_stock = Decimal(str(inventory.total_stock)) if inventory and inventory.total_stock is not None else Decimal("0")

                if available_stock == 0:
                    errors.append(f"No stock for {item}.")
                    continue

                if qty > available_stock:
                    errors.append(f"Not enough stock for {item}. Requested {qty}, available {available_stock}.")
                    continue

                if not inventory:
                    errors.append(f"No inventory record found for {item}.")
                    continue

                inventory.total_stock = Decimal(str(inventory.total_stock)) - qty
                inventory.save()

                if expiration_date:
                    if item_type == "PRODUCT":
                        if expiration_date == "NONE":
                            batches_qs = ProductBatches.objects.filter(
                                product=item, expiration_date__isnull=True
                            ).order_by("id")
                        else:
                            batches_qs = ProductBatches.objects.filter(
                                product=item, expiration_date=expiration_date
                            ).order_by("id")
                    else:  # RAW_MATERIAL
                        if expiration_date == "NONE":
                            batches_qs = RawMaterialBatches.objects.filter(
                                material=item, expiration_date__isnull=True
                            ).order_by("id")
                        else:
                            batches_qs = RawMaterialBatches.objects.filter(
                                material=item, expiration_date=expiration_date
                            ).order_by("id")

                    remaining = qty
                    for batch in batches_qs:
                        if remaining <= 0:
                            break
                        if batch.quantity >= remaining:
                            batch.quantity -= remaining
                            batch.save()
                            remaining = 0
                        else:
                            remaining -= batch.quantity
                            batch.quantity = 0
                            batch.save()

                Withdrawals.objects.create(
                    item_id=item.id,
                    item_type=item_type,
                    quantity=qty,
                    reason=reason,
                    date=timezone.now(),
                    created_by_admin=request.user,
                )
                withdrawals_made += 1


        if withdrawals_made:
            messages.success(request, f"{withdrawals_made} {item_type.lower()}(s) withdrawn successfully.")
        if errors:
            for e in errors:
                messages.error(request, e)

        return redirect("withdrawals")
    
def get_total_revenue():
    withdrawals = Withdrawals.objects.filter(item_type="PRODUCT", reason="SOLD")
    total = 0
    for w in withdrawals:
        total += w.compute_revenue()
    return total

    
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

    def get(self, request, *args, **kwargs):
        Notifications.objects.filter(is_read=False).update(is_read=True)
        return super().get(request, *args, **kwargs)


class BulkProductBatchCreateView(LoginRequiredMixin, View):
    template_name = "prodbatch_add.html"

    def get(self, request):
        form = BulkProductBatchForm()
        return render(request, self.template_name, {'form': form, 'products': form.products})

    def post(self, request):
        form = BulkProductBatchForm(request.POST)
        if form.is_valid():
            batch_date = form.cleaned_data['batch_date']
            manufactured_date = form.cleaned_data['manufactured_date']
            expiration_date = form.cleaned_data.get('expiration_date')  # get manually entered value
            auth_user = AuthUser.objects.get(id=request.user.id)

            for product_info in form.products:
                product = product_info['product']
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

        return render(request, self.template_name, {'form': form, 'products': form.products})


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


def best_sellers_api(request):
    TOP_N = 5
    qs = (
        Withdrawals.objects
        .filter(item_type="PRODUCT", reason="SOLD")
        .values("item_id")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")
    )

    sold_list = list(qs)
    product_ids = [item["item_id"] for item in sold_list]
    products = Products.objects.in_bulk(product_ids)

    labels, data = [], []
    for item in sold_list[:TOP_N]: 
        prod = products.get(item["item_id"])
        labels.append(str(prod) if prod else f"Unknown {item['item_id']}")
        data.append(float(item["total_sold"]))

    return JsonResponse({"labels": labels, "data": data})


def mark_notification_read(request, pk):
    notif = get_object_or_404(Notifications, pk=pk)
    notif.is_read = True
    notif.save()
    return redirect('notifications')

@login_required
def profile_view(request):
    return render(request, "profile.html")


class StockChangesList(ListView):
    model = StockChanges
    context_object_name = 'stock_changes'
    template_name = "stock_changes.html"
    paginate_by = 10

    def get_queryset(self):
        return StockChanges.objects.all().order_by('-date')