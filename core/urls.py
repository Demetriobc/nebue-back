"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from core.views import HomeView
from users.views import DashboardView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('profile/', include(('profiles.urls', 'profile'), namespace='profile')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('categories/', include('categories.urls', namespace='categories')),
    path('transactions/', include('transactions.urls', namespace='transactions')),
    path('cartoes/', include('cards.urls', namespace='cards')),
    path('notifications/', include(('notifications.urls', 'notifications'), namespace='notifications')),  # ← CORRIGIDO!
    path('insights/', include('analytics.urls')),
    path('chat/', include('chatbot.urls')),
    path('gamificacao/', include('gamification.urls')),
]

handler404 = core_views.page_not_found_view
handler500 = core_views.server_error_view

# ========================================
# Servir arquivos de MEDIA em desenvolvimento
# ========================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)