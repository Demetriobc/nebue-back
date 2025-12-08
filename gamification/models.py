# gamification/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid 

class NivelFinanceiro(models.Model):
    """Níveis de evolução do usuário"""
    NIVEIS = [
        (1, 'Aprendiz Financeiro'),
        (2, 'Organizador Consciente'),
        (3, 'Poupador Estratégico'),
        (4, 'Investidor Iniciante'),
        (5, 'Mestre das Finanças'),
    ]
    
    numero = models.IntegerField(choices=NIVEIS, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    pontos_necessarios = models.IntegerField()
    icone = models.CharField(max_length=50)  # Classe do Font Awesome
    cor = models.CharField(max_length=7, default='#D4AF37')  # Hex color
    
    class Meta:
        ordering = ['numero']
        verbose_name_plural = 'Níveis Financeiros'
    
    def __str__(self):
        return f"Nível {self.numero}: {self.nome}"


class TipoConquista(models.Model):
    """Categorias de conquistas"""
    CATEGORIAS = [
        ('economia', 'Economia'),
        ('organizacao', 'Organização'),
        ('investimento', 'Investimento'),
        ('quitacao', 'Quitação de Dívidas'),
        ('disciplina', 'Disciplina'),
        ('conhecimento', 'Conhecimento Financeiro'),
    ]
    
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, unique=True)
    nome = models.CharField(max_length=100)
    icone = models.CharField(max_length=50)
    cor = models.CharField(max_length=7)
    
    def __str__(self):
        return self.nome


class Conquista(models.Model):
    """Badges e conquistas que o usuário pode desbloquear"""
    RARIDADE = [
        ('comum', 'Comum'),
        ('rara', 'Rara'),
        ('epica', 'Épica'),
        ('lendaria', 'Lendária'),
    ]

    codigo = models.CharField(
        max_length=50,
        unique=True,
        default=uuid.uuid4,   # gera um código único automático
        editable=False        # opcional: evita mexer no admin sem querer
    )
    tipo = models.ForeignKey(TipoConquista, on_delete=models.CASCADE, related_name='conquistas')
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    raridade = models.CharField(max_length=20, choices=RARIDADE, default='comum')
    pontos = models.IntegerField(default=10)
    icone = models.CharField(max_length=50)  # fa-trophy, fa-star, etc
    condicao = models.CharField(max_length=200, help_text="Condição para desbloquear")
    ativa = models.BooleanField(default=True)
    
    # Critérios de desbloqueio (configuráveis)
    meta_valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    meta_quantidade = models.IntegerField(null=True, blank=True)
    meta_dias_consecutivos = models.IntegerField(null=True, blank=True)
    
    criada_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['tipo', 'raridade', 'pontos']
        verbose_name_plural = 'Conquistas'
    
    def __str__(self):
        return f"{self.titulo} ({self.raridade})"
    
    def get_cor_raridade(self):
        cores = {
            'comum': '#9E9E9E',
            'rara': '#2196F3',
            'epica': '#9C27B0',
            'lendaria': '#FFD700'
        }
        return cores.get(self.raridade, '#9E9E9E')


