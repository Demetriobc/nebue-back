"""
Services para Sistema de Gamificação do Nebue
Centraliza toda a lógica de negócio da gamificação
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class GamificationService:
    """Serviço centralizado para gamificação"""
    
    @staticmethod
    def adicionar_pontos(user, pontos, tipo='geral', descricao='Pontos adicionados'):
        """
        Adiciona pontos ao usuário e registra no histórico
        """
        from gamification.models import PerfilGamificacao, HistoricoGamificacao, NivelFinanceiro
        
        try:
            with transaction.atomic():
                perfil, created = PerfilGamificacao.objects.get_or_create(user=user)
                perfil.pontos_totais += pontos
                
                HistoricoGamificacao.objects.create(
                    perfil=perfil,
                    pontos=pontos,
                    tipo=tipo,
                    descricao=descricao
                )
                
                nivel_anterior = perfil.nivel_atual
                novo_nivel = GamificationService._calcular_nivel(perfil.pontos_totais)
                
                if novo_nivel and novo_nivel != nivel_anterior:
                    perfil.nivel_atual = novo_nivel
                    
                    HistoricoGamificacao.objects.create(
                        perfil=perfil,
                        pontos=50,
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
        """Calcula qual nível o usuário deve estar"""
        from gamification.models import NivelFinanceiro
        
        try:
            nivel = NivelFinanceiro.objects.filter(
                pontos_necessarios__lte=pontos_totais
            ).order_by('-pontos_necessarios').first()
            return nivel
        except Exception as e:
            logger.error(f"Erro ao calcular nível: {e}")
            return None
    
    @staticmethod
    def atualizar_streak(user):
        """Atualiza a sequência (streak) do usuário"""
        from gamification.models import PerfilGamificacao, HistoricoGamificacao
        
        try:
            perfil, created = PerfilGamificacao.objects.get_or_create(user=user)
            hoje = timezone.now().date()
            
            # Verifica se já atualizou hoje
            if perfil.ultima_atividade == hoje:
                return perfil
            
            ontem = hoje - timedelta(days=1)
            
            if perfil.ultima_atividade == ontem:
                # Mantém e aumenta streak
                perfil.streak_atual += 1
                
                if perfil.streak_atual > perfil.maior_streak:
                    perfil.maior_streak = perfil.streak_atual
                
                # Bônus por streak
                bonus_streak = perfil.streak_atual * 5
                
                HistoricoGamificacao.objects.create(
                    perfil=perfil,
                    pontos=bonus_streak,
                    tipo='streak',
                    descricao=f'🔥 Sequência de {perfil.streak_atual} dias! Bônus streak'
                )
                perfil.pontos_totais += bonus_streak
                
            elif perfil.ultima_atividade is None or perfil.ultima_atividade < ontem:
                # Perdeu o streak, reinicia
                if perfil.streak_atual > 0:
                    logger.info(f"{user.username} perdeu o streak de {perfil.streak_atual} dias")
                perfil.streak_atual = 1
            
            perfil.ultima_atividade = hoje
            perfil.save()
            
            # Verifica conquistas de streak
            GamificationService._verificar_conquistas_streak(user, perfil.streak_atual)
            
            return perfil
            
        except Exception as e:
            logger.error(f"Erro ao atualizar streak: {e}")
            return None
    
    @staticmethod
    def _verificar_conquistas_streak(user, streak_atual):
        """Verifica conquistas relacionadas a streak"""
        conquistas_streak = {
            7: 'streak_7',
            30: 'streak_30',
            100: 'streak_100'
        }
        
        if streak_atual in conquistas_streak:
            GamificationService.verificar_e_desbloquear_conquista(
                user, conquistas_streak[streak_atual]
            )
    
    @staticmethod
    def verificar_e_desbloquear_conquista(user, codigo_conquista):
        """Verifica e desbloqueia uma conquista específica"""
        from gamification.models import PerfilGamificacao, Conquista, ConquistaUsuario, HistoricoGamificacao
        
        try:
            perfil, created = PerfilGamificacao.objects.get_or_create(user=user)
            
            try:
                conquista = Conquista.objects.get(codigo=codigo_conquista)
            except Conquista.DoesNotExist:
                logger.warning(f"Conquista {codigo_conquista} não existe")
                return False
            
            # Verifica se já possui
            if ConquistaUsuario.objects.filter(perfil=perfil, conquista=conquista).exists():
                return False
            
            # Desbloqueia
            ConquistaUsuario.objects.create(perfil=perfil, conquista=conquista)
            
            # Adiciona pontos da conquista
            HistoricoGamificacao.objects.create(
                perfil=perfil,
                pontos=conquista.pontos,
                tipo='conquista',
                descricao=f'🏆 Conquista desbloqueada: {conquista.titulo}'
            )
            
            perfil.pontos_totais += conquista.pontos
            perfil.conquistas_desbloqueadas += 1
            perfil.save()
            
            logger.info(f"{user.username} desbloqueou conquista: {conquista.titulo}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao desbloquear conquista: {e}")
            return False
    
    @staticmethod
    def get_ranking(periodo='geral', limit=None):
        """Retorna o ranking de usuários"""
        from gamification.models import PerfilGamificacao, HistoricoGamificacao
        from django.db.models import Sum, Subquery, OuterRef
        
        try:
            if periodo == 'semanal':
                data_inicio = timezone.now() - timedelta(days=7)
                
                perfis_com_pontos = HistoricoGamificacao.objects.filter(
                    criado_em__gte=data_inicio
                ).values_list('perfil_id', flat=True).distinct()
                
                perfis = PerfilGamificacao.objects.filter(
                    id__in=perfis_com_pontos
                ).select_related('user', 'nivel_atual')
                
                pontos_semana = HistoricoGamificacao.objects.filter(
                    perfil=OuterRef('pk'),
                    criado_em__gte=data_inicio
                ).values('perfil').annotate(total=Sum('pontos')).values('total')
                
                perfis = perfis.annotate(pontos_periodo=Subquery(pontos_semana)).order_by('-pontos_periodo')
                
            elif periodo == 'mensal':
                data_inicio = timezone.now() - timedelta(days=30)
                
                perfis_com_pontos = HistoricoGamificacao.objects.filter(
                    criado_em__gte=data_inicio
                ).values_list('perfil_id', flat=True).distinct()
                
                perfis = PerfilGamificacao.objects.filter(
                    id__in=perfis_com_pontos
                ).select_related('user', 'nivel_atual')
                
                pontos_mes = HistoricoGamificacao.objects.filter(
                    perfil=OuterRef('pk'),
                    criado_em__gte=data_inicio
                ).values('perfil').annotate(total=Sum('pontos')).values('total')
                
                perfis = perfis.annotate(pontos_periodo=Subquery(pontos_mes)).order_by('-pontos_periodo')
                
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
        """Retorna a posição do usuário no ranking"""
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
        """Retorna estatísticas completas do usuário"""
        from gamification.models import PerfilGamificacao, ConquistaUsuario, NivelFinanceiro
        
        try:
            perfil, created = PerfilGamificacao.objects.get_or_create(user=user)
            
            total_conquistas = ConquistaUsuario.objects.filter(perfil=perfil).count()
            conquistas_nao_vistas = ConquistaUsuario.objects.filter(
                perfil=perfil, visualizada=False
            ).count()
            
            proximo_nivel = NivelFinanceiro.objects.filter(
                pontos_necessarios__gt=perfil.pontos_totais
            ).order_by('pontos_necessarios').first()
            
            if proximo_nivel and perfil.nivel_atual:
                nivel_atual_pontos = perfil.nivel_atual.pontos_necessarios
                pontos_para_proximo = proximo_nivel.pontos_necessarios - nivel_atual_pontos
                pontos_progresso = perfil.pontos_totais - nivel_atual_pontos
                progresso_percentual = int((pontos_progresso / pontos_para_proximo) * 100) if pontos_para_proximo > 0 else 0
            else:
                progresso_percentual = 100 if not proximo_nivel else 0
            
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
                    'completados': perfil.desafios_completados,
                    'em_andamento': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {
                'pontos_totais': 0,
                'nivel': {'atual': None, 'proximo': None, 'progresso': 0},
                'streak': {'atual': 0, 'maior': 0},
                'conquistas': {'total': 0, 'nao_visualizadas': 0},
                'desafios': {'completados': 0, 'em_andamento': 0}
            }