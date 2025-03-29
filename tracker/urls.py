from django.urls import path
from .views import ExpenseList, register_user, ExpenseDetail
from .views import MyTokenObtainPairView, MyTokenRefreshView, expense_summary, spending_trends, category_breakdown

urlpatterns = [
path('register/', register_user, name='register'),
path('expenses/', ExpenseList.as_view(), name='expense-list'),
path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
path('token/refresh/', MyTokenRefreshView.as_view(), name='token_refresh'),
path('expenses/<int:expense_id>/', ExpenseDetail.as_view(), name='expense-detail'),
path('expense-summary/', expense_summary, name='expense_summary'),
path('spending-trends/<str:period>/', spending_trends, name='spending-trends'),
path('category-breakdown/<str:period>/', category_breakdown, name='category-breakdown'),
]
