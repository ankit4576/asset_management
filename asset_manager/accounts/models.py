from django.db import models
from django.utils import timezone
from django.db.models import Sum

# Create your models here.
class User(models.Model):
    USER_TYPES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    user_type = models.CharField(max_length=50, choices=USER_TYPES, default='admin')
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.full_name} ({self.user_type})"
    

class Technician(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Linked user account if this technician has login access"
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    
class ExpenseType(models.Model):
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name  


class Expense(models.Model):
    user_name = models.CharField(max_length=150, blank=True, null=True)
    reason = models.ForeignKey(ExpenseType, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_active': True})
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reason} - ₹{self.amount}" 


class Part(models.Model):
    shipped_part_no = models.CharField(max_length=100, verbose_name="Shipped Part No.")
    part_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Part Price")
    part_description = models.TextField(verbose_name="Part Description")
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.shipped_part_no or 'No Number'} - {self.part_description}"         

class Transaction(models.Model):
    caller_id = models.CharField(max_length=100, verbose_name="Caller ID / Customer")
    source_of_income = models.CharField(max_length=200, verbose_name="Source (Cash/Card/UPI etc.)")
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    

    def __str__(self):
        return f"{self.caller_id} - {self.date.strftime('%d %b %Y')}"

    def total_amount(self):
        return sum(item.amount for item in self.items.all()) if self.items.exists() else 0


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(Part, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Charged Amount")

    def __str__(self):
        return f"{self.part.shipped_part_no} → ₹{self.amount}"
    

class AMCIncome(models.Model):
    date = models.DateField(default=timezone.now)
    customer_name = models.CharField(max_length=200)
    serial_no = models.CharField(max_length=50)
    product = models.CharField(max_length=50)  # free text
    amc_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amc_coverage = models.CharField(max_length=20, blank=True, null=True)
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.customer_name} - {self.amc_amount}"


class AMCExpense(models.Model):
    date = models.DateField(default=timezone.now)
    serial_no = models.CharField(max_length=50)
    reason = models.CharField(max_length=200)
    expencer_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.serial_no} - {self.amount}"
