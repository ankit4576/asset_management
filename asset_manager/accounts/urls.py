from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.logout_view, name='logout'),
    path('technicians/', views.manage_technicians, name='manage_technicians'),
    path('technician_add/', views.add_technician, name='add_technician'),
    path('expense-types/', views.manage_expense_types, name='manage_expense_types'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('list-expenses/', views.manage_expenses, name='list_expenses'),
    path('parts_add/', views.add_part, name='add_part'),
    path('manage-parts/', views.manage_parts, name='manage_parts'),
    # path('transactions/', views.manage_part_transactions, name='manage_part_transactions'),
    # path('transactions_add/', views.add_or_edit_part_transaction, name='add_part_transaction'),
    # path('transactions_edit/<int:pk>/', views.add_or_edit_part_transaction, name='edit_part_transaction'),
    # path('transactions_delete/<int:pk>/', views.delete_part_transaction, name='delete_part_transaction'),
    # path("get-part-details/", views.get_part_details, name="get_part_details"),
    # path('transactions/', views.manage_part_transactions, name='manage_part_transactions'),

    # path('transactions_add/', views.add_or_edit_part_transaction, name='add_part_transaction'),

    # path('transactions_edit/<int:pk>/', views.add_or_edit_part_transaction, name='edit_part_transaction'),

    # path('transactions_delete/<int:pk>/', views.delete_part_transaction, name='delete_part_transaction'),

    # path("get-part-details/", views.get_part_details, name="get_part_details"),
    # path('transaction_logs/', views.transaction_logs, name='transaction_logs'),
    # path('transaction_logs/download/', views.download_logs_excel, name='download_logs_excel'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions_add/', views.create_transaction, name='create_transaction'),
    path('get-part-details/', views.get_part_details, name='get_part_details'),
    path('transaction-detail/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    
    path('amc_dashboard', views.amc_dashboard, name='amc_dashboard'),
    path('add-income_amc/', views.add_income_amc, name='add_income'),
    path('add-expense_amc/', views.add_expense_amc, name='add_expense'),
    

]
