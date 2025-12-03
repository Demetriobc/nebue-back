from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone

from transactions.models import Transaction
from categories.models import Category


class FinancialAnalytics:
    
    def __init__(self, user):
        self.user = user
        self.today = timezone.now().date()
    
    def get_spending_projection(self, months=3):
        """Calcula projeção de gastos baseado nos últimos X meses"""
        start_date = self.today - relativedelta(months=months)
        
        expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        avg_monthly = expenses / months if months > 0 else Decimal('0')
        
        projections = {
            'avg_monthly': avg_monthly,
            'projection_3_months': avg_monthly * 3,
            'projection_6_months': avg_monthly * 6,
            'projection_12_months': avg_monthly * 12,
            'based_on_months': months,
        }
        
        return projections
    
    def get_category_trends(self, months=3):
        """Analisa tendências por categoria"""
        start_date = self.today - relativedelta(months=months)
        
        category_data = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=start_date
        ).values(
            'category__name',
            'category__color',
            'category_id'
        ).annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg=Avg('amount')
        ).order_by('-total')[:10]
        
        total_expenses = sum(item['total'] for item in category_data)
        
        trends = []
        for item in category_data:
            percentage = (item['total'] / total_expenses * 100) if total_expenses > 0 else 0
            avg_monthly = item['total'] / months
            
            trends.append({
                'category_name': item['category__name'],
                'category_color': item['category__color'],
                'total': item['total'],
                'percentage': percentage,
                'avg_monthly': avg_monthly,
                'transaction_count': item['count'],
            })
        
        return trends
    
    def simulate_savings(self, monthly_saving, months=6, annual_rate=0.08):
        """Simula economia com e sem investimento"""
        simple_saving = monthly_saving * months
        
        monthly_rate = (1 + annual_rate) ** (1/12) - 1
        invested_total = Decimal('0')
        
        for month in range(months):
            invested_total = (invested_total + monthly_saving) * (1 + Decimal(str(monthly_rate)))
        
        return {
            'monthly_saving': monthly_saving,
            'months': months,
            'simple_total': simple_saving,
            'invested_total': invested_total,
            'difference': invested_total - simple_saving,
            'annual_rate': annual_rate * 100,
        }
    
    def get_smart_alerts(self):
        """Gera alertas inteligentes baseados em padrões"""
        alerts = []
        
        current_month_start = self.today.replace(day=1)
        last_month_start = (current_month_start - relativedelta(months=1))
        last_month_end = current_month_start - timedelta(days=1)
        
        current_expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start
        ).values('category__name', 'category__color').annotate(
            total=Sum('amount')
        )
        
        last_month_expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=last_month_start,
            transaction_date__lte=last_month_end
        ).values('category__name').annotate(
            total=Sum('amount')
        )
        
        last_month_dict = {item['category__name']: item['total'] for item in last_month_expenses}
        
        for current in current_expenses:
            category_name = current['category__name']
            current_total = current['total']
            last_total = last_month_dict.get(category_name, Decimal('0'))
            
            if last_total > 0:
                increase_percentage = ((current_total - last_total) / last_total) * 100
                
                if increase_percentage > 30:
                    alerts.append({
                        'type': 'danger',
                        'icon': '🚨',
                        'category': category_name,
                        'color': current['category__color'],
                        'message': f'Você gastou {increase_percentage:.0f}% a mais em {category_name} este mês',
                        'current': current_total,
                        'last': last_total,
                        'increase': increase_percentage,
                    })
                elif increase_percentage > 15:
                    alerts.append({
                        'type': 'warning',
                        'icon': '⚠️',
                        'category': category_name,
                        'color': current['category__color'],
                        'message': f'{category_name} está {increase_percentage:.0f}% acima do mês passado',
                        'current': current_total,
                        'last': last_total,
                        'increase': increase_percentage,
                    })
        
        avg_3_months = self._get_category_averages(3)
        
        for current in current_expenses:
            category_name = current['category__name']
            current_total = current['total']
            avg = avg_3_months.get(category_name, Decimal('0'))
            
            if avg > 0:
                deviation = ((current_total - avg) / avg) * 100
                
                if deviation > 25 and category_name not in [a['category'] for a in alerts]:
                    alerts.append({
                        'type': 'info',
                        'icon': '📊',
                        'category': category_name,
                        'color': current['category__color'],
                        'message': f'{category_name} está {deviation:.0f}% acima da média dos últimos 3 meses',
                        'current': current_total,
                        'average': avg,
                        'deviation': deviation,
                    })
        
        no_transactions = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__gte=current_month_start
        ).count()
        
        if no_transactions == 0:
            alerts.insert(0, {
                'type': 'warning',
                'icon': '📝',
                'message': 'Você ainda não registrou nenhuma transação este mês',
            })
        
        return alerts[:5]
    
    def _get_category_averages(self, months=3):
        """Calcula média de gastos por categoria"""
        start_date = self.today - relativedelta(months=months)
        
        category_avgs = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=start_date
        ).values('category__name').annotate(
            avg=Sum('amount')
        )
        
        return {
            item['category__name']: item['avg'] / months 
            for item in category_avgs
        }
    
    def get_financial_health_score(self):
        """Calcula score de saúde financeira (0-10)"""
        score = 10.0
        details = []
        
        from accounts.models import Account
        
        total_balance = Account.objects.filter(
            user=self.user,
            is_active=True
        ).aggregate(total=Sum('balance'))['total'] or Decimal('0')
        
        current_month_start = self.today.replace(day=1)
        
        income = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if total_balance < 0:
            score -= 3
            details.append({
                'type': 'negative',
                'text': 'Saldo total negativo (-3 pontos)'
            })
        elif total_balance < 1000:
            score -= 1.5
            details.append({
                'type': 'warning',
                'text': 'Reserva de emergência baixa (-1.5 pontos)'
            })
        else:
            details.append({
                'type': 'positive',
                'text': 'Reserva financeira positiva (+0 pontos)'
            })
        
        if income > 0:
            expense_ratio = (expenses / income) * 100
            
            if expense_ratio > 100:
                score -= 3
                details.append({
                    'type': 'negative',
                    'text': f'Gastando mais que ganha ({expense_ratio:.0f}% da renda) (-3 pontos)'
                })
            elif expense_ratio > 80:
                score -= 1.5
                details.append({
                    'type': 'warning',
                    'text': f'Gastando {expense_ratio:.0f}% da renda (-1.5 pontos)'
                })
            else:
                details.append({
                    'type': 'positive',
                    'text': f'Gastando {expense_ratio:.0f}% da renda (Bom!)'
                })
        
        transaction_count = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__gte=current_month_start
        ).count()
        
        if transaction_count < 5:
            score -= 1
            details.append({
                'type': 'warning',
                'text': 'Poucas transações registradas (-1 ponto)'
            })
        else:
            details.append({
                'type': 'positive',
                'text': 'Boa frequência de registros'
            })
        
        streak = self._calculate_streak()
        if streak >= 7:
            score += 0.5
            details.append({
                'type': 'positive',
                'text': f'Streak de {streak} dias! (+0.5 pontos)'
            })
        
        score = max(0, min(10, score))
        
        if score >= 8:
            status = 'Excelente'
            color = 'emerald'
        elif score >= 6:
            status = 'Bom'
            color = 'blue'
        elif score >= 4:
            status = 'Regular'
            color = 'amber'
        else:
            status = 'Atenção'
            color = 'red'
        
        return {
            'score': round(score, 1),
            'status': status,
            'color': color,
            'details': details,
            'streak': streak,
            'balance': total_balance,
        }
    
    def _calculate_streak(self):
        """Calcula quantos dias seguidos o usuário registrou transações"""
        streak = 0
        current_date = self.today
        
        for _ in range(30):
            has_transaction = Transaction.objects.filter(
                account__user=self.user,
                transaction_date=current_date
            ).exists()
            
            if has_transaction:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def get_category_recommendations(self):
        """Gera recomendações de economia por categoria"""
        trends = self.get_category_trends(months=3)
        recommendations = []
        
        for trend in trends[:5]:
            if trend['percentage'] > 25:
                potential_saving = trend['avg_monthly'] * Decimal('0.20')
                
                recommendations.append({
                    'category': trend['category_name'],
                    'color': trend['category_color'],
                    'current_monthly': trend['avg_monthly'],
                    'potential_saving': potential_saving,
                    'percentage': trend['percentage'],
                    'message': f'Reduza {trend["category_name"]} em 20% e economize R$ {potential_saving:.2f}/mês',
                })
        
        return recommendations[:3]
    
    def get_monthly_comparison(self):
        """Compara últimos 6 meses"""
        months_data = []
        
        for i in range(6):
            month_date = self.today - relativedelta(months=i)
            month_start = month_date.replace(day=1)
            
            if i == 0:
                month_end = self.today
            else:
                next_month = month_start + relativedelta(months=1)
                month_end = next_month - timedelta(days=1)
            
            income = Transaction.objects.filter(
                account__user=self.user,
                transaction_type=Transaction.TransactionType.INCOME,
                transaction_date__gte=month_start,
                transaction_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            expenses = Transaction.objects.filter(
                account__user=self.user,
                transaction_type=Transaction.TransactionType.EXPENSE,
                transaction_date__gte=month_start,
                transaction_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            months_data.insert(0, {
                'month': month_start.strftime('%b/%y'),
                'income': float(income),
                'expenses': float(expenses),
                'balance': float(income - expenses),
            })
        
        return months_data
    
    def get_current_vs_last_month(self):
        """Compara mês atual com mês anterior"""
        current_month_start = self.today.replace(day=1)
        last_month_start = (current_month_start - relativedelta(months=1))
        last_month_end = current_month_start - timedelta(days=1)
        
        current_expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        last_expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=last_month_start,
            transaction_date__lte=last_month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if last_expenses > 0:
            change_percentage = ((current_expenses - last_expenses) / last_expenses) * 100
        else:
            change_percentage = 0
        
        return {
            'current': current_expenses,
            'last': last_expenses,
            'change': current_expenses - last_expenses,
            'change_percentage': change_percentage,
            'is_increase': change_percentage > 0,
        }
    
    def get_spending_by_weekday(self):
        """Analisa gastos por dia da semana"""
        from django.db.models.functions import ExtractWeekDay
        
        start_date = self.today - relativedelta(months=3)
        
        weekday_data = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=start_date
        ).annotate(
            weekday=ExtractWeekDay('transaction_date')
        ).values('weekday').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('weekday')
        
        weekday_names = {
            1: 'Domingo',
            2: 'Segunda',
            3: 'Terça',
            4: 'Quarta',
            5: 'Quinta',
            6: 'Sexta',
            7: 'Sábado',
        }
        
        result = []
        for item in weekday_data:
            result.append({
                'weekday': weekday_names.get(item['weekday'], 'N/A'),
                'total': item['total'],
                'count': item['count'],
                'avg_per_transaction': item['total'] / item['count'] if item['count'] > 0 else Decimal('0'),
            })
        
        if result:
            max_spending = max(result, key=lambda x: x['total'])
            return {
                'data': result,
                'max_day': max_spending['weekday'],
                'max_amount': max_spending['total'],
            }
        
        return {'data': [], 'max_day': None, 'max_amount': Decimal('0')}
    
    def get_month_end_forecast(self):
        """Prevê gastos até o fim do mês"""
        current_month_start = self.today.replace(day=1)
        days_passed = self.today.day
        
        next_month = current_month_start + relativedelta(months=1)
        last_day = (next_month - timedelta(days=1)).day
        days_remaining = last_day - days_passed
        
        current_expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start,
            transaction_date__lte=self.today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if days_passed > 0:
            daily_avg = current_expenses / days_passed
            forecast = current_expenses + (daily_avg * days_remaining)
        else:
            forecast = Decimal('0')
        
        return {
            'current_spent': current_expenses,
            'days_passed': days_passed,
            'days_remaining': days_remaining,
            'daily_average': daily_avg if days_passed > 0 else Decimal('0'),
            'forecast_total': forecast,
            'forecast_remaining': forecast - current_expenses if forecast > current_expenses else Decimal('0'),
        }
    
    def get_recurring_transactions(self):
        """Identifica transações recorrentes"""
        start_date = self.today - relativedelta(months=3)
        
        recurring = []
        
        transactions = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=start_date
        ).values('description', 'category__name', 'amount').annotate(
            count=Count('id')
        ).filter(count__gte=2).order_by('-count')[:5]
        
        for trans in transactions:
            recurring.append({
                'description': trans['description'],
                'category': trans['category__name'],
                'amount': trans['amount'],
                'frequency': trans['count'],
            })
        
        return recurring
    
    def get_savings_tips(self):
        """Gera dicas personalizadas de economia com impacto calculado"""
        trends = self.get_category_trends(months=3)
        tips = []
        
        for trend in trends[:5]:
            if trend['percentage'] > 15:
                reduction_10 = trend['avg_monthly'] * Decimal('0.10')
                reduction_20 = trend['avg_monthly'] * Decimal('0.20')
                reduction_30 = trend['avg_monthly'] * Decimal('0.30')
                
                tips.append({
                    'category': trend['category_name'],
                    'color': trend['category_color'],
                    'current_monthly': trend['avg_monthly'],
                    'percentage': trend['percentage'],
                    'options': [
                        {
                            'reduction': '10%',
                            'amount': reduction_10,
                            'impact_6m': reduction_10 * 6,
                            'impact_12m': reduction_10 * 12,
                        },
                        {
                            'reduction': '20%',
                            'amount': reduction_20,
                            'impact_6m': reduction_20 * 6,
                            'impact_12m': reduction_20 * 12,
                        },
                        {
                            'reduction': '30%',
                            'amount': reduction_30,
                            'impact_6m': reduction_30 * 6,
                            'impact_12m': reduction_30 * 12,
                        }
                    ]
                })
        
        return tips[:3]
    
    def get_net_worth_evolution(self):
        """Calcula evolução do patrimônio líquido (saldo) ao longo do tempo"""
        from accounts.models import Account
        
        evolution = []
        
        for i in range(6, -1, -1):
            month_date = self.today - relativedelta(months=i)
            month_start = month_date.replace(day=1)
            
            if i == 0:
                month_end = self.today
            else:
                next_month = month_start + relativedelta(months=1)
                month_end = next_month - timedelta(days=1)
            
            income = Transaction.objects.filter(
                account__user=self.user,
                transaction_type=Transaction.TransactionType.INCOME,
                transaction_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            expenses = Transaction.objects.filter(
                account__user=self.user,
                transaction_type=Transaction.TransactionType.EXPENSE,
                transaction_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            net_worth = income - expenses
            
            evolution.append({
                'month': month_start.strftime('%b/%y'),
                'net_worth': float(net_worth),
            })
        
        return evolution