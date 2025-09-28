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
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django.contrib.auth import login, authenticate
from django.contrib.auth import get_user_model
from django.utils import timezone
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.db.models import Avg, Count, Sum
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
    BulkRawMaterialBatchForm,
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
        product_type = self.request.GET.get("product_type")
        variant = self.request.GET.get("variant")
        size = self.request.GET.get("size")
        date_created = self.request.GET.get("date_created")

        if product_type:
            queryset = queryset.filter(product_type__name__icontains=product_type)
        if variant:
            queryset = queryset.filter(variant__name__icontains=variant)
        if size:
            queryset = queryset.filter(size__size_label__icontains=size)
        if date_created:
            date_created = date_created.replace("/", "-").strip()
            parts = date_created.split("-")

            year, month, day = None, None, None

            if len(parts) == 3:
                if len(parts[0]) == 4:
                    year, month, day = parts
                else:
                    month, day, year = parts
            elif len(parts) == 2:
                if len(parts[0]) == 4:
                    year, month = parts
                else:
                    month, year = parts
            elif len(parts) == 1:
                if len(parts[0]) == 4: 
                    year = parts[0]
                elif len(parts[0]) <= 2:
                    month = parts[0]

            filters = {}
            if year and year.isdigit():
                filters["date_created__year"] = int(year)
            if month and month.isdigit():
                filters["date_created__month"] = int(month)
            if day and day.isdigit():
                filters["date_created__day"] = int(day)

            if filters:
                queryset = queryset.filter(**filters)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query_params"] = self.request.GET
        return context

class ProductCreateView(CreateView):
    model = Products
    form_class = ProductsForm
    template_name = "prod_add.html"
    success_url = reverse_lazy("products")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "✅ Product added successfully.")
        return response


class ProductsUpdateView(UpdateView):
    model = Products
    form_class = ProductsForm
    template_name = "prod_edit.html"
    success_url = reverse_lazy("products")
    

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "✏️ Product updated successfully.")
        return response


class ProductsDeleteView(DeleteView):
    model = Products
    success_url = reverse_lazy("products")

    def get_success_url(self):
        messages.success(self.request, "🗑️ Product deleted successfully.")
        return super().get_success_url()


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

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        response = super().form_valid(form)
        messages.success(self.request, "✅ Raw Material created successfully.")
        return response

class RawMaterialsUpdateView(UpdateView):
    model = RawMaterials
    form_class = RawMaterialsForm
    template_name = 'rawmaterial_edit.html'
    success_url = reverse_lazy('rawmaterials')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "✏️ Raw Material updated successfully.")
        return response



class RawMaterialsDeleteView(DeleteView):
    model = RawMaterials
    success_url = reverse_lazy('rawmaterials')

    def get_success_url(self):
        messages.success(self.request, "🗑️ Raw Material deleted successfully.")
        return super().get_success_url()

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

    def get_queryset(self):
        qs = Sales.objects.select_related("created_by_admin").order_by("-date")

        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(item__icontains=query) |
                Q(quantity__icontains=query) |
                Q(amount__icontains=query) |
                Q(date__icontains=query) |
                Q(description__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )

        self._full_queryset = qs
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        full_qs = getattr(self, "_full_queryset", Sales.objects.all())

        context["sales_summary"] = full_qs.aggregate(
            total_sales=Sum("amount"),
            average_sales=Avg("amount"),
            sales_count=Count("id"),
        )

        return context


class SalesCreateView(CreateView):
    model = Sales
    form_class = SalesForm
    template_name = 'sales_add.html'
    success_url = reverse_lazy('sales')
    
    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        response = super().form_valid(form)
        messages.success(self.request, "✅ Sale recorded successfully.")
        return response

class SalesUpdateView(UpdateView):
    model = Sales
    form_class = SalesForm
    template_name = 'sales_edit.html'
    success_url = reverse_lazy('sales')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "✏️ Sale updated successfully.")
        return response

class SalesDeleteView(DeleteView):
    model = Sales
    success_url = reverse_lazy('sales')

    def get_success_url(self):
        messages.success(self.request, "🗑️ Sale deleted successfully.")
        return super().get_success_url()


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

