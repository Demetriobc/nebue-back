from decimal import Decimal
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender='transactions.Transaction')
def check_budget_on_transaction(sender, instance, created, **kwargs):
    """Check if transaction exceeded budget and create notification."""
    if not created:
        return
    
    # Only for expenses
    if instance.transaction_type != 'EXPENSE':
        return
    
    from .models import Notification
    
    # Try to import Budget - if doesn't exist, skip
    try:
        from budgets.models import Budget
    except ImportError:
        return
    
    now = timezone.now()
    try:
        budget = Budget.objects.get(
            user=instance.account.user,
            category=instance.category,
            month=now.month,
            year=now.year
        )
        
        # Calculate total spent
        from django.db.models import Sum
        from transactions.models import Transaction
        
        total_spent = Transaction.objects.filter(
            account__user=instance.account.user,
            category=instance.category,
            transaction_type='EXPENSE',
            transaction_date__month=now.month,
            transaction_date__year=now.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # If exceeded, create notification
        if total_spent > budget.amount:
            if not Notification.objects.filter(
                user=instance.account.user,
                notification_type=Notification.NotificationType.BUDGET,
                created_at__date=now.date(),
                title__icontains=instance.category.name
            ).exists():
                Notification.create_budget_alert(
                    user=instance.account.user,
                    category=instance.category,
                    amount=total_spent,
                    limit=budget.amount
                )
    except Budget.DoesNotExist:
        pass
    except Exception as e:
        print(f"Error in budget notification: {e}")


@receiver(post_save, sender='accounts.Account')
def check_low_balance(sender, instance, **kwargs):
    """Check if account balance is low and create notification."""
    from .models import Notification
    
    if instance.balance < 0:
        now = timezone.now()
        if not Notification.objects.filter(
            user=instance.user,
            notification_type=Notification.NotificationType.BALANCE,
            created_at__date=now.date(),
            title__icontains=instance.name
        ).exists():
            try:
                Notification.create_low_balance_alert(
                    user=instance.user,
                    account=instance
                )
            except Exception as e:
                print(f"Error creating balance notification: {e}")


@receiver(post_save, sender='accounts.CreditCard')
def check_card_limit(sender, instance, **kwargs):
    """Check if credit card is near limit and create notification."""
    from .models import Notification
    
    if not instance.credit_limit:
        return
    
    try:
        usage_percent = (instance.current_balance / instance.credit_limit) * 100
        
        if usage_percent >= 80:
            now = timezone.now()
            if not Notification.objects.filter(
                user=instance.account.user,
                notification_type=Notification.NotificationType.CARD,
                created_at__date=now.date(),
                title__icontains=instance.name
            ).exists():
                Notification.create_card_limit_alert(
                    user=instance.account.user,
                    card=instance,
                    usage_percent=usage_percent
                )
    except Exception as e:
        print(f"Error creating card notification: {e}")