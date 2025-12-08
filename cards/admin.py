from django.contrib import admin
from .models import Cartao, Fatura, TransacaoCartao


@admin.register(Cartao)
class CartaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'banco', 'bandeira', 'ultimos_digitos', 'limite_total', 
                    'limite_disponivel', 'usuario', 'ativo', 'criado_em']
    list_filter = ['banco', 'bandeira', 'ativo', 'criado_em']
    search_fields = ['nome', 'ultimos_digitos', 'usuario__username']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'conta', 'nome', 'banco', 'bandeira', 'ultimos_digitos')
        }),
        ('Limites', {
            'fields': ('limite_total', 'limite_disponivel')
        }),
        ('Datas', {
            'fields': ('dia_fechamento', 'dia_vencimento')
        }),
        ('Status', {
            'fields': ('ativo', 'criado_em', 'atualizado_em')
        }),
    )


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = ['cartao', 'mes', 'ano', 'valor_total', 'valor_pago', 
                    'status', 'data_vencimento']
    list_filter = ['status', 'mes', 'ano', 'cartao__banco']
    search_fields = ['cartao__nome', 'cartao__usuario__username']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Cartão', {
            'fields': ('cartao',)
        }),
        ('Período', {
            'fields': ('mes', 'ano')
        }),
        ('Valores', {
            'fields': ('valor_total', 'valor_pago')
        }),
        ('Datas', {
            'fields': ('data_fechamento', 'data_vencimento', 'data_pagamento')
        }),
        ('Status', {
            'fields': ('status', 'criado_em', 'atualizado_em')
        }),
    )


@admin.register(TransacaoCartao)
class TransacaoCartaoAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'cartao', 'fatura', 'categoria', 'valor', 
                    'data', 'parcelas', 'parcela_atual']
    list_filter = ['categoria', 'data', 'cartao__banco']
    search_fields = ['descricao', 'cartao__nome', 'cartao__usuario__username']
    readonly_fields = ['criado_em']
    date_hierarchy = 'data'
    
    fieldsets = (
        ('Informações da Transação', {
            'fields': ('cartao', 'fatura', 'descricao', 'categoria', 'valor', 'data')
        }),
        ('Parcelamento', {
            'fields': ('parcelas', 'parcela_atual')
        }),
        ('Metadados', {
            'fields': ('criado_em',)
        }),
    )