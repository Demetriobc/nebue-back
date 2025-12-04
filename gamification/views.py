# gamification/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import (
    PerfilGamificacao, Conquista, ConquistaUsuario,
    Desafio, DesafioUsuario, HistoricoGamificacao, NivelFinanceiro
)
from .services import GamificacaoService


@login_required
def dashboard_gamificacao(request):
    """Dashboard principal de gamificação"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    
    # Estatísticas
    stats = GamificacaoService.get_estatisticas(perfil)
    
    # Conquistas recentes
    conquistas_recentes = perfil.conquistas.select_related('conquista').order_by('-desbloqueada_em')[:5]
    
    # Conquistas não visualizadas
    conquistas_novas = GamificacaoService.get_conquistas_nao_visualizadas(perfil)
    
    # Desafios ativos
    desafios_ativos = perfil.desafios.filter(
        status='em_andamento'
    ).select_related('desafio')[:3]
    
    # Histórico recente
    historico = perfil.historico.all()[:10]
    
    # Próximo nível
    proximo_nivel = None
    if perfil.nivel_atual:
        proximo_nivel = NivelFinanceiro.objects.filter(
            numero=perfil.nivel_atual.numero + 1
        ).first()
    
    context = {
        'perfil': perfil,
        'stats': stats,
        'conquistas_recentes': conquistas_recentes,
        'conquistas_novas': conquistas_novas,
        'desafios_ativos': desafios_ativos,
        'historico': historico,
        'proximo_nivel': proximo_nivel,
    }
    
    return render(request, 'gamification/dashboard.html', context)


@login_required
def conquistas_list(request):
    """Lista todas as conquistas disponíveis e desbloqueadas"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    
    # Todas as conquistas
    todas_conquistas = Conquista.objects.filter(ativa=True).select_related('tipo')
    
    # Conquistas desbloqueadas
    conquistas_user_ids = perfil.conquistas.values_list('conquista_id', flat=True)
    
    # Organiza por tipo
    conquistas_por_tipo = {}
    for conquista in todas_conquistas:
        tipo_nome = conquista.tipo.nome
        if tipo_nome not in conquistas_por_tipo:
            conquistas_por_tipo[tipo_nome] = []
        
        conquistas_por_tipo[tipo_nome].append({
            'conquista': conquista,
            'desbloqueada': conquista.id in conquistas_user_ids
        })
    
    context = {
        'perfil': perfil,
        'conquistas_por_tipo': conquistas_por_tipo,
        'total_conquistas': todas_conquistas.count(),
        'total_desbloqueadas': len(conquistas_user_ids),
    }
    
    return render(request, 'gamification/conquistas.html', context)


@login_required
def desafios_list(request):
    """Lista desafios disponíveis e em andamento"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    
    # Atualiza progresso dos desafios
    GamificacaoService.atualizar_desafios(perfil)
    
    # Desafios públicos ativos
    desafios_disponiveis = Desafio.objects.filter(
        publico=True,
        status='ativo'
    ).exclude(
        participantes__perfil=perfil
    ).order_by('-data_inicio')
    
    # Desafios do usuário
    meus_desafios = DesafioUsuario.objects.filter(
        perfil=perfil
    ).select_related('desafio').order_by('-iniciado_em')
    
    context = {
        'perfil': perfil,
        'desafios_disponiveis': desafios_disponiveis,
        'meus_desafios': meus_desafios,
    }
    
    return render(request, 'gamification/desafios.html', context)


@login_required
@require_http_methods(["POST"])
def participar_desafio(request, desafio_id):
    """Inscreve o usuário em um desafio"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    desafio = get_object_or_404(Desafio, id=desafio_id, status='ativo')
    
    # Verifica se já está participando
    if DesafioUsuario.objects.filter(perfil=perfil, desafio=desafio).exists():
        messages.warning(request, 'Você já está participando deste desafio!')
        return redirect('gamification:desafios_list')
    
    # Inscreve no desafio
    DesafioUsuario.objects.create(
        perfil=perfil,
        desafio=desafio
    )
    
    messages.success(request, f'Você entrou no desafio: {desafio.titulo}! Boa sorte! 🚀')
    return redirect('gamification:desafios_list')


@login_required
def ranking_view(request):
    """Exibe o ranking de usuários"""
    periodo = request.GET.get('periodo', 'mensal')
    
    if periodo not in ['semanal', 'mensal', 'geral']:
        periodo = 'mensal'
    
    ranking = GamificacaoService.get_ranking(periodo=periodo, limite=50)
    
    # Posição do usuário atual
    perfil_user = GamificacaoService.inicializar_perfil(request.user)
    posicao_user = None
    
    for idx, perfil in enumerate(ranking, 1):
        if perfil.user == request.user:
            posicao_user = idx
            break
    
    context = {
        'ranking': ranking,
        'periodo': periodo,
        'posicao_user': posicao_user,
        'perfil_user': perfil_user,
    }
    
    return render(request, 'gamification/ranking.html', context)


@login_required
def historico_view(request):
    """Exibe o histórico completo de gamificação"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    
    # Histórico paginado
    historico = perfil.historico.all()
    
    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    if tipo_filtro:
        historico = historico.filter(tipo=tipo_filtro)
    
    context = {
        'perfil': perfil,
        'historico': historico[:50],  # Limita a 50 registros
        'tipo_filtro': tipo_filtro,
    }
    
    return render(request, 'gamification/historico.html', context)


@login_required
@require_http_methods(["POST"])
def marcar_conquistas_vistas(request):
    """Marca conquistas como visualizadas (AJAX)"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    GamificacaoService.marcar_conquistas_visualizadas(perfil)
    
    return JsonResponse({'success': True})


@login_required
def nivel_detalhes(request):
    """Detalhes do nível atual e próximos níveis"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    
    todos_niveis = NivelFinanceiro.objects.all().order_by('numero')
    
    context = {
        'perfil': perfil,
        'todos_niveis': todos_niveis,
    }
    
    return render(request, 'gamification/niveis.html', context)


# API para widgets
@login_required
def api_stats(request):
    """Retorna estatísticas em JSON para uso em widgets"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    stats = GamificacaoService.get_estatisticas(perfil)
    
    return JsonResponse(stats)


@login_required
def api_conquistas_novas(request):
    """Retorna conquistas não visualizadas"""
    perfil = GamificacaoService.inicializar_perfil(request.user)
    conquistas = GamificacaoService.get_conquistas_nao_visualizadas(perfil)
    
    data = [{
        'titulo': c.conquista.titulo,
        'descricao': c.conquista.descricao,
        'raridade': c.conquista.raridade,
        'pontos': c.conquista.pontos,
        'icone': c.conquista.icone,
        'cor': c.conquista.get_cor_raridade(),
        'desbloqueada_em': c.desbloqueada_em.strftime('%d/%m/%Y %H:%M')
    } for c in conquistas]
    
    return JsonResponse({'conquistas': data})