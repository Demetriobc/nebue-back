import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView

from accounts.models import Account
from transactions.models import Transaction

from .forms import LoginForm, SignupForm


class LoginView(FormView):
    """
    View for user authentication with custom email-based login.
    """
    form_class = LoginForm
    template_name = 'auth/login.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=email, password=password)

        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Bem-vindo de volta, {user.email}!')
            return super().form_valid(form)
        else:
            form.add_error(None, 'Email ou senha incorretos. Por favor, tente novamente.')
            return self.form_invalid(form)


class SignupView(CreateView):
    """
    View for user registration with automatic login after signup.
    """
    form_class = SignupForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            f'Bem-vindo ao Nebue, {self.object.email}! Sua conta foi criada com sucesso.'
        )
        return response


class CustomLogoutView(DjangoLogoutView):
    """
    Custom logout view that adds a success message.
    """
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'Você saiu da sua conta com sucesso. Até logo!')
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view for authenticated users.
    """
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = datetime.now()
        current_month_start = now.replace(day=1)

        # 1. Calculate total balance
        total_balance_data = Account.objects.filter(user=user).aggregate(total=Sum('balance'))
        total_balance = total_balance_data['total'] or Decimal('0.00')

        # 2. Calculate current month income
        month_income_data = Transaction.objects.filter(
            account__user=user,
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))
        month_income = month_income_data['total'] or Decimal('0.00')

        # 3. Calculate current month expenses
        month_expenses_data = Transaction.objects.filter(
            account__user=user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))
        month_expenses = month_expenses_data['total'] or Decimal('0.00')

        # 4. Calculate month balance
        month_balance = month_income - month_expenses

        # 5. Get last 10 transactions
        recent_transactions = Transaction.objects.filter(
            account__user=user
        ).select_related('account', 'category').order_by('-transaction_date', '-created_at')[:10]

        # 6. Get top 5 expense categories
        top_categories = Transaction.objects.filter(
            account__user=user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start
        ).values('category__name', 'category__color').annotate(
            total_amount=Sum('amount')
        ).order_by('-total_amount')[:5]

        # 7. Count active accounts
        active_accounts_count = Account.objects.filter(user=user, is_active=True).count()

        # 8. Category chart data
        category_chart_data = [{
            'name': cat['category__name'],
            'total': float(cat['total_amount']),
            'color': cat['category__color']
        } for cat in top_categories]

        # 9. Monthly chart data (last 6 months)
        month_labels = []
        income_data = []
        expense_data = []

        for i in range(5, -1, -1):
            target_date = now - timedelta(days=30 * i)
            month_start = target_date.replace(day=1)
            
            if month_start.month == 12:
                next_month_start = month_start.replace(year=month_start.year + 1, month=1)
            else:
                next_month_start = month_start.replace(month=month_start.month + 1)

            month_inc = Transaction.objects.filter(
                account__user=user,
                transaction_type=Transaction.TransactionType.INCOME,
                transaction_date__gte=month_start,
                transaction_date__lt=next_month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            month_exp = Transaction.objects.filter(
                account__user=user,
                transaction_type=Transaction.TransactionType.EXPENSE,
                transaction_date__gte=month_start,
                transaction_date__lt=next_month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            month_labels.append(month_start.strftime('%b/%y'))
            income_data.append(float(month_inc))
            expense_data.append(float(month_exp))

        monthly_chart_data = {
            'labels': month_labels,
            'income': income_data,
            'expense': expense_data
        }

        context.update({
            'user': user,
            'total_balance': total_balance,
            'month_income': month_income,
            'month_expenses': month_expenses,
            'month_balance': month_balance,
            'recent_transactions': recent_transactions,
            'top_categories': top_categories,
            'active_accounts_count': active_accounts_count,
            'current_month': now.strftime('%B %Y'),
            'category_chart_data': json.dumps(category_chart_data),
            'monthly_chart_data': json.dumps(monthly_chart_data),
        })

        return context