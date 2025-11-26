from django.urls import path
from . import views

app_name = 'cards'

urlpatterns = [
    # Listagem e CRUD de cartões
    path('', views.cartoes_list, name='cartoes_list'),
    path('novo/', views.cartao_create, name='cartao_create'),
    path('<int:cartao_id>/', views.cartao_detail, name='cartao_detail'),
    path('<int:cartao_id>/editar/', views.cartao_edit, name='cartao_edit'),
    path('<int:cartao_id>/deletar/', views.cartao_delete, name='cartao_delete'),
    
    # Transações
    path('<int:cartao_id>/transacao/nova/', views.transacao_create, name='transacao_create'),
    
    # Faturas
    path('fatura/<int:fatura_id>/', views.fatura_detail, name='fatura_detail'),
    path('fatura/<int:fatura_id>/pagar/', views.fatura_pagar, name='fatura_pagar'),
]