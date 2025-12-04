from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .services import GamificacaoService


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_perfil_gamificacao(sender, instance, created, **kwargs):
    """Cria perfil de gamificação para novos usuários"""
    if created:
        GamificacaoService.inicializar_perfil(instance)


@receiver(post_save, sender='transactions.Transaction')
def gamificar_transacao(sender, instance, created, **kwargs):
    """Adiciona pontos quando uma transação é criada"""
    if created:
        try:
            GamificacaoService.registrar_transacao(instance.user, instance)
        except Exception as e:
            print(f"Erro na gamificação de transação: {e}")