class ExpensesCreateView(CreateView):
    model = Expenses
    form_class = ExpensesForm
    template_name = 'expenses_add.html'
    success_url = reverse_lazy('expenses')

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        response = super().form_valid(form)
        messages.success(self.request, "✅ Expense recorded successfully.")
        return response


class ExpensesUpdateView(UpdateView):
    model = Expenses
    form_class = ExpensesForm
    template_name = 'expenses_edit.html'
    success_url = reverse_lazy('expenses')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "✏️ Expense updated successfully.")
        return response

class ExpensesDeleteView(DeleteView):
    model = Expenses
    success_url = reverse_lazy('expenses')

    def get_success_url(self):
        messages.success(self.request, "🗑️ Expense deleted successfully.")
        return super().get_success_url()


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
                Q(product__description__icontains=query) |
                Q(batch_date__icontains=query) |           
                Q(manufactured_date__icontains=query) |     
                Q(expiration_date__icontains=query) |     
                Q(quantity__icontains=query) |              
                Q(created_by_admin__username__icontains=query)  
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

    def form_valid(self, form):
        messages.success(self.request, "✅ Product Batch updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Failed to update Product Batch. Please check the form.")
        return super().form_invalid(form)


class ProductBatchDeleteView(DeleteView):
    model = ProductBatches
    success_url = reverse_lazy("product-batch")

    def get_success_url(self):
        messages.success(self.request, "🗑️ Product Batch deleted successfully.")
        return super().get_success_url()
    

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

    def get_queryset(self):
        queryset = super().get_queryset().select_related("material", "created_by_admin").order_by('-id')
        query = self.request.GET.get("q", "").strip()

        if query:
            queryset = queryset.filter(
                Q(rawmaterial__description__icontains=query) |   # raw material description from RawMaterials
                Q(batch_date__icontains=query) |             # batch_date
                Q(received_date__icontains=query) |      # received_date
                Q(expiration_date__icontains=query) |        # expiration_date
                Q(quantity__icontains=query) |               # quantity
                Q(created_by_admin__username__icontains=query)  # admin username
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
        products = Products.objects.all().select_related(
            "product_type", "variant", "size", "size_unit", "productinventory"
        )
        rawmaterials = RawMaterials.objects.all().select_related(
            "unit", "rawmaterialinventory"
        )

        return render(request, self.template_name, {
            "products": products,
            "rawmaterials": rawmaterials
        })
    
    def post(self, request):
        item_type = request.POST.get("item_type", "").upper()
        reason = request.POST.get("reason", "").upper()

        sales_channel = request.POST.get("sales_channel", None)
        price_type = request.POST.get("price_type", None)

        if item_type not in ["PRODUCT", "RAW_MATERIAL"]:
            messages.error(request, "Invalid item type.")
            return redirect("withdraw-item")

        if item_type == "PRODUCT":
            model = Products
            prefix = "product_"
        else:
            model = RawMaterials
            prefix = "material_"

        withdrawals_made = 0
        errors = []

        with transaction.atomic():
            for key, value in request.POST.items():
                if key.startswith(prefix) and value.strip():
                    try:
                        qty = Decimal(value)
                    except (InvalidOperation, TypeError):
                        continue

                    if qty <= 0:
                        continue

                    item_id = key.replace(prefix, "")
                    item = get_object_or_404(model, id=item_id)

                    if item_type == "PRODUCT":
                        inventory = getattr(item, "productinventory", None)
                    else:
                        inventory = getattr(item, "rawmaterialinventory", None)

                    if not inventory:
                        errors.append(f"No inventory record found for {item}")
                        continue

                    if qty > inventory.total_stock:
                        errors.append(f"Not enough stock for {item}")
                        continue

                    Withdrawals.objects.create(
                        item_id=item.id,
                        item_type=item_type,
                        quantity=qty,
                        reason=reason,
                        date=timezone.now(),
                        created_by_admin=request.user,
                        sales_channel=sales_channel if reason == "SOLD" else None,
                        price_type=price_type if reason == "SOLD" else None,
                    )
                    withdrawals_made += 1

        if withdrawals_made > 0:
            messages.success(request, f"{withdrawals_made} withdrawal(s) recorded successfully.")

        for error in errors:
            messages.error(request, error)

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


class BulkProductBatchCreateView(View):
    template_name = "prodbatch_add.html"

    def get(self, request):
        form = BulkProductBatchForm()
        return render(request, self.template_name, {'form': form, 'products': form.products})

    def post(self, request):
        form = BulkProductBatchForm(request.POST)
        if form.is_valid():
            batch_date = form.cleaned_data['batch_date']
            manufactured_date = form.cleaned_data['manufactured_date']
            deduct_raw_material = form.cleaned_data['deduct_raw_material']
            auth_user = AuthUser.objects.get(id=request.user.id)

            try:
                added_any = False
                for product_info in form.products:
                    product = product_info['product']
                    qty = form.cleaned_data.get(f'product_{product.id}_qty')
                    if qty:
                        ProductBatches.objects.create(
                            product=product,
                            quantity=qty,
                            batch_date=batch_date,
                            manufactured_date=manufactured_date,
                            created_by_admin=auth_user,
                            deduct_raw_material=deduct_raw_material
                        )
                        added_any = True

                if added_any:
                    messages.success(request, "✅ Product Batch added successfully.")
                else:
                    messages.warning(request, "⚠️ No product quantities were entered.")

                return redirect("product-batch")

            except Exception as e:
                messages.error(
                    request,
                    f"❌ Product Batch not added: insufficient raw materials."
                )
                return redirect("product-batch")

        return render(request, self.template_name, {'form': form, 'products': form.products})


class BulkRawMaterialBatchCreateView(LoginRequiredMixin, View):
    template_name = "rawmatbatch_add.html"

    def get(self, request):
        form = BulkRawMaterialBatchForm()
        return render(request, self.template_name, {'form': form, 'raw_materials': form.rawmaterials})

    def post(self, request):
        form = BulkRawMaterialBatchForm(request.POST)
        if form.is_valid():
            batch_date = form.cleaned_data['batch_date']
            received_date = form.cleaned_data['received_date']
            expiration_date = form.cleaned_data.get('expiration_date')  # get manually entered value
            auth_user = AuthUser.objects.get(id=request.user.id)

            for rawmaterial_info in form.rawmaterials:
                rawmaterial = rawmaterial_info['rawmaterial']
                qty = form.cleaned_data.get(f'rawmaterial_{rawmaterial.id}_qty')
                if qty:
                    RawMaterialBatches.objects.create(
                        material=rawmaterial,
                        quantity=qty,
                        batch_date=batch_date,
                        received_date=received_date,
                        expiration_date=expiration_date,
                        created_by_admin=auth_user
                    )

            return redirect('rawmaterial-batch')

        return render(request, self.template_name, {'form': form, 'raw_materials': form.rawmaterials})


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


class StockChangesList(ListView):
    model = StockChanges
    context_object_name = 'stock_changes'
    template_name = "stock_changes.html"
    paginate_by = 10

    def get_queryset(self):
        return StockChanges.objects.all().order_by('-date')
    
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirect to home page after login
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new user to the database
            messages.success(request, 'Your account has been created successfully! You can now log in.')
            return redirect('login')  # Redirect to login page after successful registration
    else:
        form = UserCreationForm()  # Instantiate a blank form

    return render(request, 'register.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new user to the database
            messages.success(request, 'Your account has been created successfully! You can now log in.')
            return redirect('login')  # Redirect to login page after successful registration
        else:
            # If the form is not valid, the errors will automatically be shown in the template
            messages.error(request, 'There were errors in your form. Please check the fields and try again.')
    else:
        form = CustomUserCreationForm()  # Instantiate a blank form

    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'profile.html') 

@login_required
def edit_profile(request):
    user = request.user  # Get the currently logged-in user

    if request.method == "POST":
        # Create a form instance with the POST data and the current user
        form = UserChangeForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()  # Save the form if it's valid
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")  # Redirect to the profile page after saving
        else:
            # If the form is invalid, show errors
            messages.error(request, "There was an error updating your profile. Please check the form.")
    else:
        # If it's a GET request, pre-fill the form with the current user data
        form = UserChangeForm(instance=user)

    return render(request, "editprofile.html", {"form": form})