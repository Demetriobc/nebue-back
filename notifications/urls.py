from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Page view
    path('', views.notifications_page, name='notifications_page'),
    
    # API endpoints
    path('api/list/', views.notifications_list, name='list'),
    path('mark-read/<int:notification_id>/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    
    # Delete actions
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
    path('delete-all-read/', views.delete_all_read, name='delete_all_read'),
]