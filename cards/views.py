from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Cartao, Fatura, TransacaoCartao
from accounts.models import Account 
from datetime import date, datetime


@login_required
def cartoes_list(request):
    cartoes = Cartao.objects.filter(usuario=request.user).order_by('-criado_em')
    
    # Calcular totais
    total_limite = sum(cartao.limite_total for cartao in cartoes)
    total_usado = sum(cartao.limite_usado for cartao in cartoes)
    total_disponivel = sum(cartao.limite_disponivel for cartao in cartoes)
    
    # Pegar mês e ano atual
    mes_atual = date.today().month
    ano_atual = date.today().year
    
    # Calcular total das faturas do mês (soma de todas as transações do mês)
    total_faturas = TransacaoCartao.objects.filter(
        cartao__usuario=request.user,
        cartao__in=cartoes,
        data__month=mes_atual,
        data__year=ano_atual
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    # Calcular percentual usado
    percentual_usado = (total_usado / total_limite * 100) if total_limite > 0 else 0
    
    # Adicionar valor da fatura atual para cada cartão
    for cartao in cartoes:
        # Calcula o valor das transações do mês para este cartão
        fatura_mes = TransacaoCartao.objects.filter(
            cartao=cartao,
            data__month=mes_atual,
            data__year=ano_atual
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        # Adiciona como atributo temporário (não sobrescreve a property)
        cartao.valor_fatura_mes = fatura_mes
    
    context = {
        'cartoes': cartoes,
        'total_limite': total_limite,
        'total_usado': total_usado,
        'total_disponivel': total_disponivel,
        'total_faturas': total_faturas,
        'percentual_usado': percentual_usado,
    }
    
    return render(request, 'cartoes/cartoes_list.html', context)


@login_required
def cartao_create(request):
    """Cria um novo cartão"""
    contas = Account.objects.filter(user=request.user).order_by('name')
    
    if request.method == 'POST':
        try:
            # Pega os dados do formulário
            nome = request.POST.get('nome')
            banco = request.POST.get('banco')
            bandeira = request.POST.get('bandeira')
            ultimos_digitos = request.POST.get('ultimos_digitos')
            limite_total = Decimal(request.POST.get('limite_total', 0))
            dia_fechamento = int(request.POST.get('dia_fechamento'))
            dia_vencimento = int(request.POST.get('dia_vencimento'))
            conta_id = request.POST.get('conta')
            
            # Validações básicas
            if not all([nome, banco, ultimos_digitos, limite_total > 0]):
                messages.error(request, 'Preencha todos os campos obrigatórios!')
                return redirect('cartao_create')
            
            # Cria o cartão
            cartao = Cartao.objects.create(
                usuario=request.user,
                nome=nome,
                banco=banco,
                bandeira=bandeira,
                ultimos_digitos=ultimos_digitos,
                limite_total=limite_total,
                limite_disponivel=limite_total,
                dia_fechamento=dia_fechamento,
                dia_vencimento=dia_vencimento,
                conta_id=conta_id if conta_id else None
            )
            
            # Cria a fatura do mês atual
            criar_fatura_mes_atual(cartao)
            
            messages.success(request, f'Cartão {nome} cadastrado com sucesso!')
            return redirect('cards:cartoes_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar cartão: {str(e)}')
    
    context = {
        'contas': contas,
        'bancos': Cartao.BANCOS,
        'bandeiras': Cartao.BANDEIRAS,
    }
    
    return render(request, 'cartoes/cartao_form.html', context)


@login_required
def cartao_detail(request, cartao_id):
    """Mostra detalhes de um cartão específico"""
    cartao = get_object_or_404(Cartao, id=cartao_id, usuario=request.user)
    
    # Busca faturas do cartão (últimos 6 meses)
    faturas = cartao.faturas.all()[:6]
    
    # Fatura atual
    fatura_atual = cartao.fatura_atual
    transacoes_recentes = []
    if fatura_atual:
        transacoes_recentes = fatura_atual.transacoes.all()[:10]
    
    # Estatísticas
    stats = {
        'total_transacoes': cartao.transacoes.count(),
        'valor_fatura_atual': fatura_atual.valor_total if fatura_atual else 0,
        'proxima_fatura': calcular_proxima_data_fechamento(cartao),
        'proximo_vencimento': calcular_proxima_data_vencimento(cartao),
    }
    
    context = {
        'cartao': cartao,
        'faturas': faturas,
        'fatura_atual': fatura_atual,
        'transacoes_recentes': transacoes_recentes,
        'stats': stats,
    }
    
    return render(request, 'cartoes/cartao_detail.html', context)


@login_required
def cartao_edit(request, cartao_id):
    """Edita um cartão existente"""
    cartao = get_object_or_404(Cartao, id=cartao_id, usuario=request.user)
    contas = Account.objects.filter(user=request.user).order_by('name')
    
    if request.method == 'POST':
        try:
            cartao.nome = request.POST.get('nome')
            cartao.banco = request.POST.get('banco')
            cartao.bandeira = request.POST.get('bandeira')
            cartao.ultimos_digitos = request.POST.get('ultimos_digitos')
            
            novo_limite = Decimal(request.POST.get('limite_total', 0))
            diferenca = novo_limite - cartao.limite_total
            cartao.limite_total = novo_limite
            cartao.limite_disponivel += diferenca
            
            cartao.dia_fechamento = int(request.POST.get('dia_fechamento'))
            cartao.dia_vencimento = int(request.POST.get('dia_vencimento'))
            
            conta_id = request.POST.get('conta')
            cartao.conta_id = conta_id if conta_id else None
            
            cartao.save()
            
            messages.success(request, 'Cartão atualizado com sucesso!')
            return redirect('cards:cartao_detail', cartao_id=cartao.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar cartão: {str(e)}')
    
    context = {
        'cartao': cartao,
        'contas': contas,
        'bancos': Cartao.BANCOS,
        'bandeiras': Cartao.BANDEIRAS,
        'editing': True,
    }
    
    return render(request, 'cartoes/cartao_form.html', context)


@login_required
def cartao_delete(request, cartao_id):
    """Desativa um cartão"""
    cartao = get_object_or_404(Cartao, id=cartao_id, usuario=request.user)
    
    if request.method == 'POST':
        cartao.ativo = False
        cartao.save()
        messages.success(request, f'Cartão {cartao.nome} removido com sucesso!')
        return redirect('cards:cartoes_list') 
    
    context = {'cartao': cartao}
    return render(request, 'cartoes/cartao_confirm_delete.html', context)


@login_required
def transacao_create(request, cartao_id):
    """Adiciona uma nova transação no cartão"""
    cartao = get_object_or_404(Cartao, id=cartao_id, usuario=request.user)
    
    if request.method == 'POST':
        try:
            descricao = request.POST.get('descricao')
            categoria = request.POST.get('categoria')
            valor = Decimal(request.POST.get('valor', 0))
            data_str = request.POST.get('data')
            parcelas = int(request.POST.get('parcelas', 1))
            
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
            
            # Verifica se tem limite disponível
            valor_total = valor * parcelas if parcelas > 1 else valor
            if cartao.limite_disponivel < valor:
                messages.error(request, 'Limite insuficiente!')
                return redirect('cards:cartao_detail', cartao_id=cartao.id)
            
            # Determina a fatura
            fatura = obter_ou_criar_fatura(cartao, data)
            
            # Cria a transação
            if parcelas > 1:
                # Cria transações parceladas
                criar_transacoes_parceladas(cartao, descricao, categoria, valor, data, parcelas)
            else:
                # Transação única
                TransacaoCartao.objects.create(
                    cartao=cartao,
                    fatura=fatura,
                    descricao=descricao,
                    categoria=categoria,
                    valor=valor,
                    data=data
                )
            
            # Atualiza limite disponível
            cartao.limite_disponivel -= valor
            cartao.save()
            
            # Atualiza total da fatura
            fatura.atualizar_total()
            
            messages.success(request, 'Transação adicionada com sucesso!')
            return redirect('cards:cartao_detail', cartao_id=cartao.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao adicionar transação: {str(e)}')
    
    context = {
        'cartao': cartao,
        'categorias': TransacaoCartao.CATEGORIAS,
    }
    
    return render(request, 'cartoes/transacao_form.html', context)


@login_required
def fatura_detail(request, fatura_id):
    fatura = get_object_or_404(Fatura, id=fatura_id, cartao__usuario=request.user)
    transacoes = fatura.transacoes.all()
    
    # Agrupa transações por categoria e calcula totais
    por_categoria = {}
    for transacao in transacoes:
        categoria = transacao.get_categoria_display()
        if categoria not in por_categoria:
            por_categoria[categoria] = {
                'transacoes': [],
                'total': 0
            }
        por_categoria[categoria]['transacoes'].append(transacao)
        por_categoria[categoria]['total'] += transacao.valor
    
    context = {
        'fatura': fatura,
        'transacoes': transacoes,
        'por_categoria': por_categoria,
    }
    
    return render(request, 'cartoes/fatura_detail.html', context)


@login_required
def fatura_pagar(request, fatura_id):
    """Registra pagamento de uma fatura"""
    fatura = get_object_or_404(Fatura, id=fatura_id, cartao__usuario=request.user)
    
    if request.method == 'POST':
        try:
            valor_pago = Decimal(request.POST.get('valor_pago', 0))
            data_pagamento_str = request.POST.get('data_pagamento')
            
            if valor_pago <= 0:
                messages.error(request, 'Informe um valor válido!')
                return redirect('fatura_detail', fatura_id=fatura.id)
            
            # Registra o pagamento
            fatura.valor_pago += valor_pago
            fatura.data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
            
            # Atualiza status
            if fatura.esta_paga:
                fatura.status = 'paga'
                # Devolve limite ao cartão
                fatura.cartao.limite_disponivel += fatura.valor_total
                fatura.cartao.save()
            
            fatura.save()
            
            messages.success(request, 'Pagamento registrado com sucesso!')
            return redirect('fatura_detail', fatura_id=fatura.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao registrar pagamento: {str(e)}')
    
    context = {'fatura': fatura}
    return render(request, 'cartoes/fatura_pagar.html', context)


# Funções auxiliares

def criar_fatura_mes_atual(cartao):
    """Cria a fatura do mês atual para um cartão"""
    hoje = datetime.now()
    mes = hoje.month
    ano = hoje.year
    
    # Verifica se já existe
    fatura = Fatura.objects.filter(cartao=cartao, mes=mes, ano=ano).first()
    if fatura:
        return fatura
    
    # Calcula datas
    data_fechamento = calcular_proxima_data_fechamento(cartao)
    data_vencimento = calcular_proxima_data_vencimento(cartao)
    
    # Cria a fatura
    fatura = Fatura.objects.create(
        cartao=cartao,
        mes=mes,
        ano=ano,
        data_fechamento=data_fechamento,
        data_vencimento=data_vencimento,
        status='aberta'
    )
    
    return fatura


def obter_ou_criar_fatura(cartao, data_transacao):
    """Obtém ou cria a fatura apropriada para uma transação"""
    # Determina o mês/ano da fatura baseado na data de fechamento
    if data_transacao.day > cartao.dia_fechamento:
        # Vai para a próxima fatura
        if data_transacao.month == 12:
            mes = 1
            ano = data_transacao.year + 1
        else:
            mes = data_transacao.month + 1
            ano = data_transacao.year
    else:
        mes = data_transacao.month
        ano = data_transacao.year
    
    # Busca ou cria a fatura
    fatura, created = Fatura.objects.get_or_create(
        cartao=cartao,
        mes=mes,
        ano=ano,
        defaults={
            'data_fechamento': calcular_data_fechamento(cartao, mes, ano),
            'data_vencimento': calcular_data_vencimento(cartao, mes, ano),
            'status': 'aberta'
        }
    )
    
    return fatura


def criar_transacoes_parceladas(cartao, descricao, categoria, valor, data_inicial, parcelas):
    """Cria transações parceladas distribuídas nos meses seguintes"""
    valor_parcela = valor / parcelas  # ← ADICIONA ESSA LINHA!
    
    for i in range(parcelas):
        # Calcula a data da parcela
        mes = data_inicial.month + i
        ano = data_inicial.year
        
        while mes > 12:
            mes -= 12
            ano += 1
        
        data_parcela = data_inicial.replace(month=mes, year=ano)
        
        # Obtém a fatura do mês
        fatura = obter_ou_criar_fatura(cartao, data_parcela)
        
        # Cria a transação
        TransacaoCartao.objects.create(
            cartao=cartao,
            fatura=fatura,
            descricao=descricao,
            categoria=categoria,
            valor=valor_parcela,  # ← CORRETO! Usa o valor dividido
            data=data_parcela,
            parcelas=parcelas,
            parcela_atual=i + 1
        )
        
        # Atualiza o total da fatura
        fatura.atualizar_total()


def calcular_proxima_data_fechamento(cartao):
    """Calcula a próxima data de fechamento"""
    hoje = datetime.now().date()
    mes = hoje.month
    ano = hoje.year
    
    # Se já passou o dia de fechamento deste mês, vai para o próximo
    if hoje.day > cartao.dia_fechamento:
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    
    return datetime(ano, mes, cartao.dia_fechamento).date()


def calcular_proxima_data_vencimento(cartao):
    """Calcula a próxima data de vencimento"""
    data_fechamento = calcular_proxima_data_fechamento(cartao)
    mes = data_fechamento.month
    ano = data_fechamento.year
    
    # Vencimento é no mês seguinte ao fechamento
    mes += 1
    if mes > 12:
        mes = 1
        ano += 1
    
    return datetime(ano, mes, cartao.dia_vencimento).date()


def calcular_data_fechamento(cartao, mes, ano):
    """Calcula data de fechamento para um mês/ano específico"""
    return datetime(ano, mes, cartao.dia_fechamento).date()


def calcular_data_vencimento(cartao, mes, ano):
    """Calcula data de vencimento para um mês/ano específico"""
    mes += 1
    if mes > 12:
        mes = 1
        ano += 1
    return datetime(ano, mes, cartao.dia_vencimento).date()


@login_required
def transacao_edit(request, transacao_id):
    """Edita uma transação existente"""
    transacao = get_object_or_404(TransacaoCartao, id=transacao_id, cartao__usuario=request.user)
    cartao = transacao.cartao
    fatura = transacao.fatura
    
    if request.method == 'POST':
        # Pega os dados do form
        descricao = request.POST.get('descricao')
        categoria = request.POST.get('categoria')
        novo_valor = Decimal(request.POST.get('valor'))
        data = request.POST.get('data')
        
        # Calcula a diferença de valor
        valor_antigo = transacao.valor
        diferenca = novo_valor - valor_antigo
        
        # Atualiza a transação
        transacao.descricao = descricao
        transacao.categoria = categoria
        transacao.valor = novo_valor
        transacao.data = data
        transacao.save()
        
        # Atualiza o total da fatura
        fatura.atualizar_total()
        
        # Atualiza o limite disponível do cartão
        cartao.limite_disponivel -= diferenca
        cartao.save()
        
        messages.success(request, 'Transação atualizada com sucesso!')
        return redirect('cards:fatura_detail', fatura_id=fatura.id)
    
    # GET - mostra o form
    context = {
        'transacao': transacao,
        'cartao': cartao,
        'categorias': TransacaoCartao.CATEGORIAS,
    }
    return render(request, 'cartoes/transacao_edit.html', context)


@login_required
def transacao_delete(request, transacao_id):
    """Deleta uma transação"""
    transacao = get_object_or_404(TransacaoCartao, id=transacao_id, cartao__usuario=request.user)
    cartao = transacao.cartao
    fatura = transacao.fatura
    fatura_id = fatura.id
    
    if request.method == 'POST':
        # Devolve o limite pro cartão
        cartao.limite_disponivel += transacao.valor
        cartao.save()
        
        # Deleta a transação
        transacao.delete()
        
        # Recalcula o total da fatura
        fatura.atualizar_total()
        
        messages.success(request, 'Transação excluída com sucesso!')
        return redirect('cards:fatura_detail', fatura_id=fatura_id)
    
    # GET - mostra confirmação
    context = {
        'transacao': transacao,
        'fatura': fatura,
    }
    return render(request, 'cartoes/transacao_confirm_delete.html', context)