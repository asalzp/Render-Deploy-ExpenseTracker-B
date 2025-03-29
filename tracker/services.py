from .models import Expense
from django.db.models import Sum

def get_total_expenses():
    """Calculate total expenses."""
    return Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0

def get_expenses_by_category():
    """Group expenses by category."""
    return Expense.objects.values('category').annotate(total=Sum('amount'))

def get_monthly_expenses():
    """Group expenses by month."""
    return Expense.objects.extra(select={'month': "strftime('%%Y-%%m', date)"}).values('month').annotate(total=Sum('amount'))
