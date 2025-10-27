from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.list import ListView
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, TemplateView, View
)
from django.views.generic.edit import ModelFormMixin
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db import transaction
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm
from django.db.models import Avg, Count, Sum
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
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
    ProductRecipeForm,
    UnifiedWithdrawForm,
    CustomUserCreationForm,
    WithdrawEditForm
)

from realsproj.models import (
    Products,
    RawMaterials,
    HistoryLog,
    HistoryLogTypes,
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
    Discounts,
    ProductRecipes,
    UserActivity
)

from django.db.models import Q, CharField
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models.functions import TruncMonth, TruncDay
from django.db.models.functions import Cast
from django.contrib.auth.models import User
import os
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta, date
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models import Q, F, CharField
from django.db.models.functions import Cast
import re
from urllib.parse import urlparse, parse_qs
from django.db.models import Count


# Helper function for creating history logs
def create_history_log(admin, log_category, entity_type, entity_id, before=None, after=None):
    """
    Create a history log entry.
    
    Args:
        admin: User instance who performed the action
        log_category: String category (e.g., "Withdrawal Edited", "Withdrawal Deleted")
        entity_type: String entity type (e.g., "withdrawal")
        entity_id: ID of the entity
        before: Dict of values before change (for updates)
        after: Dict of values after change (for creates/updates)
    """
    try:
        # Get or create log type
        log_type, _ = HistoryLogTypes.objects.get_or_create(
            category=log_category,
            defaults={'created_by_admin_id': admin.id}
        )
        
        # Build details
        details = {}
        if before:
            details['before'] = before
        if after:
            details['after'] = after
        
        # Create log entry
        HistoryLog.objects.create(
            admin_id=admin.id,
            log_type_id=log_type.id,
            log_date=timezone.now(),
            entity_type=entity_type,
            entity_id=entity_id,
            details=details if details else None,
            is_archived=False
        )
    except Exception as e:
        # Silently fail to avoid breaking the main operation
        pass


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

        context['total_stocks'] = ProductInventory.objects.aggregate(
            total=Sum('total_stock')
        )['total'] or 0

        context['recent_sales'] = Withdrawals.objects.filter(
            item_type="PRODUCT", reason="SOLD"
        ).order_by('-date')[:6]

        return context


