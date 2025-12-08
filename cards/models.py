from django.db import models
from django.conf import settings
from decimal import Decimal
from accounts.models import Account  # ← IMPORTA O Account QUE JÁ EXISTE


# REMOVE A CLASSE Conta - NÃO PRECISA MAIS!
# Vamos usar o Account do app accounts


class Cartao(models.Model):
    """Model principal de Cartão de Crédito"""
    
    BANDEIRAS = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('elo', 'Elo'),
        ('american_express', 'American Express'),
        ('hipercard', 'Hipercard'),
        ('outros', 'Outros'),
    ]
    
    BANCOS = [
        ('nubank', 'Nubank'),
        ('inter', 'Inter'),
        ('c6', 'C6 Bank'),
        ('neon', 'Neon'),
        ('picpay', 'PicPay'),
        ('itau', 'Itaú'),
        ('bradesco', 'Bradesco'),
        ('santander', 'Santander'),
        ('bb', 'Banco do Brasil'),
        ('caixa', 'Caixa'),
        ('outros', 'Outros'),
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cartoes')
    conta = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='cartoes', null=True, blank=True)  # ← MUDOU: Conta → Account
    
    # Informações do cartão
    nome = models.CharField(max_length=100, help_text="Nome/apelido do cartão")
    banco = models.CharField(max_length=50, choices=BANCOS, default='outros')
    bandeira = models.CharField(max_length=50, choices=BANDEIRAS, default='visa')
    ultimos_digitos = models.CharField(max_length=4, help_text="Últimos 4 dígitos")
    
    # Limites e faturas
    limite_total = models.DecimalField(max_digits=10, decimal_places=2)
    limite_disponivel = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Datas
    dia_fechamento = models.IntegerField(help_text="Dia do fechamento da fatura (1-31)")
    dia_vencimento = models.IntegerField(help_text="Dia do vencimento da fatura (1-31)")
    
    # Status
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cartão'
        verbose_name_plural = 'Cartões'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.nome} - {self.banco} (****{self.ultimos_digitos})"
    
    @property
    def limite_usado(self):
        """Calcula o limite usado"""
        return self.limite_total - self.limite_disponivel
    
    @property
    def percentual_usado(self):
        """Calcula o percentual do limite usado"""
        if self.limite_total > 0:
            return (self.limite_usado / self.limite_total) * 100
        return 0
    
    @property
    def fatura_atual(self):
        """Retorna a fatura do mês atual"""
        from datetime import datetime
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        return self.faturas.filter(mes=mes_atual, ano=ano_atual).first()
    
    def get_imagem_banco(self):
        """Retorna a URL da imagem do banco"""
        imagens = {
            'nubank': '/static/images/cartoes/nubank.png',
            'inter': '/static/images/cartoes/inter.png',
            'c6': '/static/images/cartoes/c6.png',
            'neon': '/static/images/cartoes/neon.png',
            'picpay': '/static/images/cartoes/picpay.png',
            'itau': '/static/images/cartoes/itau.png',
            'bradesco': '/static/images/cartoes/bradesco.png',
            'santander': '/static/images/cartoes/santander.png',
            'bb': '/static/images/cartoes/bb.png',
            'caixa': '/static/images/cartoes/caixa.png',
        }
        return imagens.get(self.banco, '/static/images/cartoes/default.png')
    
    def get_cor_banco(self):
        """Retorna a cor característica do banco"""
        cores = {
            'nubank': '#8A05BE',
            'inter': '#FF7A00',
            'c6': '#000000',
            'neon': '#00D9F5',
            'picpay': '#21C25E',
            'itau': '#EC7000',
            'bradesco': '#CC092F',
            'santander': '#EC0000',
            'bb': '#FFF500',
            'caixa': '#0066B3',
        }
        return cores.get(self.banco, '#D4AF37')


class Fatura(models.Model):
    """Model de Fatura do Cartão"""
    
    STATUS = [
        ('aberta', 'Aberta'),
        ('fechada', 'Fechada'),
        ('paga', 'Paga'),
        ('atrasada', 'Atrasada'),
    ]
    
    cartao = models.ForeignKey(Cartao, on_delete=models.CASCADE, related_name='faturas')
    
    # Período
    mes = models.IntegerField()
    ano = models.IntegerField()
    
    # Valores
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Datas
    data_fechamento = models.DateField()
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS, default='aberta')
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fatura'
        verbose_name_plural = 'Faturas'
        ordering = ['-ano', '-mes']
        unique_together = ['cartao', 'mes', 'ano']
    
    def __str__(self):
        return f"Fatura {self.mes}/{self.ano} - {self.cartao.nome}"
    
    @property
    def valor_pendente(self):
        """Calcula o valor pendente da fatura"""
        return self.valor_total - self.valor_pago
    
    @property
    def esta_paga(self):
        """Verifica se a fatura está totalmente paga"""
        return self.valor_pago >= self.valor_total
    
    def atualizar_total(self):
        """Recalcula o total da fatura baseado nas transações"""
        total = sum(t.valor for t in self.transacoes.all())
        self.valor_total = total
        self.save()


class TransacaoCartao(models.Model):
    """Model de Transação do Cartão"""
    
    CATEGORIAS = [
        ('alimentacao', 'Alimentação'),
        ('transporte', 'Transporte'),
        ('moradia', 'Moradia'),
        ('saude', 'Saúde'),
        ('educacao', 'Educação'),
        ('lazer', 'Lazer'),
        ('compras', 'Compras'),
        ('outros', 'Outros'),
    ]
    
    cartao = models.ForeignKey(Cartao, on_delete=models.CASCADE, related_name='transacoes')
    fatura = models.ForeignKey(Fatura, on_delete=models.CASCADE, related_name='transacoes')
    
    # Informações da transação
    descricao = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='outros')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    
    # Parcelamento
    parcelas = models.IntegerField(default=1)
    parcela_atual = models.IntegerField(default=1)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transação de Cartão'
        verbose_name_plural = 'Transações de Cartão'
        ordering = ['-data']
    
    def __str__(self):
        if self.parcelas > 1:
            return f"{self.descricao} - {self.parcela_atual}/{self.parcelas}"
        return self.descricao
    
    @property
    def valor_total_parcelado(self):
        """Retorna o valor total se for parcelado"""
        return self.valor * self.parcelas