class PerfilGamificacao(models.Model):
    """Perfil de gamificação do usuário"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gamificacao')
    
    # Pontos e Nível
    pontos_totais = models.IntegerField(default=0)
    nivel_atual = models.ForeignKey(NivelFinanceiro, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Streaks (sequências)
    streak_atual = models.IntegerField(default=0, help_text="Dias consecutivos de registro")
    maior_streak = models.IntegerField(default=0)
    ultima_atividade = models.DateField(null=True, blank=True)
    
    # Estatísticas
    conquistas_desbloqueadas = models.IntegerField(default=0)
    desafios_completados = models.IntegerField(default=0)
    
    # Preferências
    notificacoes_gamificacao = models.BooleanField(default=True)
    exibir_ranking = models.BooleanField(default=True)
    
    # ========================================
    # NOVOS CAMPOS DE PRIVACIDADE (ADICIONE AQUI)
    # ========================================
    apelido = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Apelido público do usuário (ex: Rápido Leão)'
    )
    
    exibir_nome_real = models.BooleanField(
        default=False,
        help_text='Se marcado, exibe o email no ranking. Caso contrário, usa apelido anônimo.'
    )
    
    perfil_publico = models.BooleanField(
        default=True,
        help_text='Se desmarcado, o perfil não aparece em rankings públicos'
    )
    # ========================================
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Gamificação'
        verbose_name_plural = 'Perfis de Gamificação'
    
    def __str__(self):
        return f"Gamificação - {self.get_nome_exibicao()}"
    
    # ========================================
    # NOVOS MÉTODOS (ADICIONE AQUI)
    # ========================================
    def save(self, *args, **kwargs):
        """Gera apelido automático se não tiver"""
        if not self.apelido:
            self.apelido = self.gerar_apelido_aleatorio()
        super().save(*args, **kwargs)
    
    def get_nome_exibicao(self):
        """Retorna o nome para exibição pública baseado nas preferências"""
        if self.exibir_nome_real:
            # Usa o email (já que username não existe)
            return self.user.email.split('@')[0]  # Pega só a parte antes do @
        else:
            # Usa o apelido anônimo
            return self.apelido or self.gerar_apelido_aleatorio()
    
    @staticmethod
    def gerar_apelido_aleatorio():
        """Gera um apelido aleatório combinando adjetivo + animal"""
        import random
        
        adjetivos = [
            'Rápido', 'Sábio', 'Forte', 'Ágil', 'Valente', 'Calmo', 'Esperto',
            'Focado', 'Dedicado', 'Persistente', 'Corajoso', 'Astuto', 'Firme',
            'Estratégico', 'Veloz', 'Inteligente', 'Poupador', 'Disciplinado',
            'Organizado', 'Eficiente', 'Próspero', 'Vencedor', 'Ambicioso'
        ]
        
        animais = [
            'Leão', 'Águia', 'Lobo', 'Raposa', 'Tigre', 'Falcão', 'Urso',
            'Pantera', 'Dragão', 'Fênix', 'Coruja', 'Tubarão', 'Gato',
            'Lince', 'Condor', 'Jaguar', 'Puma', 'Leopardo', 'Gavião'
        ]
        
        return f"{random.choice(adjetivos)} {random.choice(animais)}"
    # ========================================
    
    def adicionar_pontos(self, pontos, descricao=""):
        """Adiciona pontos e verifica se subiu de nível"""
        self.pontos_totais += pontos
        nivel_anterior = self.nivel_atual
        
        # Verifica se subiu de nível
        novo_nivel = NivelFinanceiro.objects.filter(
            pontos_necessarios__lte=self.pontos_totais
        ).order_by('-pontos_necessarios').first()
        
        if novo_nivel and (not self.nivel_atual or novo_nivel.numero > self.nivel_atual.numero):
            self.nivel_atual = novo_nivel
            self.save()
            
            # Registra a subida de nível
            HistoricoGamificacao.objects.create(
                perfil=self,
                tipo='nivel_up',
                descricao=f"Subiu para {novo_nivel.nome}!",
                pontos=0
            )
            return True, novo_nivel
        
        self.save()
        
        # Registra os pontos ganhos
        if descricao:
            HistoricoGamificacao.objects.create(
                perfil=self,
                tipo='pontos',
                descricao=descricao,
                pontos=pontos
            )
        
        return False, None
    
    def atualizar_streak(self):
        """Atualiza a sequência de dias consecutivos"""
        hoje = timezone.now().date()
        
        if not self.ultima_atividade:
            # Primeira atividade
            self.streak_atual = 1
            self.ultima_atividade = hoje
            self.save()
            return True
        
        dias_diferenca = (hoje - self.ultima_atividade).days
        
        if dias_diferenca == 0:
            # Já registrou hoje
            return False
        elif dias_diferenca == 1:
            # Manteve a sequência
            self.streak_atual += 1
            if self.streak_atual > self.maior_streak:
                self.maior_streak = self.streak_atual
            self.ultima_atividade = hoje
            
            # Bônus de streak
            bonus = self.streak_atual * 2
            self.adicionar_pontos(bonus, f"Bônus de {self.streak_atual} dias consecutivos!")
            
            self.save()
            return True
        else:
            # Quebrou a sequência
            self.streak_atual = 1
            self.ultima_atividade = hoje
            self.save()
            return False
    
    def progresso_nivel(self):
        """Retorna o progresso percentual para o próximo nível"""
        if not self.nivel_atual:
            return 0
        
        proximo_nivel = NivelFinanceiro.objects.filter(
            numero=self.nivel_atual.numero + 1
        ).first()
        
        if not proximo_nivel:
            return 100  # Já está no nível máximo
        
        pontos_necessarios = proximo_nivel.pontos_necessarios - self.nivel_atual.pontos_necessarios
        pontos_progresso = self.pontos_totais - self.nivel_atual.pontos_necessarios
        
        return min(100, int((pontos_progresso / pontos_necessarios) * 100))


class ConquistaUsuario(models.Model):
    """Conquistas desbloqueadas pelo usuário"""
    perfil = models.ForeignKey(PerfilGamificacao, on_delete=models.CASCADE, related_name='conquistas')
    conquista = models.ForeignKey(Conquista, on_delete=models.CASCADE)
    desbloqueada_em = models.DateTimeField(auto_now_add=True)
    visualizada = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['perfil', 'conquista']
        ordering = ['-desbloqueada_em']
        verbose_name = 'Conquista do Usuário'
        verbose_name_plural = 'Conquistas dos Usuários'
    
    def __str__(self):
        return f"{self.perfil.user.username} - {self.conquista.titulo}"


class Desafio(models.Model):
    """Desafios mensais ou semanais"""
    PERIODO = [
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
        ('personalizado', 'Personalizado'),
    ]
    
    STATUS = [
        ('ativo', 'Ativo'),
        ('pausado', 'Pausado'),
        ('finalizado', 'Finalizado'),
    ]
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    periodo = models.CharField(max_length=20, choices=PERIODO)
    status = models.CharField(max_length=20, choices=STATUS, default='ativo')
    
    # Recompensas
    pontos_recompensa = models.IntegerField(default=50)
    conquista_recompensa = models.ForeignKey(
        Conquista, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='desafios'
    )
    
    # Meta do desafio
    meta_tipo = models.CharField(max_length=50, help_text="economia, reduzir_gastos, etc")
    meta_valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    meta_percentual = models.IntegerField(null=True, blank=True, help_text="Para redução de gastos")
    meta_categoria = models.CharField(max_length=100, null=True, blank=True)
    
    # Datas
    data_inicio = models.DateField()
    data_fim = models.DateField()
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # Configurações
    participantes_minimos = models.IntegerField(default=1)
    publico = models.BooleanField(default=True, help_text="Visível para todos os usuários")
    
    class Meta:
        ordering = ['-data_inicio']
        verbose_name = 'Desafio'
        verbose_name_plural = 'Desafios'
    
    def __str__(self):
        return f"{self.titulo} ({self.periodo})"
    
    def esta_ativo(self):
        hoje = timezone.now().date()
        return self.data_inicio <= hoje <= self.data_fim and self.status == 'ativo'


class DesafioUsuario(models.Model):
    """Participação do usuário em desafios"""
    STATUS_CHOICES = [
        ('em_andamento', 'Em Andamento'),
        ('completado', 'Completado'),
        ('falhado', 'Falhado'),
        ('desistiu', 'Desistiu'),
    ]
    
    perfil = models.ForeignKey(PerfilGamificacao, on_delete=models.CASCADE, related_name='desafios')
    desafio = models.ForeignKey(Desafio, on_delete=models.CASCADE, related_name='participantes')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento')
    progresso = models.IntegerField(default=0, help_text="Progresso em percentual")
    valor_alcancado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    iniciado_em = models.DateTimeField(auto_now_add=True)
    completado_em = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['perfil', 'desafio']
        ordering = ['-iniciado_em']
        verbose_name = 'Desafio do Usuário'
        verbose_name_plural = 'Desafios dos Usuários'
    
    def __str__(self):
        return f"{self.perfil.user.username} - {self.desafio.titulo}"
    
    def atualizar_progresso(self, novo_valor):
        """Atualiza o progresso do desafio"""
        self.valor_alcancado = novo_valor
        
        if self.desafio.meta_valor:
            self.progresso = min(100, int((float(novo_valor) / float(self.desafio.meta_valor)) * 100))
        elif self.desafio.meta_percentual:
            self.progresso = min(100, int(novo_valor))
        
        if self.progresso >= 100:
            self.completar_desafio()
        
        self.save()
    
    def completar_desafio(self):
        """Marca o desafio como completado e entrega recompensas"""
        if self.status == 'completado':
            return
        
        self.status = 'completado'
        self.completado_em = timezone.now()
        self.save()
        
        # Adiciona pontos
        subiu_nivel, novo_nivel = self.perfil.adicionar_pontos(
            self.desafio.pontos_recompensa,
            f"Completou o desafio: {self.desafio.titulo}"
        )
        
        # Desbloqueia conquista se houver
        if self.desafio.conquista_recompensa:
            ConquistaUsuario.objects.get_or_create(
                perfil=self.perfil,
                conquista=self.desafio.conquista_recompensa
            )
        
        # Atualiza contador
        self.perfil.desafios_completados += 1
        self.perfil.save()
        
        return True


class HistoricoGamificacao(models.Model):
    """Histórico de ações de gamificação"""
    TIPOS = [
        ('pontos', 'Pontos Ganhos'),
        ('conquista', 'Conquista Desbloqueada'),
        ('nivel_up', 'Subiu de Nível'),
        ('desafio', 'Desafio Completado'),
        ('streak', 'Streak Mantido'),
    ]
    
    perfil = models.ForeignKey(PerfilGamificacao, on_delete=models.CASCADE, related_name='historico')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descricao = models.CharField(max_length=255)
    pontos = models.IntegerField(default=0)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico de Gamificação'
        verbose_name_plural = 'Históricos de Gamificação'
    
    def __str__(self):
        return f"{self.perfil.user.username} - {self.tipo} - {self.criado_em.strftime('%d/%m/%Y')}"


class Ranking(models.Model):
    """Ranking semanal/mensal de usuários"""
    PERIODO = [
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
        ('geral', 'Geral'),
    ]
    
    periodo = models.CharField(max_length=20, choices=PERIODO)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    
    # Top 10 congelado
    top_usuarios = models.JSONField(default=dict, help_text="Top 10 usuários do período")
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_inicio']
        verbose_name = 'Ranking'
        verbose_name_plural = 'Rankings'
    
    def __str__(self):
        return f"Ranking {self.periodo} - {self.data_inicio.strftime('%d/%m/%Y')}"