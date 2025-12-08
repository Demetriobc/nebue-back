"""
Core views for the Nebue application.
"""
from django.contrib import messages
from django.shortcuts import redirect, render  
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """
    Public home page view for non-authenticated users.

    Displays welcome message, feature highlights, and CTA buttons.
    Authenticated users are automatically redirected to their dashboard.
    """
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        """
        Override get method to redirect authenticated users.

        If user is logged in, redirects to dashboard.
        Non-authenticated users see the public home page.
        """
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')

        # Add test messages to verify the message system works (optional)
        if request.GET.get('test_messages'):
            messages.success(request, 'This is a success message!')
            messages.error(request, 'This is an error message!')
            messages.warning(request, 'This is a warning message!')
            messages.info(request, 'This is an info message!')

        return super().get(request, *args, **kwargs)


@login_required
def dashboard_view(request):
    """
    Dashboard principal com tratamento completo de erros.
    Garante que sempre retorna um contexto válido.
    """
    try:
        # ========================================
        # CONTEXTO PADRÃO (valores seguros)
        # ========================================
        context = {
            'total_balance': Decimal('0.00'),
            'month_income': Decimal('0.00'),
            'month_expenses': Decimal('0.00'),
            'month_balance': Decimal('0.00'),
            'active_accounts_count': 0,
            'recent_transactions': [],
            'top_categories': [],
            'category_chart_data': '[]',
            'monthly_chart_data': json.dumps({
                'labels': [], 
                'income': [], 
                'expense': []
            }),
            'current_month': timezone.now().strftime('%B de %Y'),
        }

        # Imports dentro para evitar circular imports
        try:
            from accounts.models import Account
            from transactions.models import Transaction
        except ImportError as e:
            logger.error(f"Erro ao importar models: {e}")
            return render(request, 'dashboard_error.html', {
                'error_message': 'Erro de configuração do sistema.'
            }, status=500)

        user = request.user
        now = timezone.now()
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # ========================================
        # SALDO TOTAL
        # ========================================
        try:
            accounts = Account.objects.filter(user=user, is_active=True)
            context['active_accounts_count'] = accounts.count()
            
            total = accounts.aggregate(total=Sum('balance'))['total']
            context['total_balance'] = total if total else Decimal('0.00')
            
            logger.info(f"Saldo carregado: {context['total_balance']}")
        except Exception as e:
            logger.error(f"Erro ao calcular saldo: {e}", exc_info=True)

        # ========================================
        # TRANSAÇÕES DO MÊS
        # ========================================
        try:
            transactions = Transaction.objects.filter(
                account__user=user,
                transaction_date__gte=first_day,
                transaction_date__lte=now
            )

            month_data = transactions.aggregate(
                income=Sum('amount', filter=Q(transaction_type='INCOME')),
                expense=Sum('amount', filter=Q(transaction_type='EXPENSE'))
            )

            context['month_income'] = month_data['income'] or Decimal('0.00')
            context['month_expenses'] = month_data['expense'] or Decimal('0.00')
            context['month_balance'] = context['month_income'] - context['month_expenses']
            
            logger.info(f"Transações do mês: +{context['month_income']} -{context['month_expenses']}")
        except Exception as e:
            logger.error(f"Erro ao calcular transações: {e}", exc_info=True)

        # ========================================
        # TRANSAÇÕES RECENTES
        # ========================================
        try:
            context['recent_transactions'] = Transaction.objects.filter(
                account__user=user
            ).select_related(
                'account', 'category'
            ).order_by('-transaction_date')[:5]
            
            logger.info(f"Transações recentes: {len(context['recent_transactions'])}")
        except Exception as e:
            logger.error(f"Erro ao buscar transações recentes: {e}", exc_info=True)

        # ========================================
        # TOP 5 CATEGORIAS (DESPESAS)
        # ========================================
        try:
            top_cats = Transaction.objects.filter(
                account__user=user,
                transaction_type='EXPENSE',
                transaction_date__gte=first_day
            ).values(
                'category__name', 
                'category__color'
            ).annotate(
                total=Sum('amount')
            ).order_by('-total')[:5]

            context['top_categories'] = list(top_cats)
            
            # Dados para gráfico de pizza
            if top_cats:
                chart_data = []
                for cat in top_cats:
                    chart_data.append({
                        'name': cat['category__name'] or 'Sem categoria',
                        'total': float(cat['total']),
                        'color': cat['category__color'] or '#6366f1'
                    })
                context['category_chart_data'] = json.dumps(chart_data)
            
            logger.info(f"Top categorias: {len(context['top_categories'])}")
        except Exception as e:
            logger.error(f"Erro ao processar categorias: {e}", exc_info=True)

        # ========================================
        # GRÁFICO MENSAL (últimos 6 meses)
        # ========================================
        try:
            from datetime import timedelta
            
            months_data = {
                'labels': [], 
                'income': [], 
                'expense': []
            }
            
            for i in range(5, -1, -1):
                month_date = now - timedelta(days=30 * i)
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                # Último dia do mês
                if month_date.month == 12:
                    month_end = month_date.replace(
                        year=month_date.year + 1, 
                        month=1, 
                        day=1
                    ) - timedelta(days=1)
                else:
                    month_end = month_date.replace(
                        month=month_date.month + 1, 
                        day=1
                    ) - timedelta(days=1)
                
                month_end = month_end.replace(hour=23, minute=59, second=59)

                # Transações do mês
                month_trans = Transaction.objects.filter(
                    account__user=user,
                    transaction_date__gte=month_start,
                    transaction_date__lte=month_end
                ).aggregate(
                    income=Sum('amount', filter=Q(transaction_type='INCOME')),
                    expense=Sum('amount', filter=Q(transaction_type='EXPENSE'))
                )

                # Adiciona aos dados
                month_label = month_start.strftime('%b/%y')
                months_data['labels'].append(month_label)
                months_data['income'].append(float(month_trans['income'] or 0))
                months_data['expense'].append(float(month_trans['expense'] or 0))

            context['monthly_chart_data'] = json.dumps(months_data)
            logger.info(f"Gráfico mensal gerado: {len(months_data['labels'])} meses")
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico mensal: {e}", exc_info=True)
            # Mantém valor padrão já definido

        # ========================================
        # RENDERIZA TEMPLATE
        # ========================================
        logger.info(f"Renderizando dashboard para {user.email}")
        return render(request, 'dashboard.html', context)

    except Exception as e:
        # Captura QUALQUER erro não tratado
        logger.exception(f"ERRO CRÍTICO no dashboard para {request.user}: {e}")
        
        return render(request, 'dashboard_error.html', {
            'error_message': 'Não foi possível carregar o dashboard. Tente novamente em alguns instantes.'
        }, status=500)


def page_not_found_view(request, exception):
    """
    Custom 404 error handler.
    """
    return render(request, '404.html', status=404)


def server_error_view(request):
    """
    Custom 500 error handler.
    """
    return render(request, '500.html', status=500)