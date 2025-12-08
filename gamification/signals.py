"""
Signals para Sistema de Gamificação do Nebue
Detecta ações do usuário e desbloqueia conquistas automaticamente
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .services import GamificationService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def criar_perfil_gamificacao(sender, instance, created, **kwargs):
    """
    Cria o perfil de gamificação quando o usuário se cadastra
    E desbloqueia a conquista de boas-vindas
    """
    if created:
        from .models import PerfilGamificacao, NivelFinanceiro
        
        try:
            # Cria o perfil com nível inicial
            nivel_inicial = NivelFinanceiro.objects.filter(numero=1).first()
            perfil, _ = PerfilGamificacao.objects.get_or_create(
                user=instance,
                defaults={'nivel_atual': nivel_inicial} if nivel_inicial else {}
            )
            
            # Desbloqueia conquista de boas-vindas
            GamificationService.verificar_e_desbloquear_conquista(
                instance, 
                'bem_vindo'
            )
            
            logger.info(f"✅ Perfil de gamificação criado para {instance.email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar perfil de gamificação: {e}")


@receiver(post_save, sender='transactions.Transaction')
def processar_transacao_gamificacao(sender, instance, created, **kwargs):
    """
    Processa gamificação quando uma transação é criada
    """
    if created:
        user = instance.conta.usuario if hasattr(instance, 'conta') else instance.usuario
        
        try:
            # Atualiza streak
            GamificationService.atualizar_streak(user)
            
            # Adiciona pontos pela transação
            GamificationService.adicionar_pontos(
                user,
                pontos=10,
                tipo='transacao',
                descricao=f'Transação registrada: {instance.descricao}'
            )
            
            # Verifica conquistas de quantidade de transações
            from transactions.models import Transaction
            total_transacoes = Transaction.objects.filter(
                conta__usuario=user
            ).count()
            
            # Mapeamento de conquistas por quantidade
            conquistas_map = {
                1: 'primeira_transacao',
                10: '10_transacoes',
                50: '50_transacoes',
                100: '100_transacoes'
            }
            
            if total_transacoes in conquistas_map:
                GamificationService.verificar_e_desbloquear_conquista(
                    user, 
                    conquistas_map[total_transacoes]
                )
            
            logger.info(f"✅ Gamificação processada para transação de {user.email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar gamificação de transação: {e}")


@receiver(post_save, sender='categories.Category')
def processar_categoria_gamificacao(sender, instance, created, **kwargs):
    """
    Processa gamificação quando uma categoria é criada
    """
    if created and hasattr(instance, 'usuario'):
        user = instance.usuario
        
        try:
            # Adiciona pontos pela categoria
            GamificationService.adicionar_pontos(
                user,
                pontos=5,
                tipo='categoria',
                descricao=f'Categoria criada: {instance.nome}'
            )
            
            # Verifica conquista de organizador expert (10 categorias)
            from categories.models import Category
            total_categorias = Category.objects.filter(usuario=user).count()
            
            if total_categorias == 10:
                GamificationService.verificar_e_desbloquear_conquista(
                    user, 
                    'organizador_expert'
                )
            
            logger.info(f"✅ Gamificação processada para categoria de {user.email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar gamificação de categoria: {e}")


@receiver(post_save, sender='cards.Card')
def processar_cartao_gamificacao(sender, instance, created, **kwargs):
    """
    Processa gamificação quando um cartão é criado
    """
    if created and hasattr(instance, 'usuario'):
        user = instance.usuario
        
        try:
            # Adiciona pontos pelo cartão
            GamificationService.adicionar_pontos(
                user,
                pontos=20,
                tipo='cartao',
                descricao=f'Cartão cadastrado: {instance.nome}'
            )
            
            # Verifica conquista de primeiro cartão
            from cards.models import Card
            total_cartoes = Card.objects.filter(usuario=user).count()
            
            if total_cartoes == 1:
                GamificationService.verificar_e_desbloquear_conquista(
                    user, 
                    'primeiro_cartao'
                )
            
            logger.info(f"✅ Gamificação processada para cartão de {user.email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar gamificação de cartão: {e}")


@receiver(post_save, sender='accounts.Budget')
def processar_orcamento_gamificacao(sender, instance, created, **kwargs):
    """
    Processa gamificação quando um orçamento é criado
    """
    if created and hasattr(instance, 'usuario'):
        user = instance.usuario
        
        try:
            # Adiciona pontos pelo orçamento
            GamificationService.adicionar_pontos(
                user,
                pontos=15,
                tipo='orcamento',
                descricao=f'Orçamento criado para {instance.mes}/{instance.ano}'
            )
            
            # Verifica conquista de primeiro orçamento
            from accounts.models import Budget
            total_orcamentos = Budget.objects.filter(usuario=user).count()
            
            if total_orcamentos == 1:
                GamificationService.verificar_e_desbloquear_conquista(
                    user, 
                    'primeiro_orcamento'
                )
            
            logger.info(f"✅ Gamificação processada para orçamento de {user.email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar gamificação de orçamento: {e}")