from django.urls import path

from .views import ProfileDetailView, ProfileUpdateView, ImportOFXView, ImportOFXPreviewView

app_name = 'profiles'

urlpatterns = [
    path('', ProfileDetailView.as_view(), name='profile_detail'),
    path('edit/', ProfileUpdateView.as_view(), name='profile_update'),
    path('import-ofx/', ImportOFXView.as_view(), name='import_ofx'),
    path('import-ofx/preview/', ImportOFXPreviewView.as_view(), name='import_ofx_preview'),
]