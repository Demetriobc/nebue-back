from django.contrib.auth import get_user_model
from django.db import models
from categories.models import Category

User = get_user_model()

class Budget(models.Model):
    '''
    Budget model for tracking spending limits by category.
    
    Allows users to set monthly spending limits for each category
    or a general budget for all expenses. Includes automatic
    calculation of usage percentage and alert triggers.
    
    Attributes:
        user: ForeignKey to User (CASCADE on delete)
        category: ForeignKey to Category (CASCADE on delete, nullable)
        amount_limit: Maximum amount to spend
        month: Budget month (1-12)
        year: Budget year
        is_general: If True, applies to all categories
        created_at: Timestamp when budget was created
        updated_at: Timestamp when budget was last modified
    '''
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name='Usuário'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name='Categoria',
        null=True,
        blank=True,
        help_text='Deixe em branco para orçamento geral'
    )
    amount_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Limite de Orçamento'
    )
    month = models.IntegerField(
        verbose_name='Mês',
        help_text='Mês do orçamento (1-12)'
    )
    year = models.IntegerField(
        verbose_name='Ano'
    )
    is_general = models.BooleanField(
        default=False,
        verbose_name='Orçamento Geral',
        help_text='Aplica a todas as categorias'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-year', '-month']
        unique_together = ['user', 'category', 'month', 'year']
        indexes = [
            models.Index(fields=['user', 'month', 'year']),
            models.Index(fields=['category', 'month', 'year']),
        ]
    
    def __str__(self):
        if self.is_general:
            return f'Orçamento Geral - {self.month}/{self.year}'
        return f'{self.category.name} - {self.month}/{self.year}'
    
    @property
    def spent_amount(self):
        '''Calculate total spent in this budget'''
        from transactions.models import Transaction
        from django.db.models import Sum
        
        if self.is_general:
            # Sum all expenses
            total = Transaction.objects.filter(
                account__user=self.user,
                transaction_type=Transaction.TransactionType.EXPENSE,
                transaction_date__month=self.month,
                transaction_date__year=self.year
            ).aggregate(total=Sum('amount'))['total'] or 0
        else:
            # Sum by category
            total = Transaction.objects.filter(
                account__user=self.user,
                category=self.category,
                transaction_type=Transaction.TransactionType.EXPENSE,
                transaction_date__month=self.month,
                transaction_date__year=self.year
            ).aggregate(total=Sum('amount'))['total'] or 0
        
        return total
    
    @property
    def percentage_used(self):
        '''Calculate percentage of budget used'''
        if self.amount_limit == 0:
            return 0
        return min((self.spent_amount / self.amount_limit) * 100, 100)
    
    @property
    def remaining_amount(self):
        '''Calculate remaining budget'''
        return max(self.amount_limit - self.spent_amount, 0)
    
    @property
    def is_exceeded(self):
        '''Check if budget is exceeded'''
        return self.spent_amount > self.amount_limit
    
    @property
    def alert_level(self):
        '''Return alert level based on usage'''
        percentage = self.percentage_used
        if percentage >= 100:
            return 'danger'  # Ultrapassou
        elif percentage >= 80:
            return 'warning'  # Perto do limite
        elif percentage >= 50:
            return 'info'  # Metade
        return 'success'  # OK

class Account(models.Model):
    '''
    Bank account or wallet model for tracking user finances.

    Each account belongs to a specific user and maintains a balance that is
    automatically updated through transaction signals. Accounts support three
    types: checking, savings, and wallet. Deleting an account cascades to all
    associated transactions.

    Attributes:
        user: ForeignKey to CustomUser (CASCADE on delete)
        name: Custom name for the account (e.g., 'Conta Principal')
        bank_name: Name of the financial institution
        account_type: Type of account (CHECKING, SAVINGS, or WALLET)
        balance: Current account balance (auto-updated via signals)
        is_active: Whether the account is currently active
        created_at: Timestamp when account was created (auto-generated)
        updated_at: Timestamp when account was last modified (auto-updated)

    Relationships:
        - Many-to-one with CustomUser via user field
        - One-to-many with Transaction via transactions reverse relation
        - Related name: user.accounts

    Balance Calculation:
        Balance is automatically recalculated when transactions are
        created, updated, or deleted through signals in transactions/signals.py

    Security:
        All queries MUST filter by user=request.user to ensure data isolation

    Example:
        account = Account.objects.create(
            user=request.user,
            name='Conta Corrente',
            bank_name='Banco do Brasil',
            account_type=Account.CHECKING,
            balance=1000.00
        )
    '''

    # Account type choices
    CHECKING = 'checking'
    SAVINGS = 'savings'
    WALLET = 'wallet'

    ACCOUNT_TYPE_CHOICES = [
        (CHECKING, 'Conta Corrente'),
        (SAVINGS, 'Conta Poupança'),
        (WALLET, 'Carteira'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name='Usuário'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nome da Conta'
    )
    bank_name = models.CharField(
        max_length=100,
        verbose_name='Nome do Banco'
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default=CHECKING,
        verbose_name='Tipo de Conta'
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Saldo'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Conta'
        verbose_name_plural = 'Contas'
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'account_type']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        '''
        Return string representation of the account.

        Returns:
            str: The account name
        '''
        return f'{self.name} - {self.bank_name}'

class CreditCard(models.Model):
    '''
    Credit card model linked to a bank account.
    
    Each credit card belongs to a specific account and tracks spending
    through transactions. Features include limit management, closing date,
    and automatic invoice calculation.
    
    Attributes:
        account: ForeignKey to Account (CASCADE on delete)
        name: Custom name for the card (e.g., 'Nubank Gold')
        card_number: Last 4 digits of the card (for identification)
        card_brand: Card brand (VISA, MASTERCARD, etc.)
        credit_limit: Maximum credit available
        closing_day: Day of month when invoice closes (1-28)
        due_day: Day of month when payment is due (1-28)
        is_active: Whether the card is currently active
        created_at: Timestamp when card was created
        updated_at: Timestamp when card was last modified
    
    Relationships:
        - Many-to-one with Account via account field
        - One-to-many with Transaction via credit_card reverse relation
        
    Example:
        card = CreditCard.objects.create(
            account=account,
            name='Nubank',
            card_number='1234',
            card_brand=CreditCard.VISA,
            credit_limit=5000.00,
            closing_day=5,
            due_day=15
        )
    '''
    
    # Card brand choices
    VISA = 'visa'
    MASTERCARD = 'mastercard'
    ELO = 'elo'
    AMEX = 'amex'
    HIPERCARD = 'hipercard'
    OTHER = 'other'
    
    CARD_BRAND_CHOICES = [
        (VISA, 'Visa'),
        (MASTERCARD, 'Mastercard'),
        (ELO, 'Elo'),
        (AMEX, 'American Express'),
        (HIPERCARD, 'Hipercard'),
        (OTHER, 'Outro'),
    ]
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='credit_cards',
        verbose_name='Conta Vinculada'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nome do Cartão'
    )
    card_number = models.CharField(
        max_length=4,
        verbose_name='Últimos 4 dígitos',
        help_text='Apenas os 4 últimos dígitos do cartão'
    )
    card_brand = models.CharField(
        max_length=20,
        choices=CARD_BRAND_CHOICES,
        default=VISA,
        verbose_name='Bandeira'
    )
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Limite de Crédito'
    )
    closing_day = models.IntegerField(
        verbose_name='Dia de Fechamento',
        help_text='Dia do mês (1-28)'
    )
    due_day = models.IntegerField(
        verbose_name='Dia de Vencimento',
        help_text='Dia do mês (1-28)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        verbose_name = 'Cartão de Crédito'
        verbose_name_plural = 'Cartões de Crédito'
        ordering = ['name']
        indexes = [
            models.Index(fields=['account', 'is_active']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f'{self.name} (****{self.card_number})'
    
    @property
    def available_limit(self):
        '''Calculate available credit limit'''
        from transactions.models import Transaction
        from django.db.models import Sum
        from datetime import datetime
        
        # Get current month expenses
        current_expenses = Transaction.objects.filter(
            credit_card=self,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__month=datetime.now().month,
            transaction_date__year=datetime.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return self.credit_limit - current_expenses
    
    @property
    def current_invoice(self):
        '''Get current invoice total'''
        from transactions.models import Transaction
        from django.db.models import Sum
        from datetime import datetime
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        invoice_total = Transaction.objects.filter(
            credit_card=self,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__month=current_month,
            transaction_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return invoice_total
    
# ========================================
# GAMIFICAÇÃO - SIGNALS
# ========================================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Budget)
def processar_gamificacao_budget(sender, instance, created, **kwargs):
    """
    Adiciona pontos quando cria um orçamento
    """
    if not created:
        return
    
    try:
        from gamification.services import GamificationService
        
        # 50 pontos por criar orçamento
        GamificationService.adicionar_pontos(
            user=instance.user,
            pontos=50,
            tipo='orcamento',
            descricao=f'📊 Orçamento criado: {instance.category.name if instance.category else "Geral"}'
        )
        
        # Verifica conquistas
        total_budgets = Budget.objects.filter(user=instance.user).count()
        
        if total_budgets == 1:
            GamificationService.verificar_e_desbloquear_conquista(instance.user, 'primeiro_orcamento')
        
    except Exception as e:
        print(f"Erro gamificação budget: {e}")


@receiver(post_save, sender=CreditCard)
def processar_gamificacao_cartao(sender, instance, created, **kwargs):
    """
    Adiciona pontos quando cadastra cartão de crédito
    """
    if not created:
        return
    
    try:
        from gamification.services import GamificationService
        
        # 30 pontos por cadastrar cartão
        GamificationService.adicionar_pontos(
            user=instance.account.user,
            pontos=30,
            tipo='cartao',
            descricao=f'💳 Cartão cadastrado: {instance.name}'
        )
        
        # Conquista de primeiro cartão
        total_cards = CreditCard.objects.filter(account__user=instance.account.user).count()
        
        if total_cards == 1:
            GamificationService.verificar_e_desbloquear_conquista(instance.account.user, 'primeiro_cartao')
        
    except Exception as e:
        print(f"Erro gamificação cartão: {e}")