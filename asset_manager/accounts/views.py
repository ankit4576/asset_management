import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AMCExpense, AMCIncome, Expense, ExpenseType, Technician, Transaction, TransactionItem, User, Part
from django.utils import timezone
import openpyxl
from django.db.models import F, Sum, Count, ExpressionWrapper, DecimalField
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username, password=password)
            if user.is_active:
                request.session['user_id'] = user.id
                return redirect('/dashboard/')
            else:
                return render(request, 'accounts/login.html', {'error': 'User inactive'})
        except User.DoesNotExist:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})

    return render(request, 'accounts/login.html')


# def dashboard_view(request):

#     return render(request, "accounts/dashboard.html")


# def dashboard_view(request):
#     # Get selected month/year from GET params, default to current month
#     year = int(request.GET.get('year', timezone.now().year))
#     month = int(request.GET.get('month', timezone.now().month))

#     # Validate month/year
#     try:
#         selected_date = datetime(year, month, 1)
#     except ValueError:
#         selected_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

#     start_date = selected_date
#     end_date = start_date + relativedelta(months=1) - timezone.timedelta(seconds=1)

#     # Income: Total from TransactionItem.amount
#     income_data = TransactionItem.objects.filter(
#         transaction__date__gte=start_date,
#         transaction__date__lte=end_date
#     ).aggregate(total=Sum('amount'))
#     total_income = income_data['total'] or 0

#     # Expenses
#     expenses_data = Expense.objects.filter(
#         date__gte=start_date.date(),
#         date__lte=end_date.date(),
#         is_active=True
#     ).aggregate(total=Sum('amount'))
#     total_expenses = expenses_data['total'] or 0

#     # Net Profit
#     net_profit = total_income - total_expenses

#     # Transaction & Expense Count
#     transaction_count = Transaction.objects.filter(
#         date__gte=start_date, date__lte=end_date
#     ).count()

#     expense_count = Expense.objects.filter(
#         date__gte=start_date.date(), date__lte=end_date.date(), is_active=True
#     ).count()

#     # Top 5 Parts Sold (by amount)
#     top_parts = TransactionItem.objects.filter(
#         transaction__date__gte=start_date,
#         transaction__date__lte=end_date
#     ).values('part__shipped_part_no', 'part__part_description') \
#      .annotate(total_sold=Sum('amount')) \
#      .order_by('-total_sold')[:5]

#     # Month name for display
#     month_name = calendar.month_name[month]
#     year_display = year

#     context = {
#         'total_income': total_income,
#         'total_expenses': total_expenses,
#         'net_profit': net_profit,
#         'transaction_count': transaction_count,
#         'expense_count': expense_count,
#         'top_parts': top_parts,
#         'selected_month': month,
#         'selected_year': year,
#         'month_name': month_name,
#         'year_display': year_display,
#     }
#     return render(request, 'accounts/dashboard.html', context)

def dashboard_view(request):
    # Get selected month/year
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    try:
        selected_date = datetime(year, month, 1)
    except ValueError:
        selected_date = timezone.now().replace(day=1)

    start_date = selected_date
    end_date = selected_date.replace(day=28) + timezone.timedelta(days=4)
    end_date = end_date - timezone.timedelta(days=end_date.day)

    # Filter transactions in selected month
    transactions_in_month = Transaction.objects.filter(
        date__year=year,
        date__month=month
    )

    # 1. Total Income (Charged Amount)
    income_result = TransactionItem.objects.filter(
        transaction__in=transactions_in_month
    ).aggregate(total=Sum('amount'))
    total_income = income_result['total'] or 0

    # 2. Total Part Cost (part_price from Part model)
    part_cost_result = TransactionItem.objects.filter(
        transaction__in=transactions_in_month
    ).aggregate(
        total_cost=Sum(
            ExpressionWrapper(F('part__part_price'), output_field=DecimalField(max_digits=12, decimal_places=2))
        )
    )
    total_part_cost = part_cost_result['total_cost'] or 0

    # 3. Total Expenses
    expense_result = Expense.objects.filter(
        date__year=year,
        date__month=month,
        is_active=True
    ).aggregate(total=Sum('amount'))
    total_expenses = expense_result['total'] or 0

    # 4. Balance = Income - (Part Cost + Expenses)
    balance = total_income - (total_part_cost + total_expenses)

    # Counts
    transaction_count = transactions_in_month.count()
    expense_count = Expense.objects.filter(date__year=year, date__month=month).count()

    context = {
        'total_income': total_income,
        'total_part_cost': total_part_cost,
        'total_expenses': total_expenses,
        'balance': balance,
        'transaction_count': transaction_count,
        'expense_count': expense_count,
        'selected_month': month,
        'selected_year': year,
        'month_name': calendar.month_name[month],
        'year_display': year,
    }
    return render(request, 'accounts/dashboard.html', context)


