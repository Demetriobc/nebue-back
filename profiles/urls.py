from django.urls import path

from .views import (
    ProfileDetailView, 
    ProfileUpdateView, 
    ImportOFXView, 
    ImportOFXPreviewView,
    perfil_view,
    editar_perfil,
    trocar_senha,
    deletar_foto,
)

app_name = 'profile'

urlpatterns = [
    # ========================================
    # VIEWS MODERNAS DE PERFIL
    # ========================================
    path('', perfil_view, name='profile'),
    path('editar/', editar_perfil, name='editar_perfil'),
    path('trocar-senha/', trocar_senha, name='trocar_senha'),
    path('deletar-foto/', deletar_foto, name='deletar_foto'),
    
    # ========================================
    # IMPORT OFX
    # ========================================
    path('import-ofx/', ImportOFXView.as_view(), name='import_ofx'),
    path('import-ofx/preview/', ImportOFXPreviewView.as_view(), name='import_ofx_preview'),
    
    # ========================================
    # VIEWS ANTIGAS (REDIRECIONAM)
    # ========================================
    path('detail/', ProfileDetailView.as_view(), name='profile_detail'),
    path('edit/', ProfileUpdateView.as_view(), name='profile_update'),
]