from django.urls import path
from .views import InsightsView

app_name = 'analytics'

urlpatterns = [
    path('', InsightsView.as_view(), name='insights'),
]
