from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    System notifications for users.
    
    Notifications are automatically created by signals when certain events occur:
    - Budget exceeded
    - Goal achieved
    - Credit card near limit
    - Low balance
    - Monthly summary
    
    Attributes:
        user: User who will receive the notification
        notification_type: Type of notification (BUDGET, GOAL, CARD, etc)
        title: Short notification title
        message: Detailed notification message
        icon: Optional custom emoji/icon (uses type default if empty)
        link: Optional URL to redirect when clicked
        is_read: Whether user has read the notification
        created_at: When notification was created
    """
    
    class NotificationType(models.TextChoices):
        BUDGET = 'BUDGET', '💰 Orçamento'
        GOAL = 'GOAL', '🎯 Meta'
        CARD = 'CARD', '💳 Cartão'
        BALANCE = 'BALANCE', '💵 Saldo'
        SUMMARY = 'SUMMARY', '📊 Resumo'
        IMPORT = 'IMPORT', '📥 Importação'
        GENERAL = 'GENERAL', 'ℹ️ Geral'
        INFO = 'INFO', '💡 Informação'  # ← ADICIONADO
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Usuário'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        verbose_name='Tipo'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    message = models.TextField(
        verbose_name='Mensagem'
    )
    icon = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Ícone',
        help_text='Emoji personalizado (usa padrão do tipo se vazio)'
    )
    link = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Link',
        help_text='URL para redirecionar ao clicar na notificação'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Lida'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criada em'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Lida em'
    )
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f'{self.get_notification_type_display()} - {self.title}'
    
    @classmethod
    def create_budget_alert(cls, user, category, amount, limit):
        """Create notification when budget is exceeded."""
        return cls.objects.create(
            user=user,
            notification_type=cls.NotificationType.BUDGET,
            title=f'Orçamento de {category.name} ultrapassado!',
            message=f'Você gastou R$ {amount:.2f} de R$ {limit:.2f} em {category.name}.',
            link='/accounts/orcamentos/'
        )
    
    @classmethod
    def create_goal_achieved(cls, user, goal):
        """Create notification when goal is achieved."""
        return cls.objects.create(
            user=user,
            notification_type=cls.NotificationType.GOAL,
            title=f'Meta "{goal.name}" atingida! 🎉',
            message=f'Parabéns! Você alcançou sua meta de R$ {goal.target_amount:.2f}.',
            link='/accounts/orcamentos/'
        )
    
    @classmethod
    def create_card_limit_alert(cls, user, card, usage_percent):
        """Create notification when credit card is near limit."""
        return cls.objects.create(
            user=user,
            notification_type=cls.NotificationType.CARD,
            title=f'Cartão {card.name} próximo do limite',
            message=f'Você já usou {usage_percent:.0f}% do limite do seu cartão.',
            link='/cartoes/'
        )
    
    @classmethod
    def create_low_balance_alert(cls, user, account):
        """Create notification when account balance is low."""
        return cls.objects.create(
            user=user,
            notification_type=cls.NotificationType.BALANCE,
            title=f'Saldo baixo em {account.name}',
            message=f'O saldo da sua conta está em R$ {account.balance:.2f}.',
            link='/dashboard/'
        )
    
    @classmethod
    def create_monthly_summary(cls, user, income, expenses, balance):
        """Create monthly summary notification."""
        return cls.objects.create(
            user=user,
            notification_type=cls.NotificationType.SUMMARY,
            title='Resumo mensal disponível',
            message=f'Receitas: R$ {income:.2f} | Despesas: R$ {expenses:.2f} | Balanço: R$ {balance:.2f}',
            link='/dashboard/'
        )
    
    @classmethod
    def create_import_success(cls, user, count):
        """Create notification after successful OFX import."""
        return cls.objects.create(
            user=user,
            notification_type=cls.NotificationType.IMPORT,
            title=f'Importação concluída!',
            message=f'{count} transação(ões) importada(s) com sucesso.',
            link='/transactions/transaction/'
        )
    
    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
    
    def get_icon(self):
        """Get icon for notification type. Uses custom icon if set, otherwise default."""
        # Se tem ícone customizado, retorna ele
        if self.icon:
            return self.icon
        
        # Senão usa o padrão do tipo
        icons = {
            self.NotificationType.BUDGET: '💰',
            self.NotificationType.GOAL: '🎯',
            self.NotificationType.CARD: '💳',
            self.NotificationType.BALANCE: '💵',
            self.NotificationType.SUMMARY: '📊',
            self.NotificationType.IMPORT: '📥',
            self.NotificationType.INFO: '💡',
            self.NotificationType.GENERAL: 'ℹ️',
        }
        return icons.get(self.notification_type, 'ℹ️')
    
    def get_color_class(self):
        """Get Tailwind color class for notification type."""
        colors = {
            self.NotificationType.BUDGET: 'text-red-400 bg-red-500',
            self.NotificationType.GOAL: 'text-emerald-400 bg-emerald-500',
            self.NotificationType.CARD: 'text-yellow-400 bg-yellow-500',
            self.NotificationType.BALANCE: 'text-orange-400 bg-orange-500',
            self.NotificationType.SUMMARY: 'text-blue-400 bg-blue-500',
            self.NotificationType.IMPORT: 'text-purple-400 bg-purple-500',
            self.NotificationType.INFO: 'text-blue-400 bg-blue-500',
            self.NotificationType.GENERAL: 'text-slate-400 bg-slate-500',
        }
        return colors.get(self.notification_type, 'text-slate-400 bg-slate-500')