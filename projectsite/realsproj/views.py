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
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.utils import timezone
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.db.models import Avg, Count, Sum
from datetime import datetime
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
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
    ProductRecipeFormSet,
    UnifiedWithdrawForm
    
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
    ProductRecipes,
    Discounts,
)

from django.db.models import Q, CharField
from decimal import Decimal, InvalidOperation
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime
from django.db.models.functions import Cast

from django.contrib.auth.models import User
from .forms import CustomUserChangeForm


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
    template_name = 'prod_add.html'
    success_url = reverse_lazy('products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_types'] = ProductTypes.objects.all()
        context['variants'] = ProductVariants.objects.all()
        context['sizes'] = Sizes.objects.all()
        context['unit_prices'] = UnitPrices.objects.all()
        context['srp_prices'] = SrpPrices.objects.all()

        if self.request.POST:
            context['recipe_formset'] = ProductRecipeFormSet(self.request.POST)
        else:
            context['recipe_formset'] = ProductRecipeFormSet()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        kwargs['created_by_admin'] = auth_user
        return kwargs

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(username=self.request.user.username)
        form.instance.created_by_admin = auth_user

        # Save ONE product
        self.object = form.save()

        # Attach formset recipes to the product
        recipe_formset = ProductRecipeFormSet(self.request.POST, instance=self.object)

        if recipe_formset.is_valid():
            recipes = recipe_formset.save(commit=False)
            for recipe in recipes:
                recipe.created_by_admin = auth_user
                recipe.products = self.object 
                recipe.save()
            for obj in recipe_formset.deleted_objects:
                obj.delete()
        else:
            return self.form_invalid(form)

        messages.success(self.request, "✅ Product added successfully.")
        return redirect(self.success_url)



