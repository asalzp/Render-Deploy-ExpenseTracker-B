# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Transport', 'Transport'),
        ('Entertainment', 'Entertainment'),
        ('Bills', 'Bills'),
        ('Shopping', 'Shopping'),
        ('Other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than 0")

    def __str__(self):
        return f"{self.category}: ${self.amount} on {self.date}"

    def formatted_date(self):
        return self.date.strftime("%B %d, %Y")
