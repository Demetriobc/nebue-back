# gamification/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    NivelFinanceiro, TipoConquista, Conquista, PerfilGamificacao,
    ConquistaUsuario, Desafio, DesafioUsuario, HistoricoGamificacao, Ranking
)


@admin.register(NivelFinanceiro)
class NivelFinanceiroAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nome', 'pontos_necessarios', 'preview_icone', 'preview_cor']
    list_editable = ['pontos_necessarios']
    ordering = ['numero']
    
    def preview_icone(self, obj):
        return format_html('<i class="fa {} fa-2x"></i>', obj.icone)
    preview_icone.short_description = 'Ícone'
    
    def preview_cor(self, obj):
        return format_html(
            '<span style="background: {}; padding: 5px 15px; border-radius: 5px; color: white;">{}</span>',
            obj.cor, obj.cor
        )
    preview_cor.short_description = 'Cor'


@admin.register(TipoConquista)
class TipoConquistaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'preview_icone', 'preview_cor']
    
    def preview_icone(self, obj):
        return format_html('<i class="fa {} fa-2x" style="color: {};"></i>', obj.icone, obj.cor)
    preview_icone.short_description = 'Ícone'
    
    def preview_cor(self, obj):
        return format_html(
            '<span style="background: {}; padding: 5px 15px; border-radius: 5px; color: white;">{}</span>',
            obj.cor, obj.cor
        )
    preview_cor.short_description = 'Cor'


@admin.register(Conquista)
class ConquistaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'raridade', 'pontos', 'preview_icone', 'ativa']
    list_filter = ['tipo', 'raridade', 'ativa']
    search_fields = ['titulo', 'descricao']
    list_editable = ['pontos', 'ativa']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'titulo', 'descricao', 'raridade', 'pontos', 'icone', 'ativa')
        }),
        ('Critérios de Desbloqueio', {
            'fields': ('condicao', 'meta_valor', 'meta_quantidade', 'meta_dias_consecutivos'),
            'description': 'Configure os critérios necessários para desbloquear esta conquista'
        }),
    )
    
    def preview_icone(self, obj):
        return format_html('<i class="fa {} fa-2x" style="color: {};"></i>', 
                          obj.icone, obj.get_cor_raridade())
    preview_icone.short_description = 'Ícone'


@admin.register(PerfilGamificacao)
class PerfilGamificacaoAdmin(admin.ModelAdmin):
    list_display = ['user', 'nivel_atual', 'pontos_totais', 'streak_atual', 
                    'conquistas_desbloqueadas', 'desafios_completados']
    list_filter = ['nivel_atual']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['criado_em', 'atualizado_em', 'progresso_nivel_display']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Pontuação e Nível', {
            'fields': ('pontos_totais', 'nivel_atual', 'progresso_nivel_display')
        }),
        ('Streaks', {
            'fields': ('streak_atual', 'maior_streak', 'ultima_atividade')
        }),
        ('Estatísticas', {
            'fields': ('conquistas_desbloqueadas', 'desafios_completados')
        }),
        ('Preferências', {
            'fields': ('notificacoes_gamificacao', 'exibir_ranking')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def progresso_nivel_display(self, obj):
        progresso = obj.progresso_nivel()
        return format_html(
            '<div style="width: 200px; background: #ddd; height: 20px; border-radius: 10px;">'
            '<div style="width: {}%; background: #4CAF50; height: 100%; border-radius: 10px;"></div>'
            '</div> {}%',
            progresso, progresso
        )
    progresso_nivel_display.short_description = 'Progresso para Próximo Nível'


@admin.register(ConquistaUsuario)
class ConquistaUsuarioAdmin(admin.ModelAdmin):
    list_display = ['perfil', 'conquista', 'desbloqueada_em', 'visualizada']
    list_filter = ['visualizada', 'desbloqueada_em', 'conquista__raridade']
    search_fields = ['perfil__user__username', 'conquista__titulo']
    date_hierarchy = 'desbloqueada_em'
    
    readonly_fields = ['desbloqueada_em']


@admin.register(Desafio)
class DesafioAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'periodo', 'status', 'pontos_recompensa', 
                    'data_inicio', 'data_fim', 'total_participantes']
    list_filter = ['periodo', 'status', 'publico']
    search_fields = ['titulo', 'descricao']
    date_hierarchy = 'data_inicio'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'descricao', 'periodo', 'status', 'publico')
        }),
        ('Recompensas', {
            'fields': ('pontos_recompensa', 'conquista_recompensa')
        }),
        ('Meta do Desafio', {
            'fields': ('meta_tipo', 'meta_valor', 'meta_percentual', 'meta_categoria')
        }),
        ('Período', {
            'fields': ('data_inicio', 'data_fim')
        }),
        ('Configurações', {
            'fields': ('participantes_minimos',)
        }),
    )
    
    def total_participantes(self, obj):
        return obj.participantes.count()
    total_participantes.short_description = 'Participantes'


@admin.register(DesafioUsuario)
class DesafioUsuarioAdmin(admin.ModelAdmin):
    list_display = ['perfil', 'desafio', 'status', 'progresso_bar', 
                    'iniciado_em', 'completado_em']
    list_filter = ['status', 'desafio__periodo']
    search_fields = ['perfil__user__username', 'desafio__titulo']
    date_hierarchy = 'iniciado_em'
    
    readonly_fields = ['iniciado_em', 'completado_em']
    
    def progresso_bar(self, obj):
        return format_html(
            '<div style="width: 150px; background: #ddd; height: 15px; border-radius: 10px;">'
            '<div style="width: {}%; background: #4CAF50; height: 100%; border-radius: 10px;"></div>'
            '</div> {}%',
            obj.progresso, obj.progresso
        )
    progresso_bar.short_description = 'Progresso'


@admin.register(HistoricoGamificacao)
class HistoricoGamificacaoAdmin(admin.ModelAdmin):
    list_display = ['perfil', 'tipo', 'descricao', 'pontos', 'criado_em']
    list_filter = ['tipo', 'criado_em']
    search_fields = ['perfil__user__username', 'descricao']
    date_hierarchy = 'criado_em'
    
    readonly_fields = ['criado_em']


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ['periodo', 'data_inicio', 'data_fim', 'criado_em']
    list_filter = ['periodo']
    date_hierarchy = 'data_inicio'
    
    readonly_fields = ['criado_em', 'top_usuarios_display']
    
    def top_usuarios_display(self, obj):
        if not obj.top_usuarios:
            return "Nenhum usuário no ranking"
        
        html = '<ol>'
        for user_data in obj.top_usuarios.get('usuarios', [])[:10]:
            html += f'<li><strong>{user_data.get("username")}</strong> - {user_data.get("pontos")} pontos</li>'
        html += '</ol>'
        return format_html(html)
    top_usuarios_display.short_description = 'Top 10 Usuários'