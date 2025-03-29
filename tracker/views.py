from django.contrib.auth.models import User
from django.db.models import Sum
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.hashers import make_password
from .models import Expense
from .serializers import ExpenseSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from datetime import timedelta
from datetime import datetime


# User Registration View
@api_view(['POST'])
def register_user(request):
    """Endpoint for user registration"""
    data = request.data

    # Check if username already exists
    if User.objects.filter(username=data['username']).exists():
        return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

    # Create new user
    user = User.objects.create(
        username=data['username'],
        email=data.get('email', ''),  # Email is optional
        password=make_password(data['password'])  # Hash password before storing
    )

    return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def spending_trends(request, period):
    if period not in ['month', 'week']:
        return Response({"error": "Invalid period. Choose 'month' or 'week'."}, status=400)
    
    # Get filter parameters - support both start_date and month/year filtering
    start_date = request.GET.get('start_date')
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    # Base queryset
    queryset = Expense.objects.all()
    
    # Apply filters
    if start_date:
        # Parse start_date if provided
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(date__gte=start_date_obj)
        except ValueError:
            return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=400)
    elif month and year:
        # Filter by specific month and year
        try:
            month_int = int(month)
            year_int = int(year)
            
            # Create date range for the selected month
            start_date_obj = datetime(year=year_int, month=month_int, day=1).date()
            if month_int == 12:
                end_date_obj = datetime(year=year_int+1, month=1, day=1).date()
            else:
                end_date_obj = datetime(year=year_int, month=month_int+1, day=1).date()
                
            queryset = queryset.filter(date__gte=start_date_obj, date__lt=end_date_obj)
            
            print(f"Filtering expenses for {month_int}/{year_int}: {start_date_obj} to {end_date_obj}")
            
        except ValueError:
            return Response({"error": "Invalid month or year format."}, status=400)
    else:
        # Default to current month if no filter provided
        today = datetime.now().date()
        start_date_obj = today.replace(day=1)
        queryset = queryset.filter(date__gte=start_date_obj)
        
        # If no data in current month, don't default to previous
        # as that would be confusing with the month selector
        if not queryset.exists():
            return Response({'trends': []})
            
    # Perform aggregation based on period
    if period == 'month':
        # Break down spending into weeks within the month
        trends = queryset.annotate(week=TruncWeek('date')) \
            .values('week') \
            .annotate(total=Sum('amount')) \
            .order_by('week')
    elif period == 'week':
        # Group by day within the selected week
        trends = queryset.annotate(day=TruncDay('date')) \
            .values('day') \
            .annotate(total=Sum('amount')) \
            .order_by('day')

    data = [
        {
            'period': item['week'] if period == 'month' else item['day'],
            'total': item['total']
        }
        for item in trends
    ]
    
    return Response({'trends': data})
    
# Also update category_breakdown endpoint with similar logic
@api_view(['GET'])
def category_breakdown(request, period):
    if period not in ['month', 'week']:
        return Response({"error": "Invalid period. Choose 'month' or 'week'."}, status=400)
    
    # Get filter parameters - support both start_date and month/year filtering
    start_date = request.GET.get('start_date')
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    # Base queryset
    queryset = Expense.objects.all()
    
    # Apply filters - same logic as spending_trends
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(date__gte=start_date_obj)
        except ValueError:
            return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=400)
    elif month and year:
        try:
            month_int = int(month)
            year_int = int(year)
            
            # Create date range for the selected month
            start_date_obj = datetime(year=year_int, month=month_int, day=1).date()
            if month_int == 12:
                end_date_obj = datetime(year=year_int+1, month=1, day=1).date()
            else:
                end_date_obj = datetime(year=year_int, month=month_int+1, day=1).date()
                
            queryset = queryset.filter(date__gte=start_date_obj, date__lt=end_date_obj)
            
        except ValueError:
            return Response({"error": "Invalid month or year format."}, status=400)
    else:
        # Default to current month
        today = datetime.now().date()
        start_date_obj = today.replace(day=1)
        queryset = queryset.filter(date__gte=start_date_obj)
        
        # If no data in current month, don't default to previous
        if not queryset.exists():
            return Response({'category_breakdown': []})

    # Aggregate category totals
    categories = queryset.values('category').annotate(total=Sum('amount'))

    # Prepare the response data
    data = [{'category': item['category'], 'total': item['total']} for item in categories]
    
    return Response({
        'category_breakdown': data, 
        'period_info': {
            'month': month if month else start_date_obj.month,
            'year': year if year else start_date_obj.year
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expense_summary(request):
    user = request.user

    # Total amount spent
    total_spent = Expense.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0

    # Expense breakdown by category
    category_breakdown = (
        Expense.objects
        .filter(user=user)
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    return Response({
        "total_spent": total_spent,
        "category_breakdown": list(category_breakdown)
    })

# Expense Views
class ExpenseList(APIView):
    """Handles listing and creating expenses"""
    permission_classes = [IsAuthenticated] 
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    # Enable filtering by category and date
    filterset_fields = ['category', 'date']
    
    # Enable sorting by date or amount
    ordering_fields = ['date', 'amount']
    
    def get(self, request):
        expenses = Expense.objects.filter(user=request.user)  # Get only the logged-in user's expenses

        # Get ordering query parameter
        ordering = request.query_params.get('ordering', '')

        # Apply sorting if 'ordering' is provided
        if ordering:
            expenses = expenses.order_by(ordering)
        
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id  # Assign logged-in user

        serializer = ExpenseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExpenseDetail(APIView):
    """Handles retrieving, updating, and deleting a single expense"""
    permission_classes = [IsAuthenticated]

    def get_object(self, expense_id, user):
        """Helper method to get an expense object, ensuring it belongs to the logged-in user"""
        try:
            return Expense.objects.get(id=expense_id, user=user)  # Use 'id' here
        except Expense.DoesNotExist:
            return None

    def put(self, request, expense_id):
        """Update an expense"""
        expense = self.get_object(expense_id, request.user)
        print(f"Received PUT request for expense {expense_id}: {request.data}")
        if not expense:
            return Response({"error": "Expense not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, expense_id):
        """Delete an expense"""
        expense = self.get_object(expense_id, request.user)
        
        if not expense:
            print(f"Expense with ID {expense_id} not found.")
            return Response({"error": "Expense not found"}, status=status.HTTP_404_NOT_FOUND)

        print(f"Deleting expense with ID {expense_id}")
        expense.delete()
        print(f"Expense {expense_id} deleted successfully")

        return Response({"message": "Expense deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

# Token Views
class MyTokenObtainPairView(TokenObtainPairView):
    pass  # You can customize if needed

class MyTokenRefreshView(TokenRefreshView):
    pass
