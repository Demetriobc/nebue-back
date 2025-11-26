from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from datetime import datetime
from .models import Budget, CreditCard, Account
from categories.models import Category


# ==================== BUDGET VIEWS ====================

@login_required
def budget_list(request):
    """Lista todos os orçamentos do usuário"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Filtrar por mês/ano se fornecido
    selected_month = int(request.GET.get('month', current_month))
    selected_year = int(request.GET.get('year', current_year))
    
    budgets = Budget.objects.filter(
        user=request.user,
        month=selected_month,
        year=selected_year
    ).select_related('category')
    
    # Calcular totais
    total_limit = budgets.aggregate(total=Sum('amount_limit'))['total'] or 0
    total_spent = sum(budget.spent_amount for budget in budgets)
    total_remaining = total_limit - total_spent
    
    context = {
        'budgets': budgets,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'total_limit': total_limit,
        'total_spent': total_spent,
        'total_remaining': total_remaining,
        'months': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
            (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
            (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
            (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'years': range(datetime.now().year - 2, datetime.now().year + 3),
    }
    
    return render(request, 'accounts/budget_list.html', context)


@login_required
def budget_create(request):
    """Criar novo orçamento"""
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount_limit = request.POST.get('amount_limit')
        month = request.POST.get('month')
        year = request.POST.get('year')
        is_general = request.POST.get('is_general') == 'on'
        
        # Validações
        if not amount_limit or float(amount_limit) <= 0:
            messages.error(request, 'O valor do orçamento deve ser maior que zero.')
            return redirect('accounts:budget_create')
        
        if not is_general and not category_id:
            messages.error(request, 'Selecione uma categoria ou marque como orçamento geral.')
            return redirect('accounts:budget_create')
        
        # Verificar se já existe orçamento para esta categoria/mês/ano
        existing = Budget.objects.filter(
            user=request.user,
            category_id=category_id if not is_general else None,
            month=month,
            year=year,
            is_general=is_general
        ).exists()
        
        if existing:
            messages.error(request, 'Já existe um orçamento para esta categoria neste período.')
            return redirect('accounts:budget_create')
        
        # Criar orçamento
        Budget.objects.create(
            user=request.user,
            category_id=category_id if not is_general else None,
            amount_limit=amount_limit,
            month=month,
            year=year,
            is_general=is_general
        )
        
        messages.success(request, 'Orçamento criado com sucesso!')
        return redirect('accounts:budget_list')
    
    # GET request
    categories = Category.objects.filter(
        user=request.user
    )
    
    context = {
        'categories': categories,
        'current_month': datetime.now().month,
        'current_year': datetime.now().year,
        'months': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
            (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
            (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
            (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'years': range(datetime.now().year - 1, datetime.now().year + 3),
    }
    
    return render(request, 'accounts/budget_form.html', context)


@login_required
def budget_edit(request, pk):
    """Editar orçamento existente"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount_limit = request.POST.get('amount_limit')
        month = request.POST.get('month')
        year = request.POST.get('year')
        is_general = request.POST.get('is_general') == 'on'
        
        # Validações
        if not amount_limit or float(amount_limit) <= 0:
            messages.error(request, 'O valor do orçamento deve ser maior que zero.')
            return redirect('accounts:budget_edit', pk=pk)
        
        if not is_general and not category_id:
            messages.error(request, 'Selecione uma categoria ou marque como orçamento geral.')
            return redirect('accounts:budget_edit', pk=pk)
        
        # Atualizar orçamento
        budget.category_id = category_id if not is_general else None
        budget.amount_limit = amount_limit
        budget.month = month
        budget.year = year
        budget.is_general = is_general
        budget.save()
        
        messages.success(request, 'Orçamento atualizado com sucesso!')
        return redirect('accounts:budget_list')
    
    # GET request
    categories = Category.objects.filter(
        user=request.user
    )
    
    context = {
        'budget': budget,
        'categories': categories,
        'months': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
            (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
            (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
            (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'years': range(datetime.now().year - 1, datetime.now().year + 3),
    }
    
    return render(request, 'accounts/budget_form.html', context)


@login_required
def budget_delete(request, pk):
    """Deletar orçamento"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Orçamento excluído com sucesso!')
        return redirect('accounts:budget_list')
    
    return render(request, 'accounts/budget_confirm_delete.html', {'budget': budget})


# ==================== CREDIT CARD VIEWS ====================

@login_required
def creditcard_list(request):
    """Lista todos os cartões de crédito do usuário"""
    # Pegar todas as contas do usuário
    user_accounts = Account.objects.filter(user=request.user)
    
    # Pegar cartões vinculados às contas do usuário
    credit_cards = CreditCard.objects.filter(
        account__in=user_accounts
    ).select_related('account')
    
    # Calcular totais
    total_limit = credit_cards.aggregate(total=Sum('credit_limit'))['total'] or 0
    total_available = sum(card.available_limit for card in credit_cards)
    total_invoice = sum(card.current_invoice for card in credit_cards)
    
    context = {
        'credit_cards': credit_cards,
        'total_limit': total_limit,
        'total_available': total_available,
        'total_invoice': total_invoice,
    }
    
    return render(request, 'accounts/creditcard_list.html', context)


@login_required
def creditcard_create(request):
    """Criar novo cartão de crédito"""
    if request.method == 'POST':
        account_id = request.POST.get('account')
        name = request.POST.get('name')
        card_number = request.POST.get('card_number')
        card_brand = request.POST.get('card_brand')
        credit_limit = request.POST.get('credit_limit')
        closing_day = request.POST.get('closing_day')
        due_day = request.POST.get('due_day')
        
        # Validações
        if not all([account_id, name, card_number, card_brand, credit_limit, closing_day, due_day]):
            messages.error(request, 'Todos os campos são obrigatórios.')
            return redirect('accounts:creditcard_create')
        
        if len(card_number) != 4 or not card_number.isdigit():
            messages.error(request, 'Informe apenas os 4 últimos dígitos do cartão.')
            return redirect('accounts:creditcard_create')
        
        closing_day = int(closing_day)
        due_day = int(due_day)
        
        if not (1 <= closing_day <= 28) or not (1 <= due_day <= 28):
            messages.error(request, 'Os dias devem estar entre 1 e 28.')
            return redirect('accounts:creditcard_create')
        
        # Verificar se a conta pertence ao usuário
        account = get_object_or_404(Account, pk=account_id, user=request.user)
        
        # Criar cartão
        CreditCard.objects.create(
            account=account,
            name=name,
            card_number=card_number,
            card_brand=card_brand,
            credit_limit=credit_limit,
            closing_day=closing_day,
            due_day=due_day
        )
        
        messages.success(request, 'Cartão de crédito criado com sucesso!')
        return redirect('accounts:creditcard_list')
    
    # GET request
    accounts = Account.objects.filter(user=request.user, is_active=True)
    
    context = {
        'accounts': accounts,
        'card_brands': CreditCard.CARD_BRAND_CHOICES,
    }
    
    return render(request, 'accounts/creditcard_form.html', context)


@login_required
def creditcard_edit(request, pk):
    """Editar cartão de crédito existente"""
    credit_card = get_object_or_404(
        CreditCard, 
        pk=pk, 
        account__user=request.user
    )
    
    if request.method == 'POST':
        account_id = request.POST.get('account')
        name = request.POST.get('name')
        card_number = request.POST.get('card_number')
        card_brand = request.POST.get('card_brand')
        credit_limit = request.POST.get('credit_limit')
        closing_day = request.POST.get('closing_day')
        due_day = request.POST.get('due_day')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validações
        if len(card_number) != 4 or not card_number.isdigit():
            messages.error(request, 'Informe apenas os 4 últimos dígitos do cartão.')
            return redirect('accounts:creditcard_edit', pk=pk)
        
        closing_day = int(closing_day)
        due_day = int(due_day)
        
        if not (1 <= closing_day <= 28) or not (1 <= due_day <= 28):
            messages.error(request, 'Os dias devem estar entre 1 e 28.')
            return redirect('accounts:creditcard_edit', pk=pk)
        
        # Verificar se a conta pertence ao usuário
        account = get_object_or_404(Account, pk=account_id, user=request.user)
        
        # Atualizar cartão
        credit_card.account = account
        credit_card.name = name
        credit_card.card_number = card_number
        credit_card.card_brand = card_brand
        credit_card.credit_limit = credit_limit
        credit_card.closing_day = closing_day
        credit_card.due_day = due_day
        credit_card.is_active = is_active
        credit_card.save()
        
        messages.success(request, 'Cartão de crédito atualizado com sucesso!')
        return redirect('accounts:creditcard_list')
    
    # GET request
    accounts = Account.objects.filter(user=request.user, is_active=True)
    
    context = {
        'credit_card': credit_card,
        'accounts': accounts,
        'card_brands': CreditCard.CARD_BRAND_CHOICES,
    }
    
    return render(request, 'accounts/creditcard_form.html', context)


@login_required
def creditcard_delete(request, pk):
    """Deletar cartão de crédito"""
    credit_card = get_object_or_404(
        CreditCard, 
        pk=pk, 
        account__user=request.user
    )
    
    if request.method == 'POST':
        credit_card.delete()
        messages.success(request, 'Cartão de crédito excluído com sucesso!')
        return redirect('accounts:creditcard_list')
    
    return render(request, 'accounts/creditcard_confirm_delete.html', {
        'credit_card': credit_card
    })


@login_required
def creditcard_detail(request, pk):
    """Detalhes do cartão com fatura atual"""
    from transactions.models import Transaction
    
    credit_card = get_object_or_404(
        CreditCard, 
        pk=pk, 
        account__user=request.user
    )
    
    # Pegar transações do mês atual
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    transactions = Transaction.objects.filter(
        credit_card=credit_card,
        transaction_date__month=current_month,
        transaction_date__year=current_year
    ).order_by('-transaction_date')
    
    context = {
        'credit_card': credit_card,
        'transactions': transactions,
        'current_month': current_month,
        'current_year': current_year,
    }
    
    return render(request, 'accounts/creditcard_detail.html', context)