def sales_vs_expenses(request):
    sales_monthly = (
        Sales.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    expenses_monthly = (
        Expenses.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    months = sorted(
        set([s['month'].strftime("%Y-%m") for s in sales_monthly] +
            [e['month'].strftime("%Y-%m") for e in expenses_monthly])
    )

    sales_totals = []
    expenses_totals = []

    for m in months:
        sales_totals.append(
            next((float(s['total']) for s in sales_monthly if s['month'].strftime("%Y-%m") == m), 0)
        )
        expenses_totals.append(
            next((float(e['total']) for e in expenses_monthly if e['month'].strftime("%Y-%m") == m), 0)
        )

    sales_daily = (
        Sales.objects
        .annotate(day=TruncDay('date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )
    expenses_daily = (
        Expenses.objects
        .annotate(day=TruncDay('date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )

    daily_dates = sorted(
        set([s['day'].strftime("%Y-%m-%d") for s in sales_daily] +
            [e['day'].strftime("%Y-%m-%d") for e in expenses_daily])
    )

    sales_daily_totals = []
    expenses_daily_totals = []

    for d in daily_dates:
        sales_daily_totals.append(
            next((float(s['total']) for s in sales_daily if s['day'].strftime("%Y-%m-%d") == d), 0)
        )
        expenses_daily_totals.append(
            next((float(e['total']) for e in expenses_daily if e['day'].strftime("%Y-%m-%d") == d), 0)
        )

    return JsonResponse({
        "months": months,
        "sales": sales_totals,
        "expenses": expenses_totals,
        "daily_dates": daily_dates,
        "sales_daily": sales_daily_totals,
        "expenses_daily": expenses_daily_totals,
    })

def revenue_change_api(request):
    year = request.GET.get("year")
    month = request.GET.get("month")

    sales_qs = Sales.objects.all()

    if year:
        sales_qs = sales_qs.filter(date__year=year)

    if month and month != "all":
        sales_qs = sales_qs.filter(date__month=month)
        sales_data = (
            sales_qs.annotate(day=TruncDay('date'))
            .values('day')
            .annotate(total=Sum('amount'))
            .order_by('day')
        )
        labels = [s['day'].strftime("%Y-%m-%d") for s in sales_data]
    else:
        sales_data = (
            sales_qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )
        labels = [s['month'].strftime("%Y-%m") for s in sales_data]

    revenues = [float(s['total']) for s in sales_data]

    return JsonResponse({
        "labels": labels,
        "revenues": revenues,
    })


def monthly_report(request):
    sales = (
        Sales.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_sales=Sum("amount"))
        .order_by("month")
    )

    expenses = (
        Expenses.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_expenses=Sum("amount"))
        .order_by("month") 
    )

    expenses_dict = {e["month"]: e["total_expenses"] for e in expenses}

    report = []
    prev = None

    for s in sales:
        month = s["month"]
        revenue = s["total_sales"] or 0
        cost = expenses_dict.get(month, 0) or 0
        profit = revenue - cost

        revenue_change = None
        profit_change = None
        if prev:
            revenue_change = revenue - prev["revenue"]
            profit_change = profit - prev["profit"]

        report.append({
            "month": month,
            "revenue": revenue,
            "expenses": cost,
            "profit": profit,
            "revenue_change": revenue_change,
            "profit_change": profit_change,
        })
        prev = report[-1]

    summary = {
        "total_revenue": sum(r["revenue"] for r in report),
        "total_profit": sum(r["profit"] for r in report),
        "average_profit": (sum(r["profit"] for r in report) / len(report)) if report else 0,
    }

    return render(request, "reports/monthly_report.html", {
        "report": report,
        "summary": summary,
    })


def monthly_report_export(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="financial_report.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(["Month", "Revenue", "Expenses", "Profit", "Revenue Change", "Profit Change", "Trend"])
    sales = (
        Sales.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_sales=Sum("amount"))
        .order_by("month")
    )
    expenses = (
        Expenses.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_expenses=Sum("amount"))
        .order_by("month")
    )
    sales_dict = {s["month"]: Decimal(s["total_sales"] or 0) for s in sales}
    expenses_dict = {e["month"]: Decimal(e["total_expenses"] or 0) for e in expenses}
    all_months = sorted(set(list(sales_dict.keys()) + list(expenses_dict.keys())))

    report = []
    for month in all_months:
        revenue = sales_dict.get(month, Decimal(0))
        cost = expenses_dict.get(month, Decimal(0))
        profit = revenue - cost
        report.append({
            "month": month,
            "revenue": revenue,
            "expenses": cost,
            "profit": profit,
        })

    for i in range(len(report)):
        if i > 0: 
            older = report[i - 1]
            rc = report[i]["revenue"] - older["revenue"]
            pc = report[i]["profit"] - older["profit"]

            rev_change = f"↑ ₱{rc:,.2f}" if rc > 0 else f"↓ ₱{abs(rc):,.2f}" if rc < 0 else "₱0.00"
            prof_change = f"↑ ₱{pc:,.2f}" if pc > 0 else f"↓ ₱{abs(pc):,.2f}" if pc < 0 else "₱0.00"

            if rc > 0 and pc > 0:
                trend = "Revenue & Profit Increased"
            elif rc > 0 and pc < 0:
                trend = "Revenue Increased, Profit Decreased"
            elif rc < 0 and pc > 0:
                trend = "Revenue Decreased, Profit Increased"
            elif rc == 0 and pc == 0:
                trend = "No Change"
            else:
                trend = "Revenue & Profit Decreased"
        else:
            rev_change = "-"
            prof_change = "-"
            trend = "-"

        writer.writerow([
            report[i]["month"].strftime("%B %Y"),
            f"₱{report[i]['revenue']:,.2f}",
            f"₱{report[i]['expenses']:,.2f}",
            f"₱{report[i]['profit']:,.2f}",
            rev_change,
            prof_change,
            trend,
        ])

    return response

class ProductsList(ListView):
    model = Products
    context_object_name = 'products'
    template_name = "prod_list.html"
    paginate_by = 10

    def get_queryset(self):
        
        queryset = (
            Products.objects.filter(is_archived=False)
            .select_related("product_type", "variant", "size", "size_unit", "unit_price", "srp_price")
            .order_by("-id")
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
        barcode = self.request.GET.get("barcode")

        if barcode:
            queryset = queryset.filter(barcode__icontains=barcode)
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


def product_scan_phone(request):
    
    return render(request, "product_scan_phone.html")

@require_GET
def check_barcode_availability(request):
    """API endpoint to check if a barcode already exists"""
    barcode = request.GET.get('barcode', '').strip()
    product_id = request.GET.get('product_id', None)  # For edit mode
    
    if not barcode:
        return JsonResponse({'available': True, 'message': ''})
    
    # Check if barcode exists
    qs = Products.objects.filter(barcode=barcode)
    
    # Exclude current product if editing
    if product_id:
        qs = qs.exclude(pk=product_id)
    
    if qs.exists():
        product = qs.first()
        return JsonResponse({
            'available': False,
            'message': f'Barcode already used by: {product.product_type.name} - {product.variant.name}',
            'product_id': product.id
        })
    
    return JsonResponse({
        'available': True,
        'message': 'Barcode is available'
    })

class ProductArchiveView(View):
    def post(self, request, pk):
        product = get_object_or_404(Products, pk=pk)
        product.is_archived = True
        product.save()
        page = request.POST.get('page')
        if page:
            return redirect(f"{reverse('product-list')}?page={page}")
        return redirect('product-list')

class ArchivedProductsListView(ListView):
    model = Products
    template_name = 'archived_products.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        return Products.objects.filter(is_archived=True).order_by('-date_created')

class ProductUnarchiveView(View):
    def post(self, request, pk):
        product = get_object_or_404(Products, pk=pk)
        product.is_archived = False
        product.save()
        return redirect('products-archived-list')

class ProductArchiveOldView(View):
    def post(self, request):
        one_year_ago = timezone.now() - timedelta(days=365)
        Products.objects.filter(is_archived=False, date_created__lt=one_year_ago).update(is_archived=True)
        return redirect('product-list')

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
        return context  

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        kwargs['created_by_admin'] = auth_user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        try:
            auth_user = AuthUser.objects.get(username=self.request.user.username)
            form.instance.created_by_admin = auth_user

            # Save ONE product
            self.object = form.save()

        except Exception as e:
            transaction.set_rollback(True)
            messages.error(self.request, f"❌ Product did not save. {e}")
            return redirect(self.request.path)  

        messages.success(self.request, "✅ Product added successfully.")
        return redirect('recipe-list', product_id=self.object.id)

    def form_invalid(self, form):
        """Handle validation errors (e.g., duplicate barcode)"""
        # Check if barcode error exists
        if 'barcode' in form.errors:
            messages.error(self.request, f"❌ {form.errors['barcode'][0]}")
        else:
            messages.error(self.request, "❌ Please correct the errors below.")
        
        return super().form_invalid(form)


class ProductsUpdateView(UpdateView):
    model = Products
    form_class = ProductsForm
    template_name = "prod_edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add all required context data
        context['product_types'] = ProductTypes.objects.all()
        context['variants'] = ProductVariants.objects.all()
        context['sizes'] = Sizes.objects.all()
        context['unit_prices'] = UnitPrices.objects.all()
        context['srp_prices'] = SrpPrices.objects.all()
        context['recipe_list_url'] = reverse_lazy('recipe-list', kwargs={'product_id': self.object.id})
        
        # Store the current page number
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'page=' in referer:
            try:
                context['current_page'] = re.search(r'page=(\d+)', referer).group(1)
            except (AttributeError, IndexError):
                pass
        
        return context

    def get_success_url(self):
        # Try to get page from POST data first
        page = self.request.POST.get('current_page')
        
        # If not in POST, try to get from session
        if not page and 'current_page' in self.request.session:
            page = self.request.session['current_page']
            
        # Construct URL with page if available
        url = reverse('products')
        if page:
            url = f'{url}?page={page}'
            
        return url

    def post(self, request, *args, **kwargs):
        # Store the current page in session
        referer = request.META.get('HTTP_REFERER', '')
        if 'page=' in referer:
            try:
                page = re.search(r'page=(\d+)', referer).group(1)
                request.session['current_page'] = page
            except (AttributeError, IndexError):
                pass

        # Handle photo deletion
        self.object = self.get_object()
        if "delete_photo" in request.POST:
            if self.object.photo:
                self.object.photo = None
                self.object.save(update_fields=["photo"])
                messages.success(request, "Product photo deleted.")
            else:
                messages.info(request, "No photo to delete.")
            return redirect(reverse("product-edit", kwargs={"pk": self.object.pk}))

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(username=self.request.user.username)
        form.instance.created_by_admin = auth_user
        
        # Check if photo should be deleted
        if self.request.POST.get('delete_photo_flag') == '1':
            form.instance.photo = None
        
        product = form.save()
        messages.success(self.request, "✅ Product updated successfully.")
        
        # Use get_success_url() to maintain the page number
        return redirect(self.get_success_url())

@receiver(pre_save, sender=Products)
def delete_old_product_photo_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = Products.objects.get(pk=instance.pk)
    except Products.DoesNotExist:
        return

    old_file = old_instance.photo
    new_file = instance.photo

    if old_file and old_file.name:
        if (not new_file) or (old_file.name != getattr(new_file, 'name', None)):
            try:
                old_file.delete(save=False)
            except Exception:
                pass

@receiver(post_delete, sender=Products)
def delete_product_photo_on_delete(sender, instance, **kwargs):
    if instance.photo and instance.photo.name:
        try:
            instance.photo.delete(save=False)
        except Exception:
            pass


class ProductsDeleteView(DeleteView):
    model = Products
    success_url = reverse_lazy("products")

    def get_success_url(self):
        messages.success(self.request, "🗑️ Product deleted successfully.")
        page = self.request.POST.get('page')
        if page:
            return f"{reverse_lazy('products')}?page={page}"
        return super().get_success_url()

class ProductRecipeListView(ListView):
    model = ProductRecipes
    template_name = "prodrecipe_list.html"
    context_object_name = "recipes"

    def get_queryset(self):
        return ProductRecipes.objects.filter(product_id=self.kwargs['product_id']).select_related("material")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = Products.objects.get(pk=self.kwargs["product_id"])
        return context

class ProductRecipeBulkCreateView(View):
    template_name = "prodrecipe_add.html"

    def get(self, request, product_id):
        product = Products.objects.get(pk=product_id)
        RecipeFormSet = modelformset_factory(ProductRecipes, form=ProductRecipeForm, extra=1, can_delete=False)

        formset = RecipeFormSet(queryset=ProductRecipes.objects.none())
        return render(request, self.template_name, {"formset": formset, "product": product})

    def post(self, request, product_id):
        product = Products.objects.get(pk=product_id)
        auth_user = AuthUser.objects.get(username=request.user.username)
        RecipeFormSet = modelformset_factory(ProductRecipes, form=ProductRecipeForm, extra=0, can_delete=False)

        formset = RecipeFormSet(request.POST)

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.product = product
                instance.created_by_admin = auth_user
                instance.save()
            messages.success(request, "✅ Recipes added successfully.")
            return redirect("recipe-list", product_id=product.id)

        return render(request, self.template_name, {"formset": formset, "product": product})

class ProductRecipeUpdateView(UpdateView):
    model = ProductRecipes
    form_class = ProductRecipeForm
    template_name = "prodrecipe_edit.html"

    def get_success_url(self):
        messages.success(self.request, "✅ Recipe updated successfully.")
        return reverse_lazy("recipe-list", kwargs={"product_id": self.object.product_id})

class ProductRecipeDeleteView(DeleteView):
    model = ProductRecipes

    def get_success_url(self):
        messages.success(self.request, "🗑️ Recipe deleted successfully.")
        return reverse_lazy("recipe-list", kwargs={"product_id": self.object.product_id})

class RawMaterialsList(ListView):
    model = RawMaterials
    context_object_name = 'rawmaterials'
    template_name = "rawmaterial_list.html"
    paginate_by = 10
    
    def get_queryset(self):
        queryset = RawMaterials.objects.filter(is_archived=False).select_related("unit", "created_by_admin").order_by('-id')
        
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

class RawMaterialArchiveView(View):
    def post(self, request, pk):
        item = get_object_or_404(RawMaterials, pk=pk)
        item.is_archived = True
        item.save()
        return redirect('rawmaterials-list')

class RawMaterialArchiveOldView(View):
    def post(self, request):
        one_year_ago = timezone.now() - timedelta(days=365)
        RawMaterials.objects.filter(is_archived=False, date_created__lt=one_year_ago).update(is_archived=True)
        return redirect('rawmaterials-list')

class ArchivedRawMaterialsListView(ListView):
    model = RawMaterials
    template_name = 'archived_rawmaterials.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        return RawMaterials.objects.filter(is_archived=True).order_by('-date_created')

class RawMaterialUnarchiveView(View):
    def post(self, request, pk):
        item = get_object_or_404(RawMaterials, pk=pk)
        item.is_archived = False
        item.save()
        return redirect('rawmaterials-archived-list')

class RawMaterialsCreateView(CreateView):
    model = RawMaterials
    form_class = RawMaterialsForm
    template_name = 'rawmaterial_add.html'
    success_url = reverse_lazy('rawmaterials')

    @transaction.atomic
    def form_valid(self, form):
        try:
            auth_user = AuthUser.objects.get(id=self.request.user.id)
            form.instance.created_by_admin = auth_user
            self.object = form.save()
        except Exception as e:
            transaction.set_rollback(True)
            messages.error(self.request, f"Raw material creation failed: {e}")
            return redirect(self.request.path)  
        messages.success(self.request, "✅ Raw material created successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please complete all required fields. The form was reset.")
        return redirect(self.request.path)  


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
        queryset = (
            super()
            .get_queryset()
            .select_related("admin", "log_type")
            .filter(is_archived=False)
            .order_by("-log_date")
        )

        # Get filter parameters
        admin_filter = self.request.GET.get("admin", "").strip()
        log_filter = self.request.GET.get("log", "").strip()
        date_str = self.request.GET.get("date", "").strip()

        # Apply admin filter
        if admin_filter:
            queryset = queryset.filter(admin__username=admin_filter)

        # Apply log type filter
        if log_filter:
            queryset = queryset.filter(log_type__category=log_filter)

        # Apply date filter (month-based)
        if date_str:
            try:
                # Convert YYYY-MM to start and end dates of the month
                year, month = map(int, date_str.split('-'))
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                
                start_date = timezone.make_aware(datetime(year, month, 1))
                end_date = timezone.make_aware(datetime(year, month, last_day, 23, 59, 59))
                
                queryset = queryset.filter(
                    log_date__gte=start_date,
                    log_date__lte=end_date
                )
            except (ValueError, IndexError):
                # If date format is invalid, skip the date filter
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get unique admins and log types for the filter dropdowns
        context['admins'] = HistoryLog.objects.filter(
            is_archived=False
        ).order_by('admin__username').values_list('admin__username', flat=True).distinct()
        
        context['logs'] = HistoryLog.objects.filter(
            is_archived=False
        ).order_by('log_type__category').values_list('log_type__category', flat=True).distinct()
        
        # Preserve filter parameters in pagination
        filter_params = self.request.GET.copy()
        if 'page' in filter_params:
            del filter_params['page']
        context['filter_params'] = filter_params.urlencode()
        
        # Add current filter values to context
        context['current_admin'] = self.request.GET.get('admin', '')
        context['current_log'] = self.request.GET.get('log', '')
        context['current_date'] = self.request.GET.get('date', '')
        
        return context
    
class SaleArchiveView(View):
    def post(self, request, pk):
        sale = get_object_or_404(Sales, pk=pk)
        sale.is_archived = True
        sale.save()
        return redirect('sales')

class SaleArchiveOldView(View):
    def post(self, request):
        one_year_ago = timezone.now() - timedelta(days=365)
        Sales.objects.filter(is_archived=False, date__lt=one_year_ago).update(is_archived=True)
        return redirect('sales')
    
class ArchivedSalesListView(ListView):
    model = Sales
    template_name = 'archived_sales.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        return Sales.objects.filter(is_archived=True).order_by('-date')

class SaleUnarchiveView(View):
    def post(self, request, pk):
        sale = get_object_or_404(Sales, pk=pk)
        sale.is_archived = False
        sale.save()
        return redirect('sales-archived-list')

class SalesList(ListView):
    model = Sales
    context_object_name = 'sales'
    template_name = "sales_list.html"
    paginate_by = 10

    def get_queryset(self):
        # Pagsamahin ang filter dito. Magsimula sa pagkuha lang ng HINDI naka-archive.
        qs = Sales.objects.filter(is_archived=False).select_related("created_by_admin").order_by("-date")

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
                year_str, month_str = month.split("-")
                year = int(year_str)
                month_num = int(month_str.lstrip("0"))
                qs = qs.filter(date__year=year, date__month=month_num)
            except ValueError:
                pass
        else:
            today = timezone.now()
            qs = qs.filter(date__year=today.year, date__month=today.month)

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
        # Format categories for display
        raw_categories = Sales.objects.values_list('category', flat=True).distinct()
        categories = [(cat, cat.replace('_', ' ').title()) for cat in raw_categories]
        context['categories'] = categories

        # Add withdrawal-based sales (reason='SOLD')
        month = self.request.GET.get("month", "").strip()
        withdrawal_sales_qs = Withdrawals.objects.filter(
            reason='SOLD',
            is_archived=False
        ).select_related("created_by_admin").order_by("-date")
        
        # Apply same month filter as regular sales
        if month:
            try:
                year_str, month_str = month.split("-")
                year = int(year_str)
                month_num = int(month_str.lstrip("0"))
                withdrawal_sales_qs = withdrawal_sales_qs.filter(date__year=year, date__month=month_num)
            except ValueError:
                pass
        else:
            today = timezone.now()
            withdrawal_sales_qs = withdrawal_sales_qs.filter(date__year=today.year, date__month=today.month)
        
        context['withdrawal_sales'] = withdrawal_sales_qs

        return context


class SalesCreateView(CreateView):
    model = Sales
    form_class = SalesForm
    template_name = 'sales_add.html'
    success_url = reverse_lazy('sales')

    @transaction.atomic
    def form_valid(self, form):
        try:
            auth_user = AuthUser.objects.get(id=self.request.user.id)
            form.instance.created_by_admin = auth_user
            self.object = form.save()
        except Exception as e:
            transaction.set_rollback(True)
            messages.error(self.request, f"Sale creation failed: {e}")
            return redirect(self.request.path)
        messages.success(self.request, "✅ Sale recorded successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please complete all required fields. The form was reset.")
        return redirect(self.request.path) 

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
        # Start with active (non-archived) records
        qs = Expenses.objects.filter(is_archived=False).select_related("created_by_admin").order_by("-date")

        # --- Search query ---
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
                year_str, month_str = month.split("-")
                year = int(year_str)
                month_num = int(month_str.lstrip("0"))
                qs = qs.filter(date__year=year, date__month=month_num)
            except ValueError:
                pass
        else:
            # Default: show only current month
            today = timezone.now()
            qs = qs.filter(date__year=today.year, date__month=today.month)

        self._full_queryset = qs
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        full_qs = getattr(self, "_full_queryset", Expenses.objects.filter(is_archived=False))

        context["expenses_summary"] = full_qs.aggregate(
            total_expenses=Sum("amount"),
            average_expenses=Avg("amount"),
            expenses_count=Count("id"),
        )

        categories = Expenses.objects.filter(is_archived=False).values_list('category', flat=True).distinct()
        context["categories"] = categories

        return context
    
class ExpenseArchiveView(View):
    def post(self, request, pk):
        expense = get_object_or_404(Expenses, pk=pk)
        expense.is_archived = True
        expense.save()
        return redirect('expenses')

class ExpenseArchiveOldView(View):
    def post(self, request):
        one_year_ago = timezone.now() - timedelta(days=365)
        Expenses.objects.filter(is_archived=False, date__lt=one_year_ago).update(is_archived=True)
        return redirect('expenses')

class ArchivedExpensesListView(ListView):
    model = Expenses
    template_name = 'archived_expenses.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        return Expenses.objects.filter(is_archived=True).order_by('-date')

class ExpenseUnarchiveView(View):
    def post(self, request, pk):
        expense = get_object_or_404(Expenses, pk=pk)
        expense.is_archived = False
        expense.save()
        return redirect('expenses-archived-list')

class ExpensesCreateView(CreateView):
    model = Expenses
    form_class = ExpensesForm
    template_name = 'expenses_add.html'
    success_url = reverse_lazy('expenses')

    @transaction.atomic
    def form_valid(self, form):
        try:
            auth_user = AuthUser.objects.get(id=self.request.user.id)
            form.instance.created_by_admin = auth_user
            self.object = form.save()
        except Exception as e:
            transaction.set_rollback(True)
            messages.error(self.request, f"Expense creation failed: {e}")
            return redirect(self.request.path)  # reset form
        messages.success(self.request, "✅ Expense recorded successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please complete all required fields. The form was reset.")
        return redirect(self.request.path)  # reset form


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
        queryset = (
            super()
            .get_queryset()
            .select_related("product", "created_by_admin")
            .filter(is_archived=False)
            .order_by('-id')
        )

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
                parsed_date = datetime.strptime(date_filter, "%Y-%m")
                queryset = queryset.filter(
                    Q(batch_date__year=parsed_date.year, batch_date__month=parsed_date.month) |
                    Q(manufactured_date__year=parsed_date.year, manufactured_date__month=parsed_date.month) |
                    Q(expiration_date__year=parsed_date.year, expiration_date__month=parsed_date.month)
                )
            except ValueError:
                pass

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
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
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


class ProductBatchArchiveView(View):
    def post(self, request, pk):
        batch = get_object_or_404(ProductBatches, pk=pk)
        batch.is_archived = True
        batch.save()
        messages.success(request, "📦 Product Batch archived successfully.")
        page = request.GET.get('page')
        if page:
            return redirect(f"{reverse('product-batch')}?page={page}")
        return redirect('product-batch')


class ArchivedProductBatchListView(ListView):
    model = ProductBatches
    template_name = 'archived_product_batch.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        return ProductBatches.objects.filter(is_archived=True).select_related('product', 'created_by_admin').order_by('-batch_date')


class ProductBatchUnarchiveView(View):
    def post(self, request, pk):
        batch = get_object_or_404(ProductBatches, pk=pk)
        batch.is_archived = False
        batch.save()
        messages.success(request, "✅ Product Batch restored successfully.")
        return redirect('product-batch-archived-list')


class ProductBatchArchiveOldView(View):
    def post(self, request):
        from datetime import timedelta
        one_year_ago = timezone.now() - timedelta(days=365)
        archived_count = ProductBatches.objects.filter(is_archived=False, batch_date__lt=one_year_ago).update(is_archived=True)
        messages.success(request, f"📦 {archived_count} product batch(es) older than 1 year have been archived.")
        return redirect('product-batch')
    

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
            ).filter(
                Q(product__product_type__name__icontains=q) |
                Q(product__variant__name__icontains=q) |
                Q(total_stock_str__icontains=q) |
                Q(restock_threshold_str__icontains=q)
            )

        status = self.request.GET.get("status", "")
        if status == "on_stock":
            queryset = queryset.filter(total_stock__gt=F("restock_threshold"))
        elif status == "low_stock":
            queryset = queryset.filter(total_stock__lt=F("restock_threshold"), total_stock__gt=0)
        elif status == "warning":
            queryset = queryset.filter(total_stock=F("restock_threshold"))
        elif status == "out_of_stock":
            queryset = queryset.filter(total_stock=0)

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
        queryset = (
            super()
            .get_queryset()
            .select_related("material", "created_by_admin")
            .filter(is_archived=False)
            .order_by('-id')
        )

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
                pass

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

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        form.instance.created_by_admin = auth_user
        return super().form_valid(form)
    
class RawMaterialBatchDeleteView(DeleteView):
    model = RawMaterialBatches
    success_url = reverse_lazy('rawmaterial-batch')


class RawMaterialBatchArchiveView(View):
    def post(self, request, pk):
        batch = get_object_or_404(RawMaterialBatches, pk=pk)
        batch.is_archived = True
        batch.save()
        messages.success(request, "📦 Raw Material Batch archived successfully.")
        page = request.GET.get('page')
        if page:
            return redirect(f"{reverse('rawmaterial-batch')}?page={page}")
        return redirect('rawmaterial-batch')


class ArchivedRawMaterialBatchListView(ListView):
    model = RawMaterialBatches
    template_name = 'archived_rawmaterial_batch.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        return RawMaterialBatches.objects.filter(is_archived=True).select_related('material', 'created_by_admin').order_by('-batch_date')


class RawMaterialBatchUnarchiveView(View):
    def post(self, request, pk):
        batch = get_object_or_404(RawMaterialBatches, pk=pk)
        batch.is_archived = False
        batch.save()
        messages.success(request, "✅ Raw Material Batch restored successfully.")
        return redirect('rawmaterial-batch-archived-list')


class RawMaterialBatchArchiveOldView(View):
    def post(self, request):
        from datetime import timedelta
        one_year_ago = timezone.now() - timedelta(days=365)
        archived_count = RawMaterialBatches.objects.filter(is_archived=False, batch_date__lt=one_year_ago).update(is_archived=True)
        messages.success(request, f"📦 {archived_count} raw material batch(es) older than 1 year have been archived.")
        return redirect('rawmaterial-batch')


class RawMaterialInventoryList(ListView):
    model = RawMaterialInventory
    context_object_name = 'rawmatinvent'
    template_name = "rawmatinvent_list.html"
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related("material").order_by('-material_id')

        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()

        if q:
            queryset = queryset.filter(
                Q(material__name__icontains=q) |
                Q(total_stock__icontains=q) |
                Q(reorder_threshold__icontains=q)
            )

        if status == "on_stock":
            queryset = queryset.filter(total_stock__gt=F("reorder_threshold"))
        elif status == "low_stock":
            queryset = queryset.filter(total_stock__lt=F("reorder_threshold"), total_stock__gt=0)
        elif status == "warning":
            queryset = queryset.filter(total_stock=F("reorder_threshold"))
        elif status == "out_of_stock":
            queryset = queryset.filter(total_stock=0)

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


# Product Attributes Management View
class ProductAttributesView(LoginRequiredMixin, TemplateView):
    template_name = "product_attributes.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_types'] = ProductTypes.objects.all().order_by('name')
        context['product_variants'] = ProductVariants.objects.all().order_by('name')
        context['sizes'] = Sizes.objects.all().order_by('size_label')
        context['size_units'] = SizeUnits.objects.all().order_by('unit_name')
        context['unit_prices'] = UnitPrices.objects.all().order_by('unit_price')
        context['srp_prices'] = SrpPrices.objects.all().order_by('srp_price')
        return context


# Product Type CRUD
@method_decorator(login_required, name='dispatch')
class ProductTypeAddView(View):
    def post(self, request):
        from django.db import IntegrityError
        name = request.POST.get('name')
        if name:
            try:
                auth_user = AuthUser.objects.get(id=request.user.id)
                ProductTypes.objects.create(name=name, created_by_admin=auth_user)
                messages.success(request, 'Product Type added successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Product Type already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class ProductTypeEditView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        product_type = get_object_or_404(ProductTypes, pk=pk)
        name = request.POST.get('name')
        if name:
            try:
                product_type.name = name
                product_type.save()
                messages.success(request, 'Product Type updated successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Product Type name already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class ProductTypeDeleteView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        product_type = get_object_or_404(ProductTypes, pk=pk)
        try:
            product_type.delete()
            messages.success(request, 'Product Type deleted successfully!')
        except IntegrityError:
            messages.error(request, '❌ Cannot delete this Product Type because it is being used by existing products.')
        return redirect('product-attributes')


# Product Variant CRUD
@method_decorator(login_required, name='dispatch')
class ProductVariantAddView(View):
    def post(self, request):
        from django.db import IntegrityError
        name = request.POST.get('name')
        if name:
            try:
                auth_user = AuthUser.objects.get(id=request.user.id)
                ProductVariants.objects.create(name=name, created_by_admin=auth_user)
                messages.success(request, 'Product Variant added successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Product Variant already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class ProductVariantEditView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        product_variant = get_object_or_404(ProductVariants, pk=pk)
        name = request.POST.get('name')
        if name:
            try:
                product_variant.name = name
                product_variant.save()
                messages.success(request, 'Product Variant updated successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Product Variant name already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class ProductVariantDeleteView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        product_variant = get_object_or_404(ProductVariants, pk=pk)
        try:
            product_variant.delete()
            messages.success(request, 'Product Variant deleted successfully!')
        except IntegrityError:
            messages.error(request, '❌ Cannot delete this Product Variant because it is being used by existing products.')
        return redirect('product-attributes')


# Size CRUD
@method_decorator(login_required, name='dispatch')
class SizeAddView(View):
    def post(self, request):
        from django.db import IntegrityError
        size_label = request.POST.get('size_label')
        if size_label:
            try:
                auth_user = AuthUser.objects.get(id=request.user.id)
                Sizes.objects.create(size_label=size_label, created_by_admin=auth_user)
                messages.success(request, 'Size added successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Size already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class SizeEditView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        size = get_object_or_404(Sizes, pk=pk)
        size_label = request.POST.get('size_label')
        if size_label:
            try:
                size.size_label = size_label
                size.save()
                messages.success(request, 'Size updated successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Size already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class SizeDeleteView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        size = get_object_or_404(Sizes, pk=pk)
        try:
            size.delete()
            messages.success(request, 'Size deleted successfully!')
        except IntegrityError:
            messages.error(request, '❌ Cannot delete this Size because it is being used by existing products.')
        return redirect('product-attributes')


# Size Unit CRUD
@method_decorator(login_required, name='dispatch')
class SizeUnitAddView(View):
    def post(self, request):
        from django.db import IntegrityError
        unit_name = request.POST.get('unit_name')
        if unit_name:
            try:
                auth_user = AuthUser.objects.get(id=request.user.id)
                SizeUnits.objects.create(unit_name=unit_name, created_by_admin=auth_user)
                messages.success(request, 'Size Unit added successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Size Unit already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class SizeUnitEditView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        size_unit = get_object_or_404(SizeUnits, pk=pk)
        unit_name = request.POST.get('unit_name')
        if unit_name:
            try:
                size_unit.unit_name = unit_name
                size_unit.save()
                messages.success(request, 'Size Unit updated successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Size Unit already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class SizeUnitDeleteView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        size_unit = get_object_or_404(SizeUnits, pk=pk)
        try:
            size_unit.delete()
            messages.success(request, 'Size Unit deleted successfully!')
        except IntegrityError:
            messages.error(request, '❌ Cannot delete this Size Unit because it is being used by existing products.')
        return redirect('product-attributes')


# Unit Price CRUD
@method_decorator(login_required, name='dispatch')
class UnitPriceAddView(View):
    def post(self, request):
        from django.db import IntegrityError
        unit_price = request.POST.get('unit_price')
        if unit_price:
            try:
                auth_user = AuthUser.objects.get(id=request.user.id)
                UnitPrices.objects.create(unit_price=unit_price, created_by_admin=auth_user)
                messages.success(request, 'Unit Price added successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Unit Price already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class UnitPriceEditView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        unit_price_obj = get_object_or_404(UnitPrices, pk=pk)
        unit_price = request.POST.get('unit_price')
        if unit_price:
            try:
                unit_price_obj.unit_price = unit_price
                unit_price_obj.save()
                messages.success(request, 'Unit Price updated successfully!')
            except IntegrityError:
                messages.error(request, '❌ This Unit Price already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class UnitPriceDeleteView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        unit_price = get_object_or_404(UnitPrices, pk=pk)
        try:
            unit_price.delete()
            messages.success(request, 'Unit Price deleted successfully!')
        except IntegrityError:
            messages.error(request, '❌ Cannot delete this Unit Price because it is being used by existing products.')
        return redirect('product-attributes')


# SRP Price CRUD
@method_decorator(login_required, name='dispatch')
class SrpPriceAddView(View):
    def post(self, request):
        from django.db import IntegrityError
        srp_price = request.POST.get('srp_price')
        if srp_price:
            try:
                auth_user = AuthUser.objects.get(id=request.user.id)
                SrpPrices.objects.create(srp_price=srp_price, created_by_admin=auth_user)
                messages.success(request, 'SRP Price added successfully!')
            except IntegrityError:
                messages.error(request, '❌ This SRP Price already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class SrpPriceEditView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        srp_price_obj = get_object_or_404(SrpPrices, pk=pk)
        srp_price = request.POST.get('srp_price')
        if srp_price:
            try:
                srp_price_obj.srp_price = srp_price
                srp_price_obj.save()
                messages.success(request, 'SRP Price updated successfully!')
            except IntegrityError:
                messages.error(request, '❌ This SRP Price already exists!')
        return redirect('product-attributes')

@method_decorator(login_required, name='dispatch')
class SrpPriceDeleteView(View):
    def post(self, request, pk):
        from django.db import IntegrityError
        srp_price = get_object_or_404(SrpPrices, pk=pk)
        try:
            srp_price.delete()
            messages.success(request, 'SRP Price deleted successfully!')
        except IntegrityError:
            messages.error(request, '❌ Cannot delete this SRP Price because it is being used by existing products.')
        return redirect('product-attributes')


class WithdrawSuccessView(ListView):
    model = Withdrawals
    context_object_name = 'withdrawals'
    template_name = "withdrawn.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = Withdrawals.objects.filter(is_archived=False).order_by('-date')
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
        products = Products.objects.all().order_by('id').select_related(
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
        price_input = request.POST.get("price_input")

        if price_input in ['UNIT', 'SRP']:
            price_type = price_input
            custom_price = None
        else:
            price_type = None
            try:
                custom_price = float(price_input)
            except (TypeError, ValueError):
                custom_price = None

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
                            messages.error(request, f"⚠️ Insufficient stock for {product}. Available: {inv.total_stock}")
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
                            price_type=price_type if reason == "SOLD" and sales_channel != "CONSIGNMENT" else None,
                            custom_price=custom_price if sales_channel == "CONSIGNMENT" or custom_price else None,
                            discount_id=discount_obj.id if discount_obj else None,
                            custom_discount_value=custom_value,
                        )

                        inv.total_stock -= quantity
                        inv.save()
                        count += 1
                    except Exception as e:
                        messages.error(request, f"❌ Error withdrawing product: {e}")

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
                            messages.error(request, f"⚠️ Insufficient stock for {material}. Available: {inv.total_stock}")
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
                        messages.error(request, f"❌ Error withdrawing raw material: {e}")

        if count > 0:
            messages.success(request, f"✅ Success! {count} item(s) withdrawn. Inventory updated!")
        else:
            messages.warning(request, "⚠️ No items withdrawn. Please enter quantity for at least one item.")

        return redirect("withdrawals")


class WithdrawalsArchiveView(View):
    def post(self, request, pk):
        withdrawal = get_object_or_404(Withdrawals, pk=pk)
        
        # Capture withdrawal data for history log
        withdrawal_data = {
            'item_type': withdrawal.item_type,
            'item_id': withdrawal.item_id,
            'quantity': str(withdrawal.quantity),
            'reason': withdrawal.reason,
            'sales_channel': withdrawal.sales_channel,
            'price_type': withdrawal.price_type,
        }
        
        withdrawal.is_archived = True
        withdrawal.save()
        
        # Create history log
        create_history_log(
            admin=request.user,
            log_category="Withdrawal Archived",
            entity_type="withdrawal",
            entity_id=withdrawal.id,
            after=withdrawal_data
        )
        
        messages.success(request, "📦 Withdrawal archived successfully.")
        page = request.GET.get('page')
        if page:
            return redirect(f"{reverse('withdrawals')}?page={page}")
        return redirect('withdrawals')


class ArchivedWithdrawalsListView(ListView):
    model = Withdrawals
    template_name = 'archived_withdrawals.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        return Withdrawals.objects.filter(is_archived=True).order_by('-date')


class WithdrawalsUnarchiveView(View):
    def post(self, request, pk):
        withdrawal = get_object_or_404(Withdrawals, pk=pk)
        withdrawal.is_archived = False
        withdrawal.save()
        messages.success(request, "✅ Withdrawal restored successfully.")
        return redirect('withdrawals-archived-list')


class WithdrawalsArchiveOldView(View):
    def post(self, request):
        from datetime import timedelta
        one_year_ago = timezone.now() - timedelta(days=365)
        archived_count = Withdrawals.objects.filter(is_archived=False, date__lt=one_year_ago).update(is_archived=True)
        messages.success(request, f"📦 {archived_count} withdrawal(s) older than 1 year have been archived.")
        return redirect('withdrawals')

class WithdrawUpdateView(UpdateView):
    model = Withdrawals
    form_class = WithdrawEditForm
    template_name = "withdraw_edit.html"
    success_url = reverse_lazy("withdrawals")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_raw_material'] = self.object.item_type == 'RAW_MATERIAL'
        return context

    def form_valid(self, form):
        withdrawal = self.get_object()
        
        # Save the original date before any changes
        original_date = withdrawal.date
        
        # Log the current time for debugging
        current_time = timezone.now()
        print(f"Current time: {current_time}")
        print(f"Original date before save: {original_date}")

        before = {
            'item_type': withdrawal.item_type,
            'item_id': withdrawal.item_id,
            'quantity': str(withdrawal.quantity),
            'reason': withdrawal.reason,
            'sales_channel': withdrawal.sales_channel,
            'price_type': withdrawal.price_type,
            'custom_price': str(withdrawal.custom_price),
            'discount_id': withdrawal.discount_id,
            'custom_discount_value': str(withdrawal.custom_discount_value),
            'date': str(original_date),
        }

        # Get the form data but don't save yet
        self.object = form.save(commit=False)
        
        # Explicitly set the date to the original date
        self.object.date = original_date
        
        # Save with update_fields to only update specific fields
        self.object.save(update_fields=[
            'item_id', 'quantity', 'reason', 'sales_channel', 
            'price_type', 'custom_price', 'discount_id', 'custom_discount_value'
        ])
        
        # Refresh from database to ensure we have the latest data
        withdrawal.refresh_from_db()
        
        print(f"Date after save: {withdrawal.date}")

        after = {
            'item_type': withdrawal.item_type,
            'item_id': withdrawal.item_id,
            'quantity': str(withdrawal.quantity),
            'reason': withdrawal.reason,
            'sales_channel': withdrawal.sales_channel,
            'price_type': withdrawal.price_type,
            'custom_price': str(withdrawal.custom_price),
            'discount_id': withdrawal.discount_id,
            'custom_discount_value': str(withdrawal.custom_discount_value),
            'date': str(withdrawal.date),
        }

        create_history_log(
            admin=self.request.user,
            log_category="Withdrawal Edited",
            entity_type="withdrawal",
            entity_id=withdrawal.id,
            before=before,
            after=after
        )

        messages.success(self.request, "✅ Withdrawal successfully updated.")
        
        # Return a redirect response instead of the original response
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "❌ Please correct the errors below.")
        return super().form_invalid(form)


class WithdrawDeleteView(DeleteView):
    model = Withdrawals
    success_url = reverse_lazy('withdrawals')

    def post(self, request, *args, **kwargs):
        """Override post to capture data before delete is called"""
        # Capture withdrawal data before deletion
        withdrawal = self.get_object()
        before = {
            'item_type': withdrawal.item_type,
            'item_id': withdrawal.item_id,
            'quantity': str(withdrawal.quantity),
            'reason': withdrawal.reason,
            'sales_channel': withdrawal.sales_channel,
            'price_type': withdrawal.price_type,
        }
        
        withdrawal_id = withdrawal.id
        
        # Call parent delete
        response = super().post(request, *args, **kwargs)
        
        # Create history log after deletion
        create_history_log(
            admin=request.user,
            log_category="Withdrawal Deleted",
            entity_type="withdrawal",
            entity_id=withdrawal_id,
            before=before
        )
        
        return response

    def get_success_url(self):
        messages.success(self.request, "🗑️ Withdrawal deleted successfully.")
        return super().get_success_url()
    
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
        return (
            Notifications.objects
            .filter(is_archived=False)
            .order_by('-created_at')
        )

    def get(self, request, *args, **kwargs):
        Notifications.objects.filter(is_read=False).update(is_read=True)
        return super().get(request, *args, **kwargs)

class NotificationsDeleteView(DeleteView):
    model = Notifications
    success_url = reverse_lazy('notifications')

    def get_success_url(self):
        messages.success(self.request, "🗑️ Notification deleted successfully.")
        return super().get_success_url()


class BulkProductBatchCreateView(View):
    template_name = "prodbatch_add.html"

    def get(self, request):
        form = BulkProductBatchForm()
        return render(request, self.template_name, {
            'form': form,
            'products': form.products
        })

    def post(self, request):
        form = BulkProductBatchForm(request.POST)

        if not form.is_valid():
            messages.error(request, "❌ Please fix the errors below before submitting.")
            return render(request, self.template_name, {
                'form': form,
                'products': form.products
            })

        batch_date = timezone.localdate()
        manufactured_date = form.cleaned_data['manufactured_date']
        deduct_raw_material = form.cleaned_data['deduct_raw_material']
        auth_user = AuthUser.objects.get(id=request.user.id)

        try:
            with transaction.atomic():
                added_any = False

                for product_info in form.products:
                    product = product_info['product']
                    qty = form.cleaned_data.get(f'product_{product.id}_qty')

                    if not qty or float(qty) <= 0:
                        continue

                    ProductBatches.objects.create(
                        product=product,
                        quantity=qty,
                        batch_date=batch_date,
                        manufactured_date=manufactured_date,
                        created_by_admin=auth_user,
                        deduct_raw_material=deduct_raw_material,
                    )
                    added_any = True

                if not added_any:
                    raise ValueError("⚠️ No product quantities were entered.")

        except Exception as e:
            error_message = str(e)

            if "Not enough stock" in error_message:
                error_message = error_message.split("CONTEXT:")[0].strip()
            elif "insufficient" in error_message.lower():
                error_message = "❌ Insufficient raw materials to create this batch."
            elif "No product quantities" in error_message:
                error_message = "⚠️ No product quantities were entered."
            else:
                error_message = f"❌ {error_message}"

            messages.error(request, error_message)

            return render(request, self.template_name, {
                'form': form,
                'products': form.products
            })

        messages.success(request, "✅ Product Batch added successfully.")
        return redirect("product-batch")


class BulkRawMaterialBatchCreateView(LoginRequiredMixin, View):
    template_name = "rawmatbatch_add.html"

    def get(self, request):
        form = BulkRawMaterialBatchForm()
        return render(request, self.template_name, {'form': form, 'raw_materials': form.rawmaterials})

    def post(self, request):
        form = BulkRawMaterialBatchForm(request.POST)
        if form.is_valid():
            batch_date = timezone.localdate()
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
        return (
            StockChanges.objects
            .filter(is_archived=False)
            .order_by('-date')
        )


class StockChangesArchiveView(View):
    def post(self, request, pk):
        stock_change = get_object_or_404(StockChanges, pk=pk)
        stock_change.is_archived = True
        stock_change.save()
        messages.success(request, "📦 Stock change archived successfully.")
        page = request.GET.get('page')
        if page:
            return redirect(f"{reverse('stock-changes')}?page={page}")
        return redirect('stock-changes')


class ArchivedStockChangesListView(ListView):
    model = StockChanges
    template_name = 'archived_stock_changes.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        return StockChanges.objects.filter(is_archived=True).order_by('-date')


class StockChangesUnarchiveView(View):
    def post(self, request, pk):
        stock_change = get_object_or_404(StockChanges, pk=pk)
        stock_change.is_archived = False
        stock_change.save()
        messages.success(request, "✅ Stock change restored successfully.")
        return redirect('stock-changes-archived-list')


class StockChangesArchiveOldView(View):
    def post(self, request):
        from datetime import timedelta
        one_year_ago = timezone.now() - timedelta(days=365)
        archived_count = StockChanges.objects.filter(is_archived=False, date__lt=one_year_ago).update(is_archived=True)
        messages.success(request, f"📦 {archived_count} stock change(s) older than 1 year have been archived.")
        return redirect('stock-changes')

def mask_email(email):
    """Mask email address for privacy: john@example.com -> j***@example.com"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        masked_local = local + '*'
    else:
        masked_local = local[0] + '*'
    
    return f"{masked_local}@{domain}"

def get_device_fingerprint(request):
    """Create unique device ID from browser characteristics"""
    import hashlib
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
    
    fingerprint_string = f"{user_agent}{accept_language}{accept_encoding}"
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()


def get_device_info(request):
    """Extract human-readable device details"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Detect browser
    if 'Chrome' in user_agent and 'Edg' not in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        browser = 'Safari'
    elif 'Edg' in user_agent:
        browser = 'Edge'
    else:
        browser = 'Unknown'
    
    # Detect OS
    if 'Windows' in user_agent:
        os = 'Windows'
    elif 'Mac' in user_agent:
        os = 'macOS'
    elif 'Linux' in user_agent:
        os = 'Linux'
    elif 'Android' in user_agent:
        os = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        os = 'iOS'
    else:
        os = 'Unknown'
    
    return {
        'browser': browser,
        'os': os,
        'device_name': f"{os} - {browser}"
    }


def send_login_notification(user, device_info, ip_address, is_new_device=False):
    """Send email notification about login"""
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils import timezone
    
    if is_new_device:
        subject = '🔐 New Device Verified - Real\'s Food Products'
        message = f'''Hello {user.username},

A new device has been verified for your account.

Device: {device_info['device_name']}
IP Address: {ip_address}
Time: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}

This device is now trusted and will not require OTP for future logins.

If this wasn't you, please secure your account immediately.

Real's Food Products Security Team'''
    else:
        subject = '✅ Login Notification - Real\'s Food Products'
        message = f'''Hello {user.username},

You recently logged in to your account.

Device: {device_info['device_name']}
IP Address: {ip_address}
Time: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}

This login was from a trusted device.

If this wasn't you, please secure your account immediately.

Real's Food Products Security Team'''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=True,
        )
        print(f"[EMAIL] Notification sent to {user.email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send notification: {e}")


def login_view(request):
    if request.method == 'POST':
        if 'otp_code' in request.POST:
            user_id = request.session.get('2fa_user_id')
            if not user_id:
                messages.error(request, "Session expired. Please login again.")
                return redirect('login')
            
            from realsproj.models import UserOTP, User2FASettings, TrustedDevice, LoginAttempt
            from django.utils import timezone
            
            try:
                user = User.objects.get(id=user_id)
                otp_code = request.POST.get('otp_code', '').strip()
                
                otp = UserOTP.objects.filter(
                    user=user,
                    otp_code=otp_code,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if otp:
                    otp.is_used = True
                    otp.save()
                    
                    device_fingerprint = get_device_fingerprint(request)
                    device_info = get_device_info(request)
                    ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
                    
                    TrustedDevice.objects.get_or_create(
                        user=user,
                        device_fingerprint=device_fingerprint,
                        defaults={
                            'device_name': device_info['device_name'],
                            'browser': device_info['browser'],
                            'os': device_info['os'],
                            'ip_address': ip_address,
                        }
                    )
                    
                    LoginAttempt.objects.create(
                        user=user,
                        username=user.username,
                        ip_address=ip_address,
                        device_fingerprint=device_fingerprint,
                        browser=device_info['browser'],
                        os=device_info['os'],
                        success=True,
                        required_otp=True,
                        is_trusted_device=True
                    )
                    
                    send_login_notification(user, device_info, ip_address, is_new_device=True)
                    
                    del request.session['2fa_user_id']
                    
                    login(request, user)
                    messages.success(request, "✅ Successfully logged in! This device is now trusted.")
                    return redirect('home')
                else:
                    messages.error(request, "❌ Invalid or expired OTP code.")
                    return render(request, '2fa_verify.html', {'user_email': user.email})
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return render(request, '2fa_verify.html')
        
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                from realsproj.models import User2FASettings, UserOTP, TrustedDevice, LoginAttempt
                import random
                from datetime import timedelta
                from django.utils import timezone
                from django.core.mail import send_mail
                from django.conf import settings
                
                device_fingerprint = get_device_fingerprint(request)
                device_info = get_device_info(request)
                ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
                
                print(f"\n{'='*60}")
                print(f"[2FA DEBUG] Login attempt for user: {user.username}")
                print(f"[2FA DEBUG] Device fingerprint: {device_fingerprint[:20]}...")
                print(f"[2FA DEBUG] Device info: {device_info}")
                print(f"[2FA DEBUG] IP Address: {ip_address}")
                
                try:
                    twofa_settings = User2FASettings.objects.get(user=user, is_enabled=True)
                    print(f"[2FA DEBUG] ✅ 2FA is ENABLED for user: {user.username}")
                    print(f"[2FA DEBUG] Backup email: {twofa_settings.backup_email or 'None (using primary)'}")
                    
                    trusted_device = TrustedDevice.objects.filter(
                        user=user,
                        device_fingerprint=device_fingerprint,
                        is_active=True
                    ).first()
                    
                    if trusted_device:
                        print(f"[2FA DEBUG] ✅ TRUSTED DEVICE FOUND: {trusted_device.device_name}")
                        print(f"[2FA DEBUG] Last used: {trusted_device.last_used}")
                    else:
                        print(f"[2FA DEBUG] ⚠️ NEW DEVICE - OTP Required")
                        all_devices = TrustedDevice.objects.filter(user=user)
                        print(f"[2FA DEBUG] Total trusted devices for user: {all_devices.count()}")
                        for dev in all_devices:
                            print(f"  - {dev.device_name} (fingerprint: {dev.device_fingerprint[:20]}...)")

                    if trusted_device:
                        print(f"[2FA DEBUG] 🔓 Allowing login from trusted device")
                        trusted_device.last_used = timezone.now()
                        trusted_device.save()
                        
                        LoginAttempt.objects.create(
                            user=user,
                            username=user.username,
                            ip_address=ip_address,
                            device_fingerprint=device_fingerprint,
                            browser=device_info['browser'],
                            os=device_info['os'],
                            success=True,
                            required_otp=False,
                            is_trusted_device=True
                        )
                        
                        send_login_notification(user, device_info, ip_address, is_new_device=False)
                        
                        login(request, user)
                        messages.success(request, f"✅ Welcome back! Logged in from trusted device.")
                        print(f"[2FA DEBUG] ✅ Login successful (trusted device)")
                        print(f"{'='*60}\n")
                        return redirect('home')
                    else:
                        print(f"[2FA DEBUG] 📧 Generating OTP for new device...")
                        otp_code = str(random.randint(100000, 999999))
                        print(f"[2FA DEBUG] OTP Code: {otp_code}")
                        
                        UserOTP.objects.create(
                            user=user,
                            otp_code=otp_code,
                            expires_at=timezone.now() + timedelta(minutes=5),
                            ip_address=ip_address
                        )
                        
                        email_to = twofa_settings.backup_email if twofa_settings.backup_email else user.email
                        print(f"[2FA DEBUG] Sending OTP to: {email_to}")
                        
                        try:
                            send_mail(
                                subject='🔐 New Device Login - OTP Required',
                                message=f'Hello {user.username},\n\nA login attempt was made from a new device:\n\nDevice: {device_info["device_name"]}\nIP Address: {ip_address}\n\nYour OTP code is: {otp_code}\n\nThis code will expire in 5 minutes.\n\nIf this wasn\'t you, please secure your account immediately.\n\nReals Food Products Security Team',
                                from_email=settings.EMAIL_HOST_USER,
                                recipient_list=[email_to],
                                fail_silently=False,
                            )
                            print(f"[2FA DEBUG] ✅ OTP email sent successfully!")
                        except Exception as email_error:
                            print(f"[2FA DEBUG] ❌ EMAIL ERROR: {email_error}")
                        
                        LoginAttempt.objects.create(
                            user=user,
                            username=user.username,
                            ip_address=ip_address,
                            device_fingerprint=device_fingerprint,
                            browser=device_info['browser'],
                            os=device_info['os'],
                            success=False,
                            required_otp=True,
                            is_trusted_device=False
                        )
                        
                        request.session['2fa_user_id'] = user.id
                        masked_email = mask_email(email_to)
                        messages.info(request, f"📧 New device detected! OTP sent to {masked_email}")
                        print(f"[2FA DEBUG] ✅ Redirecting to OTP verification page")
                        print(f"{'='*60}\n")
                        return render(request, '2fa_verify.html', {'user_email': masked_email})
                        
                except User2FASettings.DoesNotExist:
                    print(f"[2FA DEBUG] ❌ 2FA is NOT ENABLED for user: {user.username}")
                    print(f"[2FA DEBUG] Allowing direct login (no 2FA)")
                    print(f"{'='*60}\n")
                    login(request, user)
                    return redirect('home')
                except Exception as e:
                    print(f"[2FA DEBUG] ❌ EXCEPTION: {str(e)}")
                    print(f"{'='*60}\n")
                    messages.error(request, f"Failed to process login: {str(e)}")
                    return render(request, 'login.html')
            else:
                messages.error(request, "Your account is not active.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')    

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  
            login(request, user)
            messages.success(request, 'Your account has been created successfully! You can now log in.')
            return redirect('login')  
        else:
            messages.error(request, 'There were errors in your form. Please check the fields and try again.')
    else:
        form = CustomUserCreationForm() 

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


def export_sales(request):
    filter_type = request.GET.get('filter', 'date')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    qs = Sales.objects.filter(is_archived=False)

    if filter_type == "date" and start_date:
        # Parse the date string and filter by exact date
        try:
            year, month, day = start_date.split('-')
            qs = qs.filter(date__year=int(year), date__month=int(month), date__day=int(day))
        except (ValueError, AttributeError):
            pass

    elif filter_type == "month" and start_date:
        start = datetime.strptime(start_date, "%Y-%m")
        qs = qs.filter(date__year=start.year, date__month=start.month)

    elif filter_type == "year" and start_date:
        year = int(start_date)
        qs = qs.filter(date__year=year)

    elif filter_type == "range" and start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m")
        end = datetime.strptime(end_date, "%Y-%m")
        
        from calendar import monthrange
        start = start.replace(day=1)
        last_day = monthrange(end.year, end.month)[1]
        end = end.replace(day=last_day)
        qs = qs.filter(date__range=(start.date(), end.date()))

    total_sales = sum(s.amount for s in qs)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_{filter_type}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category', 'Amount', 'Date', 'Description', 'Created By'])

    for s in qs:
        writer.writerow([s.category, s.amount, s.date.strftime("%Y-%m-%d"), s.description, s.created_by_admin.username])

    writer.writerow([])
    writer.writerow(['', 'TOTAL SALES', total_sales])
    return response

def export_expenses(request):
    filter_type = request.GET.get('filter', 'date')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    qs = Expenses.objects.filter(is_archived=False)

    if filter_type == "date" and start_date:
        # Parse the date string and filter by exact date
        try:
            year, month, day = start_date.split('-')
            qs = qs.filter(date__year=int(year), date__month=int(month), date__day=int(day))
        except (ValueError, AttributeError):
            pass

    elif filter_type == "month" and start_date:
        start = datetime.strptime(start_date, "%Y-%m")
        qs = qs.filter(date__year=start.year, date__month=start.month)

    elif filter_type == "year" and start_date:
        year = int(start_date)
        qs = qs.filter(date__year=year)

    elif filter_type == "range" and start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m")
        end = datetime.strptime(end_date, "%Y-%m")

        from calendar import monthrange
        start = start.replace(day=1)
        last_day = monthrange(end.year, end.month)[1]
        end = end.replace(day=last_day)
        qs = qs.filter(date__range=(start.date(), end.date()))

    total_expenses = sum(e.amount for e in qs)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="expenses_{filter_type}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category', 'Amount', 'Date', 'Description', 'Created By'])

    for e in qs:
        writer.writerow([e.category, e.amount, e.date.strftime("%Y-%m-%d"), e.description, e.created_by_admin.username])

    writer.writerow([])
    writer.writerow(['', 'TOTAL EXPENSES', total_expenses])
    return response

class UserActivityList(ListView):
    model = User
    context_object_name = 'users'
    template_name = "user_activity_list.html"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q')
        users = User.objects.all().select_related('useractivity').order_by('username')
        if query:
            users = users.filter(username__icontains=query)
        return users


@receiver(user_logged_in)
def set_user_active(sender, user, request, **kwargs):
    activity, created = UserActivity.objects.get_or_create(user=user)
    activity.active = True
    activity.last_activity = timezone.now()
    activity.save()

@receiver(user_logged_out)
def set_user_inactive(sender, user, request, **kwargs):
    try:
        activity = UserActivity.objects.get(user=user)
        activity.active = False
        activity.last_logout = timezone.now()
        activity.save()
    except UserActivity.DoesNotExist:
        pass


def check_expirations(request):
    today = timezone.localdate()
    next_week = today + timedelta(days=7)
    next_month = today + timedelta(days=30)
    messages = []

    product_batches = (
        ProductBatches.objects
        .filter(expiration_date__lte=next_month, is_archived=False)
        .values(
            "product__product_type__name",
            "product__variant__name",
            "product__size__size_label",
            "product__size_unit__unit_name",
            "expiration_date"
        )
        .annotate(count=Count("id"))
    )

    for pb in product_batches:
        days = (pb["expiration_date"] - today).days
        if days < 0:
            status = "has expired"
        elif days == 0:
            status = "expires today"
        elif days <= 7:
            status = "will expire in a week"
        elif days <= 30:
            status = "will expire in a month"
        else:
            continue

        name = f'{pb["product__product_type__name"]} - {pb["product__variant__name"]} ({pb["product__size__size_label"] or ""} {pb["product__size_unit__unit_name"]})'
        message = f'{pb["count"]} {name} {status} ({pb["expiration_date"]})'
        messages.append(message)

    raw_batches = (
        RawMaterialBatches.objects
        .filter(expiration_date__lte=next_month, is_archived=False)
        .values("material__name", "expiration_date")
        .annotate(count=Count("id"))
    )

    for rb in raw_batches:
        days = (rb["expiration_date"] - today).days
        if days < 0:
            status = "has expired"
        elif days == 0:
            status = "expires today"
        elif days <= 7:
            status = "will expire in a week"
        elif days <= 30:
            status = "will expire in a month"
        else:
            continue

        message = f'{rb["count"]} {rb["material__name"]} {status} ({rb["expiration_date"]})'
        messages.append(message)

    if messages:
        Notifications.objects.create(
            item_type="SYSTEM",
            item_id=0,
            notification_type="EXPIRATION_ALERT",
            notification_timestamp=timezone.now(),
            is_read=False,
        )
        print("\n".join(messages))

    return JsonResponse({"status": "ok", "notifications_sent": len(messages)})


@method_decorator(login_required, name='dispatch')
class BestSellerProductsView(LoginRequiredMixin, TemplateView):
    template_name = "bestseller_products.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()

        filter_date = self.request.GET.get('month')  
        filter_year_only = self.request.GET.get('year')  
        
        filter_type = None 
        
        if filter_date:
            try:
                year, month = filter_date.split('-')
                current_year = int(year)
                current_month = int(month)
                filter_month = current_month
                filter_year = current_year
                filter_type = 'month'
            except (ValueError, AttributeError):
                current_month = now.month
                current_year = now.year
                filter_month = None
                filter_year = None

        elif filter_year_only:
            try:
                current_year = int(filter_year_only)
                current_month = None
                filter_month = None
                filter_year = current_year
                filter_type = 'year'
            except (ValueError, TypeError):
                current_month = now.month
                current_year = now.year
                filter_month = None
                filter_year = None

        else:
            current_month = now.month
            current_year = now.year
            filter_month = None
            filter_year = None

        filters = {
            'item_type': 'PRODUCT',
            'reason': 'SOLD',
            'is_archived': False,
            'date__year': current_year
        }
        
        if filter_type != 'year':
            filters['date__month'] = current_month

        withdrawals = Withdrawals.objects.filter(**filters).values('item_id', 'quantity', 'custom_price')

        product_sales = {}
        for w in withdrawals:
            product_id = w['item_id']
            quantity = w['quantity'] or 0
            price = w['custom_price'] or 0
            
            if product_id not in product_sales:
                product_sales[product_id] = {
                    'total_quantity': 0,
                    'total_revenue': 0
                }
            
            product_sales[product_id]['total_quantity'] += quantity
            product_sales[product_id]['total_revenue'] += quantity * price

        sold_products_list = []
        for product_id, sales_data in product_sales.items():
            try:
                product = Products.objects.select_related(
                    'product_type', 'variant', 'size', 'size_unit'
                ).get(id=product_id)
                
                sold_products_list.append({
                    'item_id': product_id,
                    'product__product_type__name': product.product_type.name,
                    'product__variant__name': product.variant.name,
                    'product__size__size_label': product.size.size_label if product.size else '',
                    'product__size_unit__unit_name': product.size_unit.unit_name,
                    'total_quantity': sales_data['total_quantity'],
                    'total_revenue': sales_data['total_revenue']
                })
            except Products.DoesNotExist:
                continue

        sold_products_list.sort(key=lambda x: x['total_quantity'], reverse=True)
        
        best_sellers = sold_products_list[:10]
        
        sold_product_ids = [p['item_id'] for p in sold_products_list]
        no_sales_products = Products.objects.filter(
            is_archived=False
        ).exclude(id__in=sold_product_ids).select_related(
            'product_type', 'variant', 'size', 'size_unit'
        )
        
        low_sellers_list = []
        
        if len(sold_products_list) > 10:
            low_sellers_from_sold = sorted(sold_products_list, key=lambda x: x['total_quantity'])[:10]
            low_sellers_list.extend(low_sellers_from_sold)
        else:
            low_sellers_list.extend(sorted(sold_products_list, key=lambda x: x['total_quantity']))

        remaining_slots = 10 - len(low_sellers_list)
        if remaining_slots > 0:
            for product in no_sales_products[:remaining_slots]:
                low_sellers_list.append({
                    'item_id': product.id,
                    'product__product_type__name': product.product_type.name,
                    'product__variant__name': product.variant.name,
                    'product__size__size_label': product.size.size_label if product.size else '',
                    'product__size_unit__unit_name': product.size_unit.unit_name,
                    'total_quantity': 0,
                    'total_revenue': 0
                })
        
        low_sellers = low_sellers_list[:10]
        total_quantity = sum(p['total_quantity'] for p in sold_products_list)
        total_revenue = sum(p['total_revenue'] for p in sold_products_list)
        total_products = len(sold_products_list)
        average_revenue = total_revenue / total_products if total_products > 0 else 0
        available_years = Withdrawals.objects.filter(
            item_type='PRODUCT',
            reason='SOLD',
            is_archived=False
        ).dates('date', 'year', order='DESC')
        
        context['best_sellers'] = best_sellers
        context['low_sellers'] = low_sellers
        context['total_products'] = total_products
        context['total_quantity'] = total_quantity
        context['total_revenue'] = total_revenue
        context['average_revenue'] = average_revenue
        context['no_sales_products'] = no_sales_products
        context['current_month'] = current_month
        context['current_year'] = current_year
        context['filter_month'] = filter_month
        context['filter_year'] = filter_year
        context['filter_type'] = filter_type
        
        if filter_type == 'year':
            context['current_month_name'] = None
            context['filter_month_name'] = None
            context['filter_month_value'] = ''
        else:
            context['current_month_name'] = datetime(current_year, current_month, 1).strftime('%B')
            context['filter_month_name'] = datetime(current_year, current_month, 1).strftime('%B')
            context['filter_month_value'] = f"{current_year}-{current_month:02d}"
        
        context['available_years'] = [d.year for d in available_years]
        context['months'] = [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]
        
        return context

@login_required
def database_backup(request):
    """
    Generate and download a Django JSON fixture backup
    """
    from django.http import HttpResponse
    from django.core import serializers
    from django.apps import apps
    from datetime import datetime
    import json
    
    if request.method == 'POST':
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'reals_backup_{timestamp}.json'
            
            # Get all models from realsproj app (including managed=False)
            app_models = apps.get_app_config('realsproj').get_models()
            
            # Serialize all data
            all_data = []
            for model in app_models:
                try:
                    # Get all objects from this model
                    queryset = model.objects.all()
                    if queryset.exists():
                        model_data = serializers.serialize('json', queryset)
                        all_data.extend(json.loads(model_data))
                except Exception as e:
                    # Skip models that can't be serialized
                    print(f"Skipping {model.__name__}: {str(e)}")
                    continue
            
            # Convert to JSON string with pretty formatting
            json_content = json.dumps(all_data, indent=2, ensure_ascii=False)
            
            # Create JSON response
            response = HttpResponse(
                json_content,
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Log the backup action
            auth_user = AuthUser.objects.get(id=request.user.id)
            
            # Get or create HistoryLogTypes for backup
            log_type, created = HistoryLogTypes.objects.get_or_create(
                category='Database Backup',
                defaults={'created_by_admin': auth_user}
            )
            
            HistoryLog.objects.create(
                admin_id=auth_user.id,
                log_type_id=log_type.id,
                log_date=timezone.now(),
                entity_type='system',
                entity_id=0
            )
            
            messages.success(request, '✅ Database backup created successfully!')
            return response
            
        except Exception as e:
            messages.error(request, f'❌ Backup error: {str(e)}')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    return redirect('home')


@login_required
def financial_loss(request):
    """View for displaying financial losses from expired and damaged items"""

    product_withdrawals = Withdrawals.objects.filter(
        item_type='PRODUCT',
        reason__in=['EXPIRED', 'DAMAGED'],
        is_archived=False
    ).select_related('created_by_admin').order_by('-date')

    raw_material_withdrawals = Withdrawals.objects.filter(
        item_type='RAW_MATERIAL',
        reason__in=['EXPIRED', 'DAMAGED'],
        is_archived=False
    ).select_related('created_by_admin').order_by('-date')

    product_loss_data = []
    total_product_loss = Decimal('0.00')
    
    for withdrawal in product_withdrawals:
        try:
            product = Products.objects.select_related(
                'product_type', 'variant', 'size', 'size_unit', 'unit_price'
            ).get(id=withdrawal.item_id)
            
            loss_amount = Decimal(withdrawal.quantity) * product.unit_price.unit_price
            total_product_loss += loss_amount
            
            product_loss_data.append({
                'date': withdrawal.date,
                'product_name': str(product),
                'quantity': withdrawal.quantity,
                'unit_price': product.unit_price.unit_price,
                'reason': withdrawal.reason,
                'get_reason_display': withdrawal.get_reason_display(),
                'loss_amount': loss_amount
            })
        except Products.DoesNotExist:
            continue

    raw_material_loss_data = []
    total_raw_material_loss = Decimal('0.00')
    
    for withdrawal in raw_material_withdrawals:
        try:
            material = RawMaterials.objects.select_related('unit').get(id=withdrawal.item_id)
            
            loss_amount = Decimal(withdrawal.quantity) * material.price_per_unit
            total_raw_material_loss += loss_amount
            
            raw_material_loss_data.append({
                'date': withdrawal.date,
                'material_name': material.name,
                'quantity': withdrawal.quantity,
                'unit_name': material.unit.unit_name,
                'price_per_unit': material.price_per_unit,
                'reason': withdrawal.reason,
                'get_reason_display': withdrawal.get_reason_display(),
                'loss_amount': loss_amount
            })
        except RawMaterials.DoesNotExist:
            continue
    
    total_loss = total_product_loss + total_raw_material_loss
    
    context = {
        'product_withdrawals': product_loss_data,
        'raw_material_withdrawals': raw_material_loss_data,
        'product_loss': total_product_loss,
        'raw_material_loss': total_raw_material_loss,
        'total_loss': total_loss,
    }
    
    return render(request, 'financial_loss.html', context)


@login_required
def financial_loss_export(request):
    """Export financial loss data to CSV"""
    filter_type = request.GET.get('filter', 'date')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    product_qs = Withdrawals.objects.filter(
        item_type='PRODUCT',
        reason__in=['EXPIRED', 'DAMAGED'],
        is_archived=False
    )

    raw_material_qs = Withdrawals.objects.filter(
        item_type='RAW_MATERIAL',
        reason__in=['EXPIRED', 'DAMAGED'],
        is_archived=False
    )

    if filter_type == "date" and start_date:
        try:
            year, month, day = start_date.split('-')
            product_qs = product_qs.filter(date__year=int(year), date__month=int(month), date__day=int(day))
            raw_material_qs = raw_material_qs.filter(date__year=int(year), date__month=int(month), date__day=int(day))
        except (ValueError, AttributeError):
            pass
    
    elif filter_type == "month" and start_date:
        start = datetime.strptime(start_date, "%Y-%m")
        product_qs = product_qs.filter(date__year=start.year, date__month=start.month)
        raw_material_qs = raw_material_qs.filter(date__year=start.year, date__month=start.month)
    
    elif filter_type == "year" and start_date:
        year = int(start_date)
        product_qs = product_qs.filter(date__year=year)
        raw_material_qs = raw_material_qs.filter(date__year=year)
    
    elif filter_type == "range" and start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m")
        end = datetime.strptime(end_date, "%Y-%m")
        
        from calendar import monthrange
        start = start.replace(day=1)
        last_day = monthrange(end.year, end.month)[1]
        end = end.replace(day=last_day)
        product_qs = product_qs.filter(date__range=(start.date(), end.date()))
        raw_material_qs = raw_material_qs.filter(date__range=(start.date(), end.date()))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="financial_loss_{filter_type}.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response)

    writer.writerow(['PRODUCTS - EXPIRED & DAMAGED'])
    writer.writerow(['Date', 'Product', 'Quantity', 'Unit Price', 'Reason', 'Financial Loss'])
    
    total_product_loss = Decimal('0.00')
    for withdrawal in product_qs:
        try:
            product = Products.objects.select_related(
                'product_type', 'variant', 'size', 'size_unit', 'unit_price'
            ).get(id=withdrawal.item_id)
            
            loss_amount = Decimal(withdrawal.quantity) * product.unit_price.unit_price
            total_product_loss += loss_amount
            
            writer.writerow([
                withdrawal.date.strftime("%Y-%m-%d %H:%M"),
                str(product),
                withdrawal.quantity,
                product.unit_price.unit_price,
                withdrawal.get_reason_display(),
                f"{loss_amount:.2f}"
            ])
        except Products.DoesNotExist:
            continue
    
    writer.writerow([])
    writer.writerow(['', '', '', '', 'TOTAL PRODUCT LOSS', f"₱{total_product_loss:.2f}"])
    writer.writerow([])

    writer.writerow(['RAW MATERIALS - EXPIRED & DAMAGED'])
    writer.writerow(['Date', 'Raw Material', 'Quantity', 'Price per Unit', 'Reason', 'Financial Loss'])
    
    total_raw_material_loss = Decimal('0.00')
    for withdrawal in raw_material_qs:
        try:
            material = RawMaterials.objects.select_related('unit').get(id=withdrawal.item_id)
            
            loss_amount = Decimal(withdrawal.quantity) * material.price_per_unit
            total_raw_material_loss += loss_amount
            
            writer.writerow([
                withdrawal.date.strftime("%Y-%m-%d %H:%M"),
                f"{material.name} ({material.unit.unit_name})",
                withdrawal.quantity,
                material.price_per_unit,
                withdrawal.get_reason_display(),
                f"{loss_amount:.2f}"
            ])
        except RawMaterials.DoesNotExist:
            continue
    
    writer.writerow([])
    writer.writerow(['', '', '', '', 'TOTAL RAW MATERIAL LOSS', f"₱{total_raw_material_loss:.2f}"])
    writer.writerow([])

    total_loss = total_product_loss + total_raw_material_loss
    writer.writerow(['', '', '', '', 'TOTAL FINANCIAL LOSS', f"₱{total_loss:.2f}"])
    
    return response

@login_required
def setup_2fa(request):
    """Enable 2FA for the current user"""
    from realsproj.models import User2FASettings
    
    if request.method == 'POST':
        backup_email = request.POST.get('backup_email', '').strip()
        
        # Create or update 2FA settings
        settings, created = User2FASettings.objects.get_or_create(
            user=request.user,
            defaults={
                'is_enabled': True,
                'method': 'email',
                'backup_email': backup_email if backup_email else None
            }
        )
        
        if not created:
            settings.is_enabled = True
            settings.backup_email = backup_email if backup_email else None
            settings.save()
        
        messages.success(request, "✅ Two-Factor Authentication has been enabled!")
        return redirect('profile')
    
    # GET request - show setup form
    try:
        twofa_settings = User2FASettings.objects.get(user=request.user)
    except User2FASettings.DoesNotExist:
        twofa_settings = None
    
    return render(request, '2fa_setup.html', {
        'user_email': request.user.email,
        'twofa_settings': twofa_settings
    })


@login_required
def disable_2fa(request):
    """Disable 2FA for the current user"""
    from realsproj.models import User2FASettings
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        # Verify password before disabling
        if not request.user.check_password(password):
            messages.error(request, "❌ Incorrect password. Cannot disable 2FA.")
            return redirect('profile')
        
        try:
            settings = User2FASettings.objects.get(user=request.user)
            settings.is_enabled = False
            settings.save()
            messages.success(request, "✅ Two-Factor Authentication has been disabled.")
        except User2FASettings.DoesNotExist:
            messages.info(request, "2FA was not enabled.")
        
        return redirect('profile')
    
    return redirect('profile')