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
from .services import GamificationService


@login_required
def dashboard_gamificacao(request):
    """Dashboard principal de gamificação"""
    # Atualiza streak do dia
    GamificationService.atualizar_streak(request.user)
    
    # Busca ou cria perfil
    perfil, created = PerfilGamificacao.objects.get_or_create(user=request.user)
    
    # Estatísticas completas
    stats = GamificationService.get_estatisticas_usuario(request.user)
    
    # Próximo nível
    proximo_nivel = NivelFinanceiro.objects.filter(
        pontos_necessarios__gt=perfil.pontos_totais
    ).order_by('pontos_necessarios').first()
    
    # Conquistas recentes (últimas 5)
    conquistas_recentes = ConquistaUsuario.objects.filter(
        perfil=perfil
    ).select_related('conquista').order_by('-desbloqueada_em')[:5]
    
    # Histórico recente (últimas 10 ações)
    historico = HistoricoGamificacao.objects.filter(
        perfil=perfil
    ).order_by('-criado_em')[:10]
    
    # Desafios ativos (se você tiver implementado)
    desafios_ativos = []
    try:
        desafios_ativos = DesafioUsuario.objects.filter(
            perfil=perfil,
            status='em_andamento'
        ).select_related('desafio')[:3]
    except:
        pass
    
    context = {
        'perfil': perfil,
        'stats': stats,
        'proximo_nivel': proximo_nivel,
        'conquistas_recentes': conquistas_recentes,
        'historico': historico,
        'desafios_ativos': desafios_ativos,
    }
    
    return render(request, 'gamification/dashboard.html', context)


@login_required
def conquistas_list(request):
    """Lista todas as conquistas disponíveis e desbloqueadas"""
    perfil, created = PerfilGamificacao.objects.get_or_create(user=request.user)
    
    # Todas as conquistas
    todas_conquistas = Conquista.objects.all().select_related('tipo')
    
    # IDs das conquistas desbloqueadas
    conquistas_desbloqueadas_ids = list(
        ConquistaUsuario.objects.filter(perfil=perfil).values_list('conquista_id', flat=True)
    )
    
    # Contadores
    total = todas_conquistas.count()
    desbloqueadas_count = len(conquistas_desbloqueadas_ids)
    progresso = int((desbloqueadas_count / total * 100)) if total > 0 else 0
    
    context = {
        'todas_conquistas': todas_conquistas,
        'conquistas_desbloqueadas_ids': conquistas_desbloqueadas_ids,
        'todas_conquistas_count': total,
        'conquistas_desbloqueadas_count': desbloqueadas_count,
        'progresso_percentual': progresso,
    }
    
    return render(request, 'gamification/conquistas_list.html', context)


@login_required
def ranking_view(request):
    """Exibe o ranking de usuários"""
    periodo = request.GET.get('periodo', 'geral')
    
    if periodo not in ['semanal', 'mensal', 'geral']:
        periodo = 'geral'
    
    # Busca ranking usando o service
    ranking = GamificationService.get_ranking(periodo=periodo, limit=100)
    
    # Busca posição do usuário
    posicao_user = GamificationService.get_posicao_usuario(request.user, periodo=periodo)
    
    context = {
        'ranking': ranking,
        'periodo': periodo,
        'posicao_user': posicao_user,
    }
    
    return render(request, 'gamification/ranking.html', context)


@login_required
def niveis_view(request):
    """Exibe todos os níveis e o progresso do usuário"""
    perfil, created = PerfilGamificacao.objects.get_or_create(user=request.user)
    
    # Todos os níveis ordenados
    todos_niveis = NivelFinanceiro.objects.all().order_by('numero')
    
    context = {
        'perfil': perfil,
        'todos_niveis': todos_niveis,
    }
    
    return render(request, 'gamification/niveis.html', context)


@login_required
def nivel_detalhes(request):
    """Detalhes do nível atual e próximos níveis (alias para niveis_view)"""
    return niveis_view(request)


@login_required
def historico_view(request):
    """Exibe o histórico completo de pontos"""
    perfil, created = PerfilGamificacao.objects.get_or_create(user=request.user)
    
    # Histórico completo
    historico = HistoricoGamificacao.objects.filter(
        perfil=perfil
    ).order_by('-criado_em')
    
    # Filtro por tipo (opcional)
    tipo_filtro = request.GET.get('tipo', '')
    if tipo_filtro:
        historico = historico.filter(tipo=tipo_filtro)
    
    context = {
        'perfil': perfil,
        'historico': historico[:100],  # Limita a 100
        'tipo_filtro': tipo_filtro,
    }
    
    return render(request, 'gamification/historico.html', context)


@login_required
def desafios_list(request):
    """Lista desafios disponíveis e em andamento"""
    perfil, created = PerfilGamificacao.objects.get_or_create(user=request.user)
    
    try:
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
    except:
        # Se não tiver modelo de Desafio ainda
        context = {
            'perfil': perfil,
            'desafios_disponiveis': [],
            'meus_desafios': [],
        }
    
    return render(request, 'gamification/desafios.html', context)


@login_required
@require_http_methods(["POST"])
def participar_desafio(request, desafio_id):
    """Inscreve o usuário em um desafio"""
    try:
        perfil, created = PerfilGamificacao.objects.get_or_create(user=request.user)
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
        
        messages.success(request, f'Você entrou no desafio: {desafio.titulo}! 🚀')
    except:
        messages.error(request, 'Erro ao participar do desafio.')
    
    return redirect('gamification:desafios_list')


# ========================================
# APIs JSON (para widgets e AJAX)
# ========================================

@login_required
def api_stats(request):
    """Retorna estatísticas em JSON"""
    stats = GamificationService.get_estatisticas_usuario(request.user)
    return JsonResponse(stats, safe=False)


@login_required
def api_conquistas_novas(request):
    """Retorna conquistas não visualizadas"""
    perfil, created = PerfilGamificacao.objects.get_or_create(user=request.user)
    
    conquistas = ConquistaUsuario.objects.filter(
        perfil=perfil,
        visualizada=False
    ).select_related('conquista')
    
    data = [{
        'titulo': c.conquista.titulo,
        'descricao': c.conquista.descricao,
        'raridade': c.conquista.raridade,
        'pontos': c.conquista.pontos,
        'icone': c.conquista.icone,
        'desbloqueada_em': c.desbloqueada_em.strftime('%d/%m/%Y %H:%M')
    } for c in conquistas]
    
    return JsonResponse({'conquistas': data})


@login_required
@require_http_methods(["POST"])
def marcar_conquistas_vistas(request):
    """Marca conquistas como visualizadas"""
    perfil, created = PerfilGamificacao.objects.get_or_create(user=request.user)
    
    ConquistaUsuario.objects.filter(
        perfil=perfil,
        visualizada=False
    ).update(visualizada=True)
    
    return JsonResponse({'success': True})