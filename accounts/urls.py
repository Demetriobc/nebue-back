"""
URL configuration for the accounts app.

This module defines URL patterns for managing bank accounts, including:
- List view: Display all user accounts
- Create view: Add a new account
- Update view: Edit an existing account
- Delete view: Remove an account

All views require user authentication and enforce data isolation
(users can only access their own accounts).
"""
from django.urls import path

from . import views
from . import views_budget

app_name = 'accounts'

urlpatterns = [
    path('', views.AccountListView.as_view(), name='account_list'),
    path('new/', views.AccountCreateView.as_view(), name='account_create'),
    path('<int:pk>/edit/', views.AccountUpdateView.as_view(), name='account_update'),
    path('<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),
    ##orçamento
    path('orcamentos/', views_budget.budget_list, name='budget_list'),
    path('orcamentos/novo/', views_budget.budget_create, name='budget_create'),
    path('orcamentos/<int:pk>/editar/', views_budget.budget_edit, name='budget_edit'),
    path('orcamentos/<int:pk>/excluir/', views_budget.budget_delete, name='budget_delete'),
    
    # Credit Card URLs
    path('cartoes/', views_budget.creditcard_list, name='creditcard_list'),
    path('cartoes/novo/', views_budget.creditcard_create, name='creditcard_create'),
    path('cartoes/<int:pk>/editar/', views_budget.creditcard_edit, name='creditcard_edit'),
    path('cartoes/<int:pk>/excluir/', views_budget.creditcard_delete, name='creditcard_delete'),
    path('cartoes/<int:pk>/', views_budget.creditcard_detail, name='creditcard_detail'),
]