class ProductsUpdateView(UpdateView):
    model = Products
    form_class = ProductsForm
    template_name = "prod_edit.html"
    success_url = reverse_lazy("products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_types'] = ProductTypes.objects.all()
        context['variants'] = ProductVariants.objects.all()
        context['sizes'] = Sizes.objects.all()
        context['unit_prices'] = UnitPrices.objects.all()
        context['srp_prices'] = SrpPrices.objects.all()

        if self.request.method == "POST":
            context["recipe_formset"] = ProductRecipeFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["recipe_formset"] = ProductRecipeFormSet(instance=self.object)
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        kwargs['created_by_admin'] = auth_user
        return kwargs

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(username=self.request.user.username)
        form.instance.created_by_admin = auth_user
        self.object = form.save()

        recipe_formset = ProductRecipeFormSet(self.request.POST, instance=self.object)

        if recipe_formset.is_valid():
            recipes = recipe_formset.save(commit=False)
            for recipe in recipes:
                recipe.created_by_admin = auth_user
                recipe.products = self.object
                recipe.save()
            for obj in recipe_formset.deleted_objects:
                obj.delete()
            recipe_formset.save_m2m()  # <-- important
        else:
            return self.render_to_response(
                self.get_context_data(form=form, recipe_formset=recipe_formset)
            )

        messages.success(self.request, "✅ Product added successfully.")
        return redirect(self.success_url)


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
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related("unit", "created_by_admin").order_by('-id')
        query = self.request.GET.get("q", "").strip()
        date_filter = self.request.GET.get("date_filter", "").strip()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(unit__unit_name__icontains=query) |
                Q(price_per_unit__icontains=query) |
                Q(date_created__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )
        
        if date_filter:
            try:
                # Parse only year and month (from YYYY-MM)
                parsed_date = datetime.strptime(date_filter, "%Y-%m")
                queryset = queryset.filter(
                    Q(date_created__year=parsed_date.year, date_created__month=parsed_date.month)
                )
            except ValueError:
                pass  # Ignore invalid format

        return queryset

        return queryset

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

        admin_filter = self.request.GET.get("admin", "").strip()
        if admin_filter:
            queryset = queryset.filter(admin__username=admin_filter)

        log_filter = self.request.GET.get("log", "").strip()
        if log_filter:
            queryset = queryset.filter(log_type__category=log_filter)

        date_str = self.request.GET.get("date", "").strip()
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(log_date__date=date_obj)
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admins'] = HistoryLog.objects.values_list('admin__username', flat=True).distinct()
        context['logs'] = HistoryLog.objects.values_list('log_type__category', flat=True).distinct()
        return context
    

class SalesList(ListView):
    model = Sales
    context_object_name = 'sales'
    template_name = "sales_list.html"
    paginate_by = 10

    def get_queryset(self):
        qs = Sales.objects.select_related("created_by_admin").order_by("-date")

        # --- Search filter ---
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(category__icontains=query) |
                Q(amount__icontains=query) |
                Q(date__icontains=query) |
                Q(description__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )

        # --- Category filter ---
        category = self.request.GET.get("category", "").strip()
        if category:
            qs = qs.filter(category__iexact=category)

        # --- Month filter (YYYY-MM) ---
        month = self.request.GET.get("month", "").strip()
        if month:
            try:
                year, month_num = month.split("-")
                qs = qs.filter(date__year=year, date__month=month_num)
            except ValueError:
                pass  # ignore invalid month

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
        categories = Sales.objects.values_list('category', flat=True).distinct()
        context['categories'] = categories

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
        category = self.request.GET.get("category", "").strip()
        month = self.request.GET.get("month", "").strip()

        if query:
            queryset = queryset.filter(
                Q(category__icontains=query) |
                Q(amount__icontains=query) |
                Q(date__icontains=query) |
                Q(description__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )
        if category:
            queryset = queryset.filter(category=category)
        if month:
            # Filter by month (YYYY-MM)
            queryset = queryset.filter(date__year=int(month.split("-")[0]),
                                       date__month=int(month.split("-")[1]))

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
            # Unique categories for dropdown
        categories = Expenses.objects.values_list('category', flat=True).distinct()
        context["categories"] = categories
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
        date_filter = self.request.GET.get("date_filter", "").strip()

        if query:
            queryset = queryset.filter(
                Q(product__product_type__name__icontains=query) |
                Q(product__variant__name__icontains=query) |
                Q(batch_date__icontains=query) |
                Q(manufactured_date__icontains=query) |
                Q(expiration_date__icontains=query)
            )

        if date_filter:
            try:
                # Parse only year and month (from YYYY-MM)
                parsed_date = datetime.strptime(date_filter, "%Y-%m")
                queryset = queryset.filter(
                    Q(batch_date__year=parsed_date.year, batch_date__month=parsed_date.month) |
                    Q(manufactured_date__year=parsed_date.year, manufactured_date__month=parsed_date.month) |
                    Q(expiration_date__year=parsed_date.year, expiration_date__month=parsed_date.month)
                )
            except ValueError:
                pass  # Ignore invalid format

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
        queryset = super().get_queryset().select_related(
            "product",
            "product__product_type",
            "product__variant",
            "product__size",
            "product__size_unit",
        )

        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.annotate(
                total_stock_str=Cast("total_stock", CharField()),
                restock_threshold_str=Cast("restock_threshold", CharField()),
            )

            queryset = queryset.filter(
                Q(product__description__icontains=q) |
                Q(product__product_type__name__icontains=q) |
                Q(product__variant__name__icontains=q) |
                Q(product__size__size_label__icontains=q) |      # ✅ fixed here
                Q(product__size_unit__unit_name__icontains=q) |  # ✅ correct
                Q(unit__unit_name__icontains=q) |                # ✅ correct
                Q(total_stock_str__icontains=q) |
                Q(restock_threshold_str__icontains=q)
            )

        return queryset.order_by("product_id")

class RawMaterialList(ListView):
    model = RawMaterials
    context_object_name = 'raw_materials'
    template_name = "rawmaterial_list.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related("unit", "created_by_admin").order_by('-id')
        query = self.request.GET.get("q", "").strip()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(unit__unit_name__icontains=query) |
                Q(price_per_unit__icontains=query) |
                Q(expiration_date__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )

        return queryset

    
class RawMaterialBatchList(ListView):
    model = RawMaterialBatches
    context_object_name = 'rawmatbatch'
    template_name = "rawmatbatch_list.html"
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related("material", "created_by_admin").order_by('-id')
        query = self.request.GET.get("q", "").strip()
        date_filter = self.request.GET.get("date_filter", "").strip()

        if query:
            queryset = queryset.filter(
                Q(material__name__icontains=query) |
                Q(batch_date__icontains=query) |
                Q(received_date__icontains=query) |
                Q(quantity__icontains=query) |
                Q(expiration_date__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )
        
        if date_filter:
            try:
                # Parse only year and month (from YYYY-MM)
                parsed_date = datetime.strptime(date_filter, "%Y-%m")
                queryset = queryset.filter(
                    Q(batch_date__year=parsed_date.year, batch_date__month=parsed_date.month) |
                    Q(received_date__year=parsed_date.year, received_date__month=parsed_date.month) |
                    Q(expiration_date__year=parsed_date.year, expiration_date__month=parsed_date.month)
                )
            except ValueError:
                pass  # Ignore invalid format

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
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related("material").order_by('-material_id')
        query = self.request.GET.get("q", "").strip()

        if query:
            queryset = queryset.filter(
                Q(material__name__icontains=query) |
                Q(total_stock__icontains=query) |
                Q(reorder_threshold__icontains=query)
            )

        return queryset

class ProductTypeCreateView(CreateView):
    model = ProductTypes
    form_class = ProductTypesForm
    template_name = "prodtype_add.html"
    success_url = reverse_lazy("product-add")

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        return super().form_valid(form)

class ProductVariantCreateView(CreateView):
    model = ProductVariants
    form_class = ProductVariantsForm
    template_name = "prodvar_add.html"
    success_url = reverse_lazy("product-add")


    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        return super().form_valid(form)

class SizesCreateView(CreateView):
    model = Sizes
    form_class = SizesForm
    template_name = "sizes_add.html"
    success_url = reverse_lazy("product-add")

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        return super().form_valid(form)

class SizeUnitsCreateView(CreateView):
    model = SizeUnits
    form_class = SizeUnitsForm
    template_name = "sizeunits_add.html"
    success_url = reverse_lazy("product-add")

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        return super().form_valid(form)

class UnitPricesCreateView(CreateView):
    model = UnitPrices
    form_class = UnitPricesForm
    template_name = "unitprices_add.html"
    success_url = reverse_lazy("product-add")

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        return super().form_valid(form)

class SrpPricesCreateView(CreateView):
    model = SrpPrices
    form_class = SrpPricesForm
    template_name = "srpprices_add.html"
    success_url = reverse_lazy("product-add")

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        return super().form_valid(form)


class WithdrawSuccessView(ListView):
    model = Withdrawals
    context_object_name = 'withdrawals'
    template_name = "withdrawn.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = Withdrawals.objects.all().order_by('-date')
        request = self.request

        q = request.GET.get("q")
        if q:
            filters = (
                Q(created_by_admin__username__icontains=q) |
                Q(reason__icontains=q) |
                Q(item_type__icontains=q)
            )
            if q.isdigit():
                filters |= Q(item_id=q)
            queryset = queryset.filter(filters)

        item_type = request.GET.get("item_type")
        if item_type:
            queryset = queryset.filter(item_type=item_type)

        reason = request.GET.get("reason")
        if reason:
            queryset = queryset.filter(reason=reason)

        date_val = request.GET.get("date")
        if date_val:
            try:
                if len(date_val) == 7:  # YYYY-MM
                    year, month = map(int, date_val.split("-"))
                    queryset = queryset.filter(date__year=year, date__month=month)
                elif len(date_val) == 10:  # YYYY-MM-DD
                    year, month, day = map(int, date_val.split("-"))
                    queryset = queryset.filter(date__year=year, date__month=month, date__day=day)
                elif len(date_val) == 4:  # YYYY
                    queryset = queryset.filter(date__year=int(date_val))
            except ValueError:
                pass  

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admins"] = (
            Withdrawals.objects
            .values_list("created_by_admin__username", flat=True)
            .distinct()
            .order_by("created_by_admin__username")
        )
        return context
    
class WithdrawItemView(View):
    template_name = "withdraw_item.html"

    def get(self, request):
        products = Products.objects.all().select_related(
            "product_type", "variant", "size", "size_unit", "productinventory"
        )
        rawmaterials = RawMaterials.objects.all().select_related(
            "unit", "rawmaterialinventory"
        )
        discounts = Discounts.objects.all()

        return render(request, self.template_name, {
            "products": products,
            "rawmaterials": rawmaterials,
            "discounts": discounts
        })

    def post(self, request):
        item_type = request.POST.get("item_type")
        reason = request.POST.get("reason")
        sales_channel = request.POST.get("sales_channel")
        price_type = request.POST.get("price_type")

        count = 0  

        if item_type == "PRODUCT":
            for key, value in request.POST.items():
                if key.startswith("product_") and value:
                    try:
                        product_id = key.split("_")[1]
                        quantity = float(value)
                        if quantity <= 0:
                            continue
                        product = Products.objects.get(id=product_id)
                        inv = product.productinventory

                        if quantity > inv.total_stock:
                            messages.error(request, f"Not enough stock for {product}")
                            continue

                        discount_val = request.POST.get(f"discount_{product_id}")
                        discount_obj = None
                        custom_value = None
                        if discount_val:
                            try:
                                discount_obj = Discounts.objects.get(value=discount_val)
                            except Discounts.DoesNotExist:
                                custom_value = discount_val

                        Withdrawals.objects.create(
                            item_id=product.id,
                            item_type="PRODUCT",
                            quantity=quantity,
                            reason=reason,
                            date=timezone.now(),
                            created_by_admin=request.user,
                            sales_channel=sales_channel if reason == "SOLD" else None,
                            price_type=price_type if reason == "SOLD" else None,
                            discount_id=discount_obj.id if discount_obj else None,
                            custom_discount_value=custom_value,
                        )

                        inv.total_stock -= quantity
                        inv.save()
                        count += 1
                    except Exception as e:
                        messages.error(request, f"Error withdrawing product: {e}")

        elif item_type == "RAW_MATERIAL":
            for key, value in request.POST.items():
                if key.startswith("material_") and value:
                    try:
                        material_id = key.split("_")[1]
                        quantity = float(value)
                        if quantity <= 0:
                            continue
                        material = RawMaterials.objects.get(id=material_id)
                        inv = material.rawmaterialinventory

                        if quantity > inv.total_stock:
                            messages.error(request, f"Not enough stock for {material}")
                            continue

                        Withdrawals.objects.create(
                            item_id=material.id,
                            item_type="RAW_MATERIAL",
                            quantity=quantity,
                            reason=reason,
                            date=timezone.now(),
                            created_by_admin=request.user,
                        )

                        inv.total_stock -= quantity
                        inv.save()
                        count += 1
                    except Exception as e:
                        messages.error(request, f"Error withdrawing raw material: {e}")

        if count > 0:
            messages.success(request, f"{count} item(s) withdrawn successfully.")
        else:
            messages.warning(request, "No withdrawals were recorded.")

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
            auth_user = AuthUser.objects.get(id=request.user.id)

            for rawmaterial_info in form.rawmaterials:
                rawmaterial = rawmaterial_info['rawmaterial']
                qty = form.cleaned_data.get(f'rawmaterial_{rawmaterial.id}_qty')
                exp_date = form.cleaned_data.get(f'rawmaterial_{rawmaterial.id}_exp')

                if qty:
                    RawMaterialBatches.objects.create(
                        material=rawmaterial,
                        quantity=qty,
                        batch_date=batch_date,
                        received_date=received_date,
                        expiration_date=exp_date,
                        created_by_admin=auth_user
                    )

            return redirect('rawmaterial-batch')

        return render(request, self.template_name, {'form': form, 'raw_materials': form.rawmaterials})

@login_required
def profile_view(request):
    return render(request, "profile.html")


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


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
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('home')  # Redirect to home after successful login
            else:
                messages.error(request, "Your account is not active.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

# def register(request):
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()  # Save the new user to the database
#             messages.success(request, 'Your account has been created successfully! You can now log in.')
#             return redirect('login')  # Redirect to login page after successful registration
#     else:
#         form = UserCreationForm()  # Instantiate a blank form

#     return render(request, 'register.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
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
    user = request.user

    if request.method == "POST":
        # --- General fields ---
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")

        # --- Password fields (read early) ---
        current_password = (request.POST.get("current_password") or "").strip()
        new_password = (request.POST.get("new_password") or "").strip()
        repeat_new_password = (request.POST.get("repeat_new_password") or "").strip()

        # ===== HARD GUARDS: block partial password inputs =====
        if current_password and not (new_password or repeat_new_password):
            messages.error(request, "To change your password, please enter both New Password and Repeat New Password.")
            form = UserChangeForm(request.POST, instance=user)
            return render(request, "editprofile.html", {"form": form, "active_tab": "account-change-password"})

        if (new_password or repeat_new_password) and not current_password:
            messages.error(request, "Please enter your Current Password to change your password.")
            form = UserChangeForm(request.POST, instance=user)
            return render(request, "editprofile.html", {"form": form, "active_tab": "account-change-password"})

        if new_password and not repeat_new_password:
            messages.error(request, "Please repeat your new password.")
            form = UserChangeForm(request.POST, instance=user)
            return render(request, "editprofile.html", {"form": form, "active_tab": "account-change-password"})

        if repeat_new_password and not new_password:
            messages.error(request, "Please enter a new password.")
            form = UserChangeForm(request.POST, instance=user)
            return render(request, "editprofile.html", {"form": form, "active_tab": "account-change-password"})

        # ===== Full password change flow (all three provided) =====
        password_change_requested = False
        if current_password and new_password and repeat_new_password:
            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
                form = UserChangeForm(request.POST, instance=user)
                return render(request, "editprofile.html", {"form": form, "active_tab": "account-change-password"})

            if new_password != repeat_new_password:
                messages.error(request, "New passwords do not match.")
                form = UserChangeForm(request.POST, instance=user)
                return render(request, "editprofile.html", {"form": form, "active_tab": "account-change-password"})

            try:
                validate_password(new_password, user=user)
            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, msg)
                form = UserChangeForm(request.POST, instance=user)
                return render(request, "editprofile.html", {"form": form, "active_tab": "account-change-password"})

            password_change_requested = True

        # --- Email uniqueness (exclude self) ---
        if User.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, "This email address is already in use by another account.")
            form = UserChangeForm(request.POST, instance=user)
            return render(request, "editprofile.html", {"form": form, "active_tab": "account-general"})

        # --- Apply profile changes ---
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # --- Apply password change if requested ---
        if password_change_requested:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password updated successfully.")

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    # GET
    form = UserChangeForm(instance=user)
    return render(request, "editprofile.html", {"form": form, "active_tab": "account-general"})