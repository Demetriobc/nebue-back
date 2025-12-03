from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Conversation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name='Usuário'
    )
    title = models.CharField(
        max_length=200,
        default='Nova Conversa',
        verbose_name='Título'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativa'
    )

    class Meta:
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.title}'


class Message(models.Model):
    class MessageType(models.TextChoices):
        USER = 'USER', 'Usuário'
        ASSISTANT = 'ASSISTANT', 'Assistente'
        SYSTEM = 'SYSTEM', 'Sistema'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversa'
    )
    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.USER,
        verbose_name='Tipo'
    )
    content = models.TextField(
        verbose_name='Conteúdo'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadados'
    )

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f'{self.get_message_type_display()}: {self.content[:50]}'
