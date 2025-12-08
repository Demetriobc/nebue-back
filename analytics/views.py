from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
import json

from .utils import FinancialAnalytics


class InsightsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/insights.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        analytics = FinancialAnalytics(self.request.user)
        
        context['projections'] = analytics.get_spending_projection(months=3)
        context['category_trends'] = analytics.get_category_trends(months=3)
        context['smart_alerts'] = analytics.get_smart_alerts()
        context['health_score'] = analytics.get_financial_health_score()
        context['recommendations'] = analytics.get_category_recommendations()
        context['monthly_comparison'] = analytics.get_monthly_comparison()
        context['current_vs_last'] = analytics.get_current_vs_last_month()
        context['weekday_analysis'] = analytics.get_spending_by_weekday()
        context['forecast'] = analytics.get_month_end_forecast()
        context['recurring'] = analytics.get_recurring_transactions()
        context['savings_tips'] = analytics.get_savings_tips()
        context['net_worth_evolution'] = analytics.get_net_worth_evolution()
        
        simulation_amount = Decimal('300')
        context['default_simulation'] = analytics.simulate_savings(
            monthly_saving=simulation_amount,
            months=6
        )
        
        context['monthly_comparison_json'] = json.dumps(context['monthly_comparison'])
        
        weekday_data = context['weekday_analysis'].get('data', [])
        if weekday_data:
            context['weekday_json'] = json.dumps([
                {'day': item['weekday'], 'total': float(item['total'])}
                for item in weekday_data
            ])
        else:
            context['weekday_json'] = json.dumps([])
        
        context['net_worth_json'] = json.dumps(context['net_worth_evolution'])
        
        return context