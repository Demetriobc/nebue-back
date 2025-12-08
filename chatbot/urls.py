from django.urls import path
from .views import (
    ChatView,
    SendMessageView,
    ClearConversationView,
    DeleteConversationView,
    DeleteMessageView
)

app_name = 'chatbot'

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('send/', SendMessageView.as_view(), name='send_message'),
    path('clear/', ClearConversationView.as_view(), name='clear_conversation'),
    path('conversation/<int:pk>/delete/', DeleteConversationView.as_view(), name='delete_conversation'),
    path('message/<int:pk>/delete/', DeleteMessageView.as_view(), name='delete_message'),
]