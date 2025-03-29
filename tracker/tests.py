from django.contrib.auth.models import User
from django.test import TestCase
from .models import Expense

class ExpenseServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        Expense.objects.create(user=self.user, category="Food", amount=50.0, date="2025-01-01")
        Expense.objects.create(user=self.user, category="Transport", amount=20.0, date="2025-01-02")

    def test_get_total_expenses(self):
        from tracker.services import get_total_expenses
        total = get_total_expenses()
        self.assertEqual(total, 70.0)

    def test_get_expenses_by_category(self):
        from tracker.services import get_expenses_by_category
        categories = get_expenses_by_category()
        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0]['total'], 50.0)
