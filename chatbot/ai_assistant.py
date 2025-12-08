import json
import os
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.conf import settings

from transactions.models import Transaction
from categories.models import Category
from accounts.models import Account


class FinancialAssistant:
    """
    Assistente financeiro inteligente com IA Groq (Llama 3.1)
    Focado em precisão, sem alucinações, baseado em dados reais.
    """
    
    def __init__(self, user):
        self.user = user
        self.today = timezone.now().date()
        self.api_key = self._get_api_key()
    
    def _get_api_key(self):
        """Busca API key de forma segura"""
        return getattr(settings, 'GROQ_API_KEY', None) or os.environ.get('GROQ_API_KEY')
    
    def get_system_prompt(self):
        """Prompt do sistema com regras RÍGIDAS contra alucinações"""
        return f"""Você é Nebue, assistente financeiro pessoal do usuário {self.user.email}.

🎯 SUA MISSÃO:
Ajudar o usuário a tomar decisões financeiras inteligentes com base em DADOS REAIS.

⚠️ REGRAS ABSOLUTAS (NUNCA VIOLE):
1. Use APENAS dados fornecidos no contexto financeiro
2. NUNCA invente números, valores ou estatísticas
3. Se não tiver dados, diga: "Não tenho essa informação ainda"
4. Seja BREVE: máximo 3-4 linhas por resposta
5. Use emojis para destacar: 💰 (dinheiro), 📊 (análise), 🎯 (meta), ⚠️ (alerta)
6. Responda SEMPRE em português brasileiro
7. Quando falar de valores, use o formato: R$ X.XXX,XX
8. Base suas dicas em "Pai Rico Pai Pobre" e "O Homem Mais Rico da Babilônia"

📅 DATA DE HOJE: {self.today.strftime('%d/%m/%Y')}

💡 EXEMPLOS DE RESPOSTAS CORRETAS:
- "Você gastou R$ 2.800 este mês, 15% a mais que o anterior."
- "Alimentação representa 45% dos seus gastos. Considere reduzir."
- "Seu saldo atual é R$ 3.200 distribuído em 2 contas."

❌ NUNCA FAÇA:
- Inventar valores ou porcentagens
- Dar conselhos genéricos sem dados
- Responder com mais de 5 linhas
- Usar palavras como "provavelmente", "talvez", "cerca de" (seja preciso!)
"""
    
    def get_context_data(self):
        """Coleta dados financeiros REAIS do usuário de forma robusta"""
        current_month_start = self.today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Transações do mês atual
        current_month_transactions = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__gte=current_month_start,
            transaction_date__lte=self.today
        )
        
        # Gastos mês atual
        month_expenses = current_month_transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Receitas mês atual
        month_income = current_month_transactions.filter(
            transaction_type=Transaction.TransactionType.INCOME
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Gastos mês anterior
        last_month_expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=last_month_start,
            transaction_date__lt=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Saldo total de contas ativas
        accounts = Account.objects.filter(user=self.user, is_active=True)
        total_balance = accounts.aggregate(total=Sum('balance'))['total'] or Decimal('0')
        
        # Top 5 categorias de gastos
        top_categories = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:5]
        
        # Calcular porcentagem de cada categoria
        total_expenses = month_expenses['total'] or Decimal('0')
        categories_with_percentage = []
        for cat in top_categories:
            percentage = (float(cat['total']) / float(total_expenses) * 100) if total_expenses > 0 else 0
            categories_with_percentage.append({
                'nome': cat['category__name'],
                'total': float(cat['total']),
                'quantidade_transacoes': cat['count'],
                'porcentagem': round(percentage, 1)
            })
        
        # Comparação com mês anterior
        variation = 0
        if last_month_expenses > 0:
            current = month_expenses['total'] or Decimal('0')
            variation = float((current - last_month_expenses) / last_month_expenses * 100)
        
        # Contas individuais
        accounts_list = [
            {
                'nome': acc.name,
                'tipo': acc.get_account_type_display(),
                'saldo': float(acc.balance)
            }
            for acc in accounts
        ]
        
        context = {
            'data_atual': self.today.strftime('%d/%m/%Y'),
            'mes_atual': {
                'gastos': float(month_expenses['total'] or 0),
                'quantidade_gastos': month_expenses['count'],
                'receitas': float(month_income['total'] or 0),
                'quantidade_receitas': month_income['count'],
                'balanco': float((month_income['total'] or 0) - (month_expenses['total'] or 0)),
            },
            'mes_anterior': {
                'gastos': float(last_month_expenses),
            },
            'comparacao': {
                'variacao_percentual': round(variation, 1),
                'aumentou': variation > 0
            },
            'contas': {
                'saldo_total': float(total_balance),
                'quantidade': accounts.count(),
                'detalhes': accounts_list
            },
            'categorias_top_5': categories_with_percentage,
        }
        
        return context
    
    def process_message(self, user_message, conversation_history):
        """Processa mensagem do usuário com validações robustas"""
        
        # Validação 1: Biblioteca instalada
        try:
            from groq import Groq
        except ImportError:
            return "❌ **Erro técnico**: Biblioteca Groq não instalada.\n\n💡 Solução: `pip install groq`"
        
        # Validação 2: API Key configurada
        if not self.api_key:
            return "❌ **Configuração ausente**: API Key do Groq não encontrada.\n\n💡 Adicione `GROQ_API_KEY` no arquivo `.env`"
        
        # Validação 3: Mensagem não vazia
        if not user_message or not user_message.strip():
            return "🤔 Você não disse nada! Como posso ajudar?"
        
        # Limitar tamanho da mensagem (segurança)
        if len(user_message) > 500:
            return "⚠️ Mensagem muito longa! Por favor, seja mais objetivo (máximo 500 caracteres)."
        
        # Obter contexto financeiro real
        context = self.get_context_data()
        
        # Formatar histórico (últimas 5 mensagens apenas)
        formatted_history = self._format_history(conversation_history)
        
        # System prompt com regras rígidas
        system_prompt = self.get_system_prompt()
        
        # User prompt com contexto estruturado
        user_prompt = f"""📊 DADOS FINANCEIROS REAIS (use APENAS estes dados):
```json
{json.dumps(context, indent=2, ensure_ascii=False)}
```

💬 HISTÓRICO RECENTE:
{formatted_history}

❓ PERGUNTA DO USUÁRIO:
{user_message}

⚠️ LEMBRE-SE: 
- Use APENAS os dados acima
- Seja BREVE (3-4 linhas no máximo)
- Não invente informações
- Se não tiver dados para responder, seja honesto"""

        try:
            client = Groq(api_key=self.api_key)
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model="llama-3.3-70b-versatile",  # Modelo ATUALIZADO (2024)
                temperature=0.3,  # Baixa temperatura = menos criatividade = mais precisão
                max_tokens=400,  # Limitar resposta
                top_p=0.9,  # Foco em respostas mais prováveis
                stream=False,
                stop=None,
            )
            
            assistant_response = chat_completion.choices[0].message.content.strip()
            
            # Validação da resposta
            if not assistant_response:
                return "🤔 Desculpe, não consegui processar sua pergunta. Tente reformular!"
            
            # Limitar tamanho da resposta (segurança extra)
            if len(assistant_response) > 1000:
                assistant_response = assistant_response[:1000] + "..."
            
            return assistant_response
            
        except Exception as e:
            error_message = str(e)
            
            # Tratamento de erros específicos
            if 'authentication' in error_message.lower() or 'api key' in error_message.lower():
                return "❌ **Erro de autenticação**: API Key inválida.\n\n💡 Verifique se a chave está correta no `.env`"
            elif 'rate limit' in error_message.lower():
                return "⏰ **Limite atingido**: Muitas requisições.\n\n💡 Aguarde alguns segundos e tente novamente."
            elif 'timeout' in error_message.lower():
                return "⏱️ **Timeout**: Servidor demorou para responder.\n\n💡 Tente novamente."
            else:
                return f"❌ **Erro inesperado**: {error_message[:100]}\n\n💡 Tente novamente ou contate o suporte."
    
    def _format_history(self, history):
        """Formata histórico de forma concisa"""
        if not history:
            return "Primeira interação com o usuário."
        
        # Pegar últimas 5 mensagens apenas
        recent_history = history[-5:]
        
        formatted = []
        for msg in recent_history:
            role = "👤 Usuário" if msg['role'] == 'user' else "🤖 Nebue"
            content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted) if formatted else "Primeira interação."
    
    def _get_expenses_summary(self):
        """Resumo de gastos do mês"""
        current_month_start = self.today.replace(day=1)
        
        expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        return {
            'total': float(expenses['total'] or 0),
            'quantidade': expenses['count'] or 0,
            'periodo': 'mês atual',
            'media_por_transacao': float(expenses['total'] / expenses['count']) if expenses['count'] > 0 else 0
        }
    
    def _get_balance_summary(self):
        """Resumo de saldos"""
        accounts = Account.objects.filter(
            user=self.user,
            is_active=True
        )
        
        accounts_list = [
            {
                'nome': acc.name,
                'tipo': acc.get_account_type_display(),
                'saldo': float(acc.balance)
            }
            for acc in accounts
        ]
        
        total = sum(acc['saldo'] for acc in accounts_list)
        
        return {
            'contas': accounts_list,
            'total': total,
            'quantidade_contas': len(accounts_list)
        }
    
    def _get_categories_summary(self):
        """Resumo de categorias"""
        current_month_start = self.today.replace(day=1)
        
        categories = Transaction.objects.filter(
            account__user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=current_month_start
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        total_expenses = sum(cat['total'] for cat in categories)
        
        categories_with_percentage = [
            {
                'nome': cat['category__name'],
                'total': float(cat['total']),
                'quantidade': cat['count'],
                'porcentagem': round(float(cat['total']) / total_expenses * 100, 1) if total_expenses > 0 else 0
            }
            for cat in categories
        ]
        
        return {
            'categorias': categories_with_percentage,
            'total_gasto': float(total_expenses)
        }