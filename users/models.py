from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    '''
    Custom manager for CustomUser model that uses email as the unique identifier.

    Extends Django's default UserManager to support email-based authentication
    instead of username-based authentication.
    '''

    def create_user(self, email, password=None, **extra_fields):
        '''
        Create and save a regular user with the given email and password.

        Args:
            email (str): User's email address (required, used for authentication)
            password (str): User's password (optional for social auth scenarios)
            **extra_fields: Additional fields to set on the user model

        Returns:
            CustomUser: The created user instance

        Raises:
            ValueError: If email is not provided
        '''
        if not email:
            raise ValueError('O usuário precisa de um email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        '''
        Create and save a superuser with the given email and password.

        Automatically sets is_staff, is_superuser, and is_active to True.
        Used by Django management commands like createsuperuser.

        Args:
            email (str): Superuser's email address
            password (str): Superuser's password
            **extra_fields: Additional fields to set on the user model

        Returns:
            CustomUser: The created superuser instance

        Raises:
            ValueError: If is_staff or is_superuser is not True
        '''
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    '''
    Custom user model that uses email instead of username for authentication.

    This model extends Django's AbstractUser but removes the username field
    and makes email the primary authentication identifier. Includes additional
    profile fields for complete user information.

    Attributes:
        email: Unique email address used for authentication
        nome_usuario: Optional unique username for public display
        nome_completo: User's full name
        telefone: User's phone number
        foto_perfil: Profile picture upload
        bio: Short biography (max 500 chars)
        created_at: Timestamp when the user was created (auto-generated)
        updated_at: Timestamp when the user was last modified (auto-updated)

    Note:
        Username field is disabled (set to None)
        EMAIL authentication is required for login
    '''
    # ========================================
    # AUTENTICAÇÃO
    # ========================================
    username = None  # Disable username field
    email = models.EmailField(unique=True, verbose_name='Email')

    # ========================================
    # CAMPOS DE PERFIL
    # ========================================
    nome_usuario = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name='Nome de Usuário',
        help_text='Nome público para rankings e identificação (ex: @investidor_top)'
    )
    nome_completo = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Nome Completo',
        help_text='Seu nome completo'
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefone',
        help_text='Número de telefone para contato'
    )
    foto_perfil = models.ImageField(
        upload_to='perfil/',
        blank=True,
        null=True,
        verbose_name='Foto de Perfil',
        help_text='Imagem de perfil (max 5MB)'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Biografia',
        help_text='Conte um pouco sobre você (máximo 500 caracteres)'
    )

    # ========================================
    # TIMESTAMPS
    # ========================================
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    # ========================================
    # CONFIGURAÇÃO
    # ========================================
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']

    def __str__(self):
        '''Return the user's email address as string representation.'''
        return self.email

    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================
    def get_nome_exibicao(self):
        """
        Retorna o melhor nome disponível para exibição.
        
        Ordem de prioridade:
        1. nome_usuario (se definido)
        2. nome_completo (se definido)
        3. parte do email antes do @
        
        Returns:
            str: Nome para exibição
        """
        if self.nome_usuario:
            return self.nome_usuario
        if self.nome_completo:
            return self.nome_completo
        return self.email.split('@')[0]

    def get_iniciais(self):
        """
        Retorna iniciais para usar em avatar placeholder.
        
        Se nome_completo existe: primeiras letras de nome e sobrenome
        Senão: primeiras 2 letras do email
        
        Returns:
            str: Iniciais em maiúsculas (ex: "JD" para João da Silva)
        """
        if self.nome_completo:
            partes = self.nome_completo.split()
            if len(partes) >= 2:
                return f"{partes[0][0]}{partes[1][0]}".upper()
            return partes[0][:2].upper()
        return self.email[:2].upper()

    def get_avatar_url(self):
        """
        Retorna URL da foto de perfil ou None se não houver.
        
        Returns:
            str|None: URL completa da foto ou None
        """
        if self.foto_perfil:
            return self.foto_perfil.url
        return None