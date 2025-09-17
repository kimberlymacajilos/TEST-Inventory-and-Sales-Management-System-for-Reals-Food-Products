from django.db.models import Sum
from realsproj.models import Withdrawals, Products


sold_withdrawals = (
    Withdrawals.objects
    .filter(item_type="PRODUCT", reason="SOLD")
    .values("item_id") 
    .annotate(total_sold=Sum("quantity"))
    .order_by("-total_sold")
)
