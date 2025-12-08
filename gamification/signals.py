"""
Signals para Sistema de Gamificação do Nebue
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
    """
    if created:
        from .models import PerfilGamificacao, NivelFinanceiro
        
        try:
            nivel_inicial = NivelFinanceiro.objects.filter(numero=1).first()
            perfil, _ = PerfilGamificacao.objects.get_or_create(
                user=instance,
                defaults={'nivel_atual': nivel_inicial} if nivel_inicial else {}
            )
            
            GamificationService.verificar_e_desbloquear_conquista(
                instance, 
                'bem_vindo'
            )
            
            logger.info(f"✅ Perfil criado para {instance.email}")
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")