def logout_view(request):
    request.session.flush()
    return redirect('/login/')


def add_technician(request):
    message = None
    error = None

    # Only staff users not already linked to a technician
    users = User.objects.filter(user_type='staff').exclude(technician__isnull=False)

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        is_active = True if request.POST.get("is_active") == "on" else False
        user_id = request.POST.get("user")

        try:
            technician = Technician(
                name=name,
                email=email,
                phone=phone,
                address=address,
                is_active=is_active,
                date_joined=timezone.now()
            )

            if user_id:
                user = User.objects.get(id=user_id)
                technician.user = user

            technician.save()
            message = "Technician added successfully!"
        except Exception as e:
            error = f"Error: {str(e)}"

    return render(request, "accounts/add_technician.html", {"users": users, "message": message, "error": error})


def manage_technicians(request):
    users = User.objects.filter(user_type='staff', technician__isnull=True)
    technicians = Technician.objects.all().order_by('-date_joined')

    if request.method == "POST":
        action = request.POST.get("action")
        tech_id = request.POST.get("tech_id")

        # ---------- ADD ----------
        if action == "add":
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            is_active = True if request.POST.get('is_active') == 'on' else False
            user_id = request.POST.get('user')

            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    messages.error(request, "Selected user does not exist.")
                    return redirect('manage_technicians')

            Technician.objects.create(
                name=name,
                email=email,
                phone=phone,
                address=address,
                is_active=is_active,
                user=user
            )
            messages.success(request, "Technician added successfully!")
            return redirect('manage_technicians')

        # ---------- EDIT ----------
        elif action == "edit" and tech_id:
            technician = get_object_or_404(Technician, id=tech_id)

            technician.name = request.POST.get('name')
            technician.email = request.POST.get('email')
            technician.phone = request.POST.get('phone')
            technician.address = request.POST.get('address')
            technician.is_active = True if request.POST.get('is_active') == 'on' else False

            user_id = request.POST.get('user')
            technician.user = User.objects.get(id=user_id) if user_id else None

            # If technician is inactive, deactivate linked user
            if technician.user:
                technician.user.is_active = technician.is_active
                technician.user.save()

            technician.save()
            messages.success(request, "Technician updated successfully!")
            return redirect('manage_technicians')

        # ---------- DELETE ----------
        elif action == "delete" and tech_id:
            technician = get_object_or_404(Technician, id=tech_id)
            if technician.user:
                technician.user.is_active = False
                technician.user.save()
            technician.delete()
            messages.success(request, "Technician deleted successfully!")
            return redirect('manage_technicians')

        # ---------- TOGGLE ACTIVE ----------
        elif action == "toggle" and tech_id:
            technician = get_object_or_404(Technician, id=tech_id)
            technician.is_active = not technician.is_active
            technician.save()

            # Toggle linked user
            if technician.user:
                technician.user.is_active = technician.is_active
                technician.user.save()

            messages.success(request, f"Technician {'activated' if technician.is_active else 'deactivated'} successfully!")
            return redirect('manage_technicians')

    context = {
        'users': users,
        'technicians': technicians
    }
    return render(request, 'accounts/technicians_list.html', context)



def manage_expense_types(request):
    if request.method == "POST":
        action = request.POST.get("action")

        # Add or Edit
        if action == "add_or_edit":
            et_id = request.POST.get("id")
            name = request.POST.get("name").strip()
            is_active = True if request.POST.get("is_active") == "on" else False

            if et_id:  # Edit existing
                et = ExpenseType.objects.get(id=et_id)
                et.name = name
                et.is_active = is_active
                et.save()
                messages.success(request, "Expense Type updated successfully!")
            else:  # Add new
                ExpenseType.objects.create(name=name, is_active=is_active)
                messages.success(request, "Expense Type added successfully!")

        # Delete
        elif action == "delete":
            et_id = request.POST.get("id")
            ExpenseType.objects.filter(id=et_id).delete()
            messages.success(request, "Expense Type deleted successfully!")

        # Toggle status
        elif action == "toggle":
            et_id = request.POST.get("id")
            et = ExpenseType.objects.get(id=et_id)
            et.is_active = not et.is_active
            et.save()
            messages.success(request, f"Expense Type {'activated' if et.is_active else 'deactivated'} successfully!")

        return redirect("manage_expense_types")

    expense_types = ExpenseType.objects.all().order_by("-created_at")
    return render(request, "accounts/manage_expense_types.html", {"expense_types": expense_types})

