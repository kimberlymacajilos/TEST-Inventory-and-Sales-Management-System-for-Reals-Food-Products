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
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.db.models import Avg, Count, Sum
from datetime import datetime
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
    CustomUserCreationForm
    
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
    Discounts,
    ProductRecipes,
    UserActivity
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
import os
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.signals import user_logged_in, user_logged_out


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

def revenue_change_api(request):
    sales_data = (
        Sales.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    months = [s['month'].strftime("%Y-%m") for s in sales_data]
    revenues = [float(s['total']) for s in sales_data]

    revenue_changes = [0] 
    for i in range(1, len(revenues)):
        change = revenues[i] - revenues[i-1]
        revenue_changes.append(change)

    return JsonResponse({
        "months": months,
        "revenue_changes": revenue_changes,
    })


def monthly_report(request):
    sales = (
        Sales.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_sales=Sum("amount"))
        .order_by("month")  # 👈 ascending (oldest first)
    )

    expenses = (
        Expenses.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_expenses=Sum("amount"))
        .order_by("month")  # 👈 keep aligned
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
        # Palitan ang super().get_queryset() para magsimula sa pag-filter ng HINDI naka-archive
        queryset = (
            Products.objects.filter(is_archived=False)
            .select_related("product_type", "variant", "size", "size_unit", "unit_price", "srp_price")
            .order_by("id")
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
    


from django.shortcuts import render

def product_add_barcode(request):
    return render(request, "product_add_barcode.html")

from django.shortcuts import render

def product_scan_phone(request):
    # ito yung scanner-only view para sa phone
    return render(request, "product_scan_phone.html")

class ProductArchiveView(View):
    def post(self, request, pk):
        product = get_object_or_404(Products, pk=pk)
        product.is_archived = True
        product.save()
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

    def form_valid(self, form):
        auth_user = AuthUser.objects.get(username=self.request.user.username)
        form.instance.created_by_admin = auth_user
        self.object = form.save()

        messages.success(self.request, "✅ Product added successfully.")
        return redirect('recipe-list', product_id=self.object.id)


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

        context['recipe_list_url'] = reverse_lazy('recipe-list', kwargs={'product_id': self.object.id})
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        auth_user = AuthUser.objects.get(id=self.request.user.id)
        kwargs['created_by_admin'] = auth_user
        return kwargs
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if "delete_photo" in request.POST:
            if self.object.photo:
                try:
                    if os.path.isfile(self.object.photo.path):
                        os.remove(self.object.photo.path)
                except Exception:
                    pass
                self.object.photo = None
                self.object.save()
                messages.success(request, "Product photo deleted.")
            else:
                messages.info(request, "No photo to delete.")

            return redirect(
                reverse("product-edit", kwargs={"pk": self.object.pk})
            )

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        old_photo = None
        if self.object.photo:
            old_photo = self.object.photo.path 

        product = form.save(commit=False)
        auth_user = AuthUser.objects.get(username=self.request.user.username)
        form.instance.created_by_admin = auth_user
        self.object = form.save()

        delete_photo = self.request.POST.get("delete_photo")
        if delete_photo == "1" and old_photo and os.path.isfile(old_photo):
            os.remove(old_photo)
            product.photo = None

        if "photo" in form.changed_data and old_photo and os.path.isfile(old_photo):
            os.remove(old_photo)

        product.save()
        messages.success(self.request, "✅ Product updated successfully.")
        return redirect(self.success_url)

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
        queryset = (
            super()
            .get_queryset()
            .select_related("admin", "log_type")
            .filter(is_archived=False)
            .order_by("-log_date")
        )

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
        context['admins'] = HistoryLog.objects.filter(is_archived=False).values_list('admin__username', flat=True).distinct()
        context['logs'] = HistoryLog.objects.filter(is_archived=False).values_list('log_type__category', flat=True).distinct()
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
        queryset = Expenses.objects.filter(is_archived=False).select_related("created_by_admin").order_by("-date")

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(category__icontains=query) |
                Q(amount__icontains=query) |
                Q(date__icontains=query) |
                Q(description__icontains=query) |
                Q(created_by_admin__username__icontains=query)
            )

        # --- Category filter ---
        category = self.request.GET.get("category", "").strip()
        if category:
            queryset = queryset.filter(category__iexact=category)

        # --- Month filter (YYYY-MM) ---
        month = self.request.GET.get("month", "").strip()
        if month:
            try:
                year, month_num = month.split("-")
                queryset = queryset.filter(date__year=year, date__month=month_num)
            except (ValueError, IndexError):
                pass # Ignore invalid format

        self._full_queryset = queryset
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs_for_summary = getattr(self, 'filtered_queryset', Expenses.objects.filter(is_archived=False))

        summary = qs_for_summary.aggregate(
            total_expenses=Sum("amount"),
            average_expenses=Avg("amount"),
            expenses_count=Count("id"),
        )

        context["expenses_summary"] = summary
        
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
                Q(product__product_type__name__icontains=q) |
                Q(product__variant__name__icontains=q)
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
        return (
            Notifications.objects
            .filter(is_archived=False)
            .order_by('-created_at')
        )

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
        return (
            StockChanges.objects
            .filter(is_archived=False)
            .order_by('-date')
        )
    
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
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the new user to the database
            login(request, user)
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


def export_sales(request):
    filter_type = request.GET.get('filter', 'date')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    qs = Sales.objects.all()

    if filter_type == "date" and start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        qs = qs.filter(date__date=start.date())

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
        qs = qs.filter(date__date__range=(start, end))

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

    qs = Expenses.objects.all()

    if filter_type == "date" and start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        qs = qs.filter(date__date=start.date())

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
        qs = qs.filter(date__date__range=(start, end))

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