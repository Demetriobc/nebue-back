# gamification/urls.py
from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_gamificacao, name='dashboard'),
    
    # Conquistas
    path('conquistas/', views.conquistas_list, name='conquistas_list'),
    path('conquistas/marcar-vistas/', views.marcar_conquistas_vistas, name='marcar_conquistas_vistas'),
    
    # Desafios
    path('desafios/', views.desafios_list, name='desafios_list'),
    path('desafios/<int:desafio_id>/participar/', views.participar_desafio, name='participar_desafio'),
    
    # Ranking
    path('ranking/', views.ranking_view, name='ranking'),
    
    # Níveis
    path('niveis/', views.nivel_detalhes, name='niveis'),
    
    # Histórico
    path('historico/', views.historico_view, name='historico'),
    
    # API endpoints
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/conquistas-novas/', views.api_conquistas_novas, name='api_conquistas_novas'),
]