def add_expense(request):
    expense_types = ExpenseType.objects.filter(is_active=True)

    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        reason_id = request.POST.get('reason')
        description = request.POST.get('description')
        date = request.POST.get('date')
        amount = request.POST.get('amount')

        reason = ExpenseType.objects.get(id=reason_id) if reason_id else None

        Expense.objects.create(
            user_name=user_name,
            reason=reason,
            description=description,
            date=date,
            amount=amount,
            is_active=True
        )
        messages.success(request, "Expense added successfully!")
        return redirect('list_expenses')  # redirect to listing after adding

    return render(request, 'accounts/add_expense.html', {
        'expense_types': expense_types
    })


# View for listing, editing, and deleting expenses
def manage_expenses(request):
    expenses = Expense.objects.all().order_by('-id')
    expense_types = ExpenseType.objects.filter(is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        expense_id = request.POST.get('expense_id')

        if action == 'add':
            user_name = request.POST.get('user_name')
            reason_id = request.POST.get('reason')
            description = request.POST.get('description')
            date = request.POST.get('date')
            amount = request.POST.get('amount')

            reason = ExpenseType.objects.get(id=reason_id) if reason_id else None

            Expense.objects.create(
                user_name=user_name,
                reason=reason,
                description=description,
                date=date,
                amount=amount,
                is_active=True
            )
            messages.success(request, "Expense added successfully!")

        elif action == 'edit' and expense_id:
            exp = get_object_or_404(Expense, id=expense_id)
            exp.user_name = request.POST.get('user_name')
            reason_id = request.POST.get('reason')
            exp.reason = ExpenseType.objects.get(id=reason_id) if reason_id else None
            exp.description = request.POST.get('description')
            exp.date = request.POST.get('date')
            exp.amount = request.POST.get('amount')
            exp.save()
            messages.success(request, "Expense updated successfully!")

        elif action == 'delete' and expense_id:
            exp = get_object_or_404(Expense, id=expense_id)
            exp.delete()
            messages.success(request, "Expense deleted successfully!")

        return redirect('list_expenses')

    return render(request, 'accounts/list_expenses.html', {
        'expenses': expenses,
        'expense_types': expense_types
    })


def add_part(request):
    if request.method == "POST":
        shipped_part_no = request.POST.get('shipped_part_no')
        part_price = request.POST.get('part_price')
        part_description = request.POST.get('part_description')

        if not part_price or not part_description:
            messages.error(request, "Please fill all required fields.")
            return redirect('add_part')

        Part.objects.create(
            shipped_part_no=shipped_part_no,
            part_price=part_price,
            part_description=part_description
        )
        messages.success(request, "Part added successfully!")
        return redirect('manage_parts')

    return render(request, 'accounts/add_parts.html')

def manage_parts(request):
    parts = Part.objects.all().order_by('-date_added')

    if request.method == "POST":
        action = request.POST.get("action")
        part_id = request.POST.get("part_id")

        if action == "add":
            shipped_part_no = request.POST.get('shipped_part_no')
            part_price = request.POST.get('part_price')
            part_description = request.POST.get('part_description')

            if not part_price or not part_description:
                messages.error(request, "Please fill all required fields.")
                return redirect('manage_parts')

            Part.objects.create(
                shipped_part_no=shipped_part_no,
                part_price=part_price,
                part_description=part_description
            )
            messages.success(request, "Part added successfully!")
            return redirect('manage_parts')

        elif action == "edit" and part_id:
            part = get_object_or_404(Part, id=part_id)
            part.shipped_part_no = request.POST.get('shipped_part_no')
            part.part_price = request.POST.get('part_price')
            part.part_description = request.POST.get('part_description')
            part.save()
            messages.success(request, "Part updated successfully!")
            return redirect('manage_parts')

        elif action == "delete" and part_id:
            part = get_object_or_404(Part, id=part_id)
            part.delete()
            messages.success(request, "Part deleted successfully!")
            return redirect('manage_parts')

    return render(request, 'accounts/parts_list.html', {'parts': parts})

def create_transaction(request):
    technicians = Technician.objects.filter(is_active=True)

    if request.method == "POST":
        caller_id = request.POST.get("caller_id", "").strip()
        source_of_income = request.POST.get("source_of_income", "").strip()
        technician_id = request.POST.get("technician")

        if not all([caller_id, source_of_income, technician_id]):
            return render(request, 'accounts/part_transaction_form.html', {
                'technicians': technicians,
                'error': 'All fields are required.'
            })

        try:
            technician = Technician.objects.get(id=technician_id)
        except Technician.DoesNotExist:
            technician = None

        transaction = Transaction.objects.create(
            caller_id=caller_id,
            source_of_income=source_of_income,
            technician=technician,
        )

        # Process parts from part_no[] and amount[]
        part_nos = request.POST.getlist("part_no[]")
        amounts = request.POST.getlist("amount[]")

        saved_count = 0
        for i, part_no in enumerate(part_nos):
            part_no = part_no.strip()
            if not part_no or i >= len(amounts):
                continue
            amount_str = amounts[i]
            try:
                amount = Decimal(amount_str)
                if amount < 0:
                    continue
                part = Part.objects.get(shipped_part_no=part_no)
                TransactionItem.objects.create(
                    transaction=transaction,
                    part=part,
                    amount=amount
                )
                saved_count += 1
            except (Part.DoesNotExist, InvalidOperation, ValueError):
                continue  # Skip invalid entries

        if saved_count == 0:
            transaction.delete()
            return render(request, 'accounts/part_transaction_form.html', {
                'technicians': technicians,
                'error': 'At least one valid part with amount is required.'
            })

        return redirect('transaction_list')  # or whatever your list URL name is

    return render(request, 'accounts/part_transaction_form.html', {
        'technicians': technicians
    })

def get_part_details(request):
    part_no = request.GET.get('part_no', '').strip()
    if not part_no:
        return JsonResponse({'error': 'Part number required'}, status=400)

    try:
        part = Part.objects.get(shipped_part_no=part_no)
        return JsonResponse({
            'description': part.part_description,
            'retail_price': float(part.part_price),
        })
    except Part.DoesNotExist:
        return JsonResponse({'error': 'Part not found'}, status=404)
    

def transaction_list(request):
    transactions = Transaction.objects.select_related('technician') \
                                     .prefetch_related('items__part') \
                                     .all().order_by('-date')

    today = timezone.now().date()
    month_start = today.replace(day=1)

    context = {
        'transactions': transactions,
        'technicians': Technician.objects.filter(is_active=True),

        'total_transactions': transactions.count(),
        'today_total': transactions.filter(date__date=today).aggregate(t=Sum('items__amount'))['t'] or 0,
        'month_total': transactions.filter(date__date__gte=month_start).aggregate(t=Sum('items__amount'))['t'] or 0,
        'grand_total': transactions.aggregate(t=Sum('items__amount'))['t'] or 0,
        'today': today.strftime('%Y-%m-%d'),
    }
    return render(request, 'accounts/transaction_list.html', context)    

def transaction_detail(request, pk):
    trans = get_object_or_404(Transaction, pk=pk)
    return render(request, 'accounts/transaction_detail_partial.html', {'trans': trans})



def amc_dashboard(request):
    total_income = AMCIncome.objects.aggregate(total=Sum('amc_amount'))['total'] or 0
    total_expense = AMCExpense.objects.aggregate(total=Sum('amount'))['total'] or 0

    balance = total_income - total_expense
    loss = total_expense - total_income if total_expense > total_income else 0

    incomes = AMCIncome.objects.order_by('-date')
    expenses = AMCExpense.objects.order_by('-date')

    return render(request, 'accounts/amc_dashboard.html', {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'loss': loss,
        'incomes': incomes,
        'expenses': expenses
    })


def add_income_amc(request):
    if request.method == "POST":
        AMCIncome.objects.create(
            date=request.POST.get('date'),
            customer_name=request.POST.get('customer_name'),
            serial_no=request.POST.get('serial_no'),
            product=request.POST.get('product'),
            amc_amount=request.POST.get('amc_amount'),
            amc_coverage=request.POST.get('amc_coverage'),
            technician_id=request.POST.get('technician')
        )
        return redirect('amc_dashboard')

    technicians = Technician.objects.all()
    return render(request, 'accounts/add_income_amc.html', {'technicians': technicians})


def add_expense_amc(request):
    if request.method == "POST":
        AMCExpense.objects.create(
            date=request.POST.get('date'),
            serial_no=request.POST.get('serial_no'),
            reason=request.POST.get('reason'),
            expencer_name=request.POST.get('expencer_name'),
            amount=request.POST.get('amount')
        )
        return redirect('amc_dashboard')

    return render(request, 'accounts/add_expense_amc.html')