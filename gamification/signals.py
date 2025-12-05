"""
Services para Sistema de Gamificação do Nebue
Contém toda a lógica de negócio centralizada
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class GamificationService:
    """
    Serviço centralizado para gerenciar toda a gamificação
    """
    
    @staticmethod
    def adicionar_pontos(user, pontos, tipo='geral', descricao='Pontos adicionados'):
        """
        Adiciona pontos ao usuário e registra no histórico
        
        Args:
            user: Usuário que receberá os pontos
            pontos: Quantidade de pontos a adicionar
            tipo: Tipo de ação (transacao, meta, investimento, etc)
            descricao: Descrição da ação
        
        Returns:
            PerfilGamificacao atualizado
        """
        from .models import PerfilGamificacao, HistoricoPontos, Nivel
        
        try:
            with transaction.atomic():
                # Busca ou cria perfil
                perfil, created = PerfilGamificacao.objects.get_or_create(user=user)
                
                # Adiciona pontos
                perfil.pontos_totais += pontos
                
                # Registra no histórico
                HistoricoPontos.objects.create(
                    perfil=perfil,
                    pontos=pontos,
                    tipo=tipo,
                    descricao=descricao
                )
                
                # Verifica se subiu de nível
                nivel_anterior = perfil.nivel_atual
                novo_nivel = GamificationService._calcular_nivel(perfil.pontos_totais)
                
                if novo_nivel and novo_nivel != nivel_anterior:
                    perfil.nivel_atual = novo_nivel
                    
                    # Registra o level up
                    HistoricoPontos.objects.create(
                        perfil=perfil,
                        pontos=50,  # Bônus por subir de nível
                        tipo='nivel_up',
                        descricao=f'🎊 Level UP! Você alcançou o nível {novo_nivel.numero}: {novo_nivel.nome}'
                    )
                    perfil.pontos_totais += 50
                
                perfil.save()
                
                logger.info(f"{user.username} ganhou {pontos} pontos - Total: {perfil.pontos_totais}")
                
                return perfil
                
        except Exception as e:
            logger.error(f"Erro ao adicionar pontos: {e}")
            raise
    
    @staticmethod
    def _calcular_nivel(pontos_totais):
        """
        Calcula qual nível o usuário deve estar baseado nos pontos
        """
        from .models import Nivel
        
        try:
            # Busca o nível mais alto que o usuário atingiu
            nivel = Nivel.objects.filter(
                pontos_necessarios__lte=pontos_totais
            ).order_by('-pontos_necessarios').first()
            
            return nivel
            
        except Exception as e:
            logger.error(f"Erro ao calcular nível: {e}")
            return None
    
    @staticmethod
    def atualizar_streak(user):
        """
        Atualiza a sequência (streak) do usuário
        Deve ser chamado quando o usuário faz uma ação no dia
        """
        from .models import PerfilGamificacao, HistoricoPontos
        
        try:
            perfil = PerfilGamificacao.objects.get(user=user)
            hoje = timezone.now().date()
            
            # Verifica se já atualizou hoje
            if perfil.ultima_acao_data == hoje:
                return perfil
            
            # Verifica se a última ação foi ontem (mantém streak)
            ontem = hoje - timedelta(days=1)
            
            if perfil.ultima_acao_data == ontem:
                # Mantém e aumenta streak
                perfil.streak_atual += 1
                
                # Atualiza maior streak se necessário
                if perfil.streak_atual > perfil.maior_streak:
                    perfil.maior_streak = perfil.streak_atual
                
                # Bônus por streak
                bonus_streak = perfil.streak_atual * 5  # 5 pontos por dia de streak
                
                HistoricoPontos.objects.create(
                    perfil=perfil,
                    pontos=bonus_streak,
                    tipo='streak',
                    descricao=f'🔥 Sequência de {perfil.streak_atual} dias! Bônus streak'
                )
                perfil.pontos_totais += bonus_streak
                
            elif perfil.ultima_acao_data is None or perfil.ultima_acao_data < ontem:
                # Perdeu o streak, reinicia
                if perfil.streak_atual > 0:
                    logger.info(f"{user.username} perdeu o streak de {perfil.streak_atual} dias")
                perfil.streak_atual = 1
            
            perfil.ultima_acao_data = hoje
            perfil.save()
            
            return perfil
            
        except Exception as e:
            logger.error(f"Erro ao atualizar streak: {e}")
            return None
    
    @staticmethod
    def verificar_e_desbloquear_conquista(user, codigo_conquista):
        """
        Verifica e desbloqueia uma conquista específica
        
        Args:
            user: Usuário
            codigo_conquista: Código único da conquista
        
        Returns:
            True se desbloqueou, False se já tinha ou não existe
        """
        from .models import PerfilGamificacao, Conquista, ConquistaUsuario, HistoricoPontos
        
        try:
            perfil = PerfilGamificacao.objects.get(user=user)
            conquista = Conquista.objects.get(codigo=codigo_conquista)
            
            # Verifica se já possui
            if ConquistaUsuario.objects.filter(perfil=perfil, conquista=conquista).exists():
                return False
            
            # Desbloqueia
            ConquistaUsuario.objects.create(
                perfil=perfil,
                conquista=conquista
            )
            
            # Adiciona pontos da conquista
            HistoricoPontos.objects.create(
                perfil=perfil,
                pontos=conquista.pontos,
                tipo='conquista',
                descricao=f'🏆 Conquista desbloqueada: {conquista.titulo}'
            )
            
            perfil.pontos_totais += conquista.pontos
            perfil.save()
            
            logger.info(f"{user.username} desbloqueou conquista: {conquista.titulo}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao desbloquear conquista: {e}")
            return False
    
    @staticmethod
    def get_ranking(periodo='geral', limit=None):
        """
        Retorna o ranking de usuários
        
        Args:
            periodo: 'semanal', 'mensal' ou 'geral'
            limit: Quantidade máxima de resultados (None = todos)
        
        Returns:
            QuerySet ordenado por pontos
        """
        from .models import PerfilGamificacao, HistoricoPontos
        from django.db.models import Sum, Q
        
        try:
            if periodo == 'semanal':
                data_inicio = timezone.now() - timedelta(days=7)
                
                # Busca perfis com pontos na última semana
                perfis_com_pontos = HistoricoPontos.objects.filter(
                    criado_em__gte=data_inicio
                ).values_list('perfil_id', flat=True).distinct()
                
                # Calcula pontos da semana para cada perfil
                perfis = PerfilGamificacao.objects.filter(
                    id__in=perfis_com_pontos
                ).select_related('user', 'nivel_atual')
                
                # Anota com soma dos pontos da semana
                from django.db.models import Subquery, OuterRef
                
                pontos_semana = HistoricoPontos.objects.filter(
                    perfil=OuterRef('pk'),
                    criado_em__gte=data_inicio
                ).values('perfil').annotate(
                    total=Sum('pontos')
                ).values('total')
                
                perfis = perfis.annotate(
                    pontos_periodo=Subquery(pontos_semana)
                ).order_by('-pontos_periodo')
                
            elif periodo == 'mensal':
                data_inicio = timezone.now() - timedelta(days=30)
                
                perfis_com_pontos = HistoricoPontos.objects.filter(
                    criado_em__gte=data_inicio
                ).values_list('perfil_id', flat=True).distinct()
                
                perfis = PerfilGamificacao.objects.filter(
                    id__in=perfis_com_pontos
                ).select_related('user', 'nivel_atual')
                
                pontos_mes = HistoricoPontos.objects.filter(
                    perfil=OuterRef('pk'),
                    criado_em__gte=data_inicio
                ).values('perfil').annotate(
                    total=Sum('pontos')
                ).values('total')
                
                perfis = perfis.annotate(
                    pontos_periodo=Subquery(pontos_mes)
                ).order_by('-pontos_periodo')
                
            else:  # geral
                perfis = PerfilGamificacao.objects.all().select_related(
                    'user', 'nivel_atual'
                ).order_by('-pontos_totais')
            
            if limit:
                perfis = perfis[:limit]
            
            return perfis
            
        except Exception as e:
            logger.error(f"Erro ao buscar ranking: {e}")
            return PerfilGamificacao.objects.none()
    
    @staticmethod
    def get_posicao_usuario(user, periodo='geral'):
        """
        Retorna a posição do usuário no ranking
        
        Args:
            user: Usuário
            periodo: 'semanal', 'mensal' ou 'geral'
        
        Returns:
            Posição do usuário (int) ou None
        """
        try:
            ranking = GamificationService.get_ranking(periodo=periodo)
            
            for index, perfil in enumerate(ranking, start=1):
                if perfil.user == user:
                    return index
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar posição do usuário: {e}")
            return None
    
    @staticmethod
    def get_estatisticas_usuario(user):
        """
        Retorna estatísticas completas do usuário
        """
        from .models import PerfilGamificacao, ConquistaUsuario, Desafio
        
        try:
            perfil = PerfilGamificacao.objects.get(user=user)
            
            # Conta conquistas
            total_conquistas = ConquistaUsuario.objects.filter(perfil=perfil).count()
            conquistas_nao_vistas = ConquistaUsuario.objects.filter(
                perfil=perfil,
                visualizada=False
            ).count()
            
            # Busca próximo nível
            from .models import Nivel
            proximo_nivel = Nivel.objects.filter(
                pontos_necessarios__gt=perfil.pontos_totais
            ).order_by('pontos_necessarios').first()
            
            # Calcula progresso
            if proximo_nivel:
                nivel_atual_pontos = perfil.nivel_atual.pontos_necessarios if perfil.nivel_atual else 0
                pontos_para_proximo = proximo_nivel.pontos_necessarios - nivel_atual_pontos
                pontos_progresso = perfil.pontos_totais - nivel_atual_pontos
                progresso_percentual = int((pontos_progresso / pontos_para_proximo) * 100) if pontos_para_proximo > 0 else 0
            else:
                progresso_percentual = 100
            
            return {
                'pontos_totais': perfil.pontos_totais,
                'nivel': {
                    'atual': perfil.nivel_atual,
                    'proximo': proximo_nivel,
                    'progresso': progresso_percentual
                },
                'streak': {
                    'atual': perfil.streak_atual,
                    'maior': perfil.maior_streak
                },
                'conquistas': {
                    'total': total_conquistas,
                    'nao_visualizadas': conquistas_nao_vistas
                },
                'desafios': {
                    'completados': 0,  # Implementar quando tiver desafios
                    'em_andamento': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {}