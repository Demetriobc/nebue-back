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
from datetime import timedelta
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


def capitalize_month(month_string):
    """
    Capitaliza o primeiro caractere da string do mês.
    Ex: "dezembro de 2025" -> "Dezembro de 2025"
    """
    if not month_string:
        return month_string
    return month_string[0].upper() + month_string[1:]


@login_required
def dashboard_view(request):
    """
    Dashboard principal com filtro de mês e tratamento completo de erros.
    Garante que sempre retorna um contexto válido.
    """
    try:
        # ========================================
        # 1. PROCESSAMENTO DO FILTRO DE MÊS
        # ========================================
        selected_month = request.GET.get('month', '')
        now = timezone.now()
        
        # Gerar lista de meses disponíveis (últimos 12 meses)
        available_months = []
        for i in range(12):
            month_date = now - timedelta(days=30 * i)
            # Normalizar para primeiro dia do mês
            month_date = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            available_months.append({
                'value': month_date.strftime('%Y-%m'),
                'label': capitalize_month(month_date.strftime('%B de %Y'))
            })
        
        # Determinar range de datas para filtro
        if selected_month:
            try:
                year, month = map(int, selected_month.split('-'))
                start_date = timezone.datetime(year, month, 1)
                start_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
                
                # Último dia do mês
                if month == 12:
                    end_date = timezone.datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = timezone.datetime(year, month + 1, 1) - timedelta(days=1)
                
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59)) if timezone.is_naive(end_date) else end_date.replace(hour=23, minute=59, second=59)
                
                current_month_label = capitalize_month(start_date.strftime('%B de %Y'))
                
            except (ValueError, AttributeError) as e:
                logger.warning(f"Formato de mês inválido: {selected_month} - {e}")
                # Se formato inválido, usar mês atual
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                current_month_label = capitalize_month(now.strftime('%B de %Y'))
                selected_month = ''
        else:
            # Mês atual por padrão
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            current_month_label = capitalize_month(now.strftime('%B de %Y'))

        # ========================================
        # 2. CONTEXTO PADRÃO (valores seguros)
        # ========================================
        context = {
            # Filtro de mês
            'available_months': available_months,
            'selected_month': selected_month,
            'current_month': current_month_label,
            
            # Estatísticas
            'total_balance': Decimal('0.00'),
            'month_income': Decimal('0.00'),
            'month_expenses': Decimal('0.00'),
            'month_balance': Decimal('0.00'),
            'active_accounts_count': 0,
            
            # Dados
            'recent_transactions': [],
            'top_categories': [],
            'category_chart_data': '[]',
            'monthly_chart_data': json.dumps({
                'labels': [], 
                'income': [], 
                'expense': []
            }),
        }

        # Imports dentro para evitar circular imports
        try:
            from accounts.models import Account
            from transactions.models import Transaction
        except ImportError as e:
            logger.error(f"Erro ao importar models: {e}")
            messages.error(request, 'Erro de configuração do sistema.')
            return render(request, 'dashboard.html', context)

        user = request.user

        # ========================================
        # 3. SALDO TOTAL (todas as contas ativas)
        # ========================================
        try:
            accounts = Account.objects.filter(user=user, is_active=True)
            context['active_accounts_count'] = accounts.count()
            
            total = accounts.aggregate(total=Sum('balance'))['total']
            context['total_balance'] = total if total else Decimal('0.00')
            
            logger.debug(f"Saldo total: R$ {context['total_balance']}")
        except Exception as e:
            logger.error(f"Erro ao calcular saldo: {e}", exc_info=True)

        # ========================================
        # 4. TRANSAÇÕES DO PERÍODO SELECIONADO
        # ========================================
        try:
            transactions = Transaction.objects.filter(
                account__user=user,
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )

            period_data = transactions.aggregate(
                income=Sum('amount', filter=Q(transaction_type='INCOME')),
                expense=Sum('amount', filter=Q(transaction_type='EXPENSE'))
            )

            context['month_income'] = period_data['income'] or Decimal('0.00')
            context['month_expenses'] = period_data['expense'] or Decimal('0.00')
            context['month_balance'] = context['month_income'] - context['month_expenses']
            
            logger.debug(f"Período {current_month_label}: +{context['month_income']} -{context['month_expenses']}")
        except Exception as e:
            logger.error(f"Erro ao calcular transações do período: {e}", exc_info=True)

        # ========================================
        # 5. TRANSAÇÕES RECENTES (do período)
        # ========================================
        try:
            context['recent_transactions'] = transactions.select_related(
                'account', 'category'
            ).order_by('-transaction_date', '-created_at')[:10]
            
            logger.debug(f"Transações recentes: {context['recent_transactions'].count()}")
        except Exception as e:
            logger.error(f"Erro ao buscar transações recentes: {e}", exc_info=True)

        # ========================================
        # 6. TOP 5 CATEGORIAS (DESPESAS do período)
        # ========================================
        try:
            top_cats = transactions.filter(
                transaction_type='EXPENSE'
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
                        'color': cat['category__color'] or '#8b5cf6'  # Violet como padrão
                    })
                context['category_chart_data'] = json.dumps(chart_data)
            
            logger.debug(f"Top {len(context['top_categories'])} categorias processadas")
        except Exception as e:
            logger.error(f"Erro ao processar categorias: {e}", exc_info=True)

        # ========================================
        # 7. GRÁFICO DE EVOLUÇÃO (últimos 6 meses)
        # ========================================
        try:
            months_data = {
                'labels': [], 
                'income': [], 
                'expense': []
            }
            
            for i in range(5, -1, -1):  # 6 meses (5 até 0)
                month_date = now - timedelta(days=30 * i)
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                # Último dia do mês
                if month_date.month == 12:
                    month_end = timezone.datetime(
                        month_date.year + 1, 1, 1
                    ) - timedelta(days=1)
                else:
                    month_end = timezone.datetime(
                        month_date.year, month_date.month + 1, 1
                    ) - timedelta(days=1)
                
                month_end = month_end.replace(hour=23, minute=59, second=59)
                
                # Garantir timezone aware
                if timezone.is_naive(month_start):
                    month_start = timezone.make_aware(month_start)
                if timezone.is_naive(month_end):
                    month_end = timezone.make_aware(month_end)

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
                month_label = month_start.strftime('%b/%y').capitalize()
                months_data['labels'].append(month_label)
                months_data['income'].append(float(month_trans['income'] or 0))
                months_data['expense'].append(float(month_trans['expense'] or 0))

            context['monthly_chart_data'] = json.dumps(months_data)
            logger.debug(f"Gráfico mensal: {len(months_data['labels'])} meses processados")
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico mensal: {e}", exc_info=True)
            # Mantém valor padrão já definido

        # ========================================
        # 8. RENDERIZA TEMPLATE
        # ========================================
        logger.info(f"Dashboard carregado para {user.email} - Período: {current_month_label}")
        return render(request, 'dashboard.html', context)

    except Exception as e:
        # Captura QUALQUER erro não tratado
        logger.exception(f"ERRO CRÍTICO no dashboard para {request.user}: {e}")
        
        messages.error(
            request, 
            'Não foi possível carregar o dashboard completamente. Alguns dados podem estar indisponíveis.'
        )
        
        # Retorna com contexto mínimo ao invés de página de erro
        return render(request, 'dashboard.html', {
            'available_months': [],
            'selected_month': '',
            'current_month': timezone.now().strftime('%B de %Y'),
            'total_balance': Decimal('0.00'),
            'month_income': Decimal('0.00'),
            'month_expenses': Decimal('0.00'),
            'month_balance': Decimal('0.00'),
            'active_accounts_count': 0,
            'recent_transactions': [],
            'top_categories': [],
            'category_chart_data': '[]',
            'monthly_chart_data': json.dumps({'labels': [], 'income': [], 'expense': []}),
        })


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