import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from .ai_assistant import FinancialAssistant


class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'chatbot/chat.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Buscar conversa ativa ou criar uma nova
        conversation = Conversation.objects.filter(
            user=self.request.user,
            is_active=True
        ).first()
        
        if not conversation:
            conversation = Conversation.objects.create(
                user=self.request.user,
                title='Conversa Principal'
            )
        
        messages = conversation.messages.all()
        
        context['conversation'] = conversation
        context['messages'] = messages
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class SendMessageView(LoginRequiredMixin, View):
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'error': 'Mensagem vazia'}, status=400)
            
            # Buscar ou criar conversa ativa
            conversation = Conversation.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            
            if not conversation:
                conversation = Conversation.objects.create(
                    user=request.user,
                    title='Nova Conversa'
                )
            
            # Salvar mensagem do usuário
            user_msg = Message.objects.create(
                conversation=conversation,
                message_type=Message.MessageType.USER,
                content=user_message
            )
            
            # Buscar histórico da conversa
            conversation_history = [
                {
                    'role': 'user' if msg.message_type == Message.MessageType.USER else 'assistant',
                    'content': msg.content
                }
                for msg in conversation.messages.all().order_by('created_at')[:10]
            ]
            
            # Processar com IA
            assistant = FinancialAssistant(request.user)
            assistant_response = assistant.process_message(user_message, conversation_history)
            
            # Salvar resposta do assistente
            assistant_msg = Message.objects.create(
                conversation=conversation,
                message_type=Message.MessageType.ASSISTANT,
                content=assistant_response
            )
            
            # Atualizar timestamp da conversa
            conversation.updated_at = assistant_msg.created_at
            conversation.save()
            
            return JsonResponse({
                'success': True,
                'user_message': {
                    'id': user_msg.id,
                    'content': user_msg.content,
                    'created_at': user_msg.created_at.isoformat(),
                    'type': 'user'
                },
                'assistant_message': {
                    'id': assistant_msg.id,
                    'content': assistant_msg.content,
                    'created_at': assistant_msg.created_at.isoformat(),
                    'type': 'assistant'
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': f'Erro ao processar mensagem: {str(e)}'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ClearConversationView(LoginRequiredMixin, View):
    """Desativa conversa atual e cria uma nova"""
    
    def post(self, request):
        try:
            # Desativar todas as conversas atuais
            Conversation.objects.filter(
                user=request.user,
                is_active=True
            ).update(is_active=False)
            
            # Criar nova conversa
            new_conversation = Conversation.objects.create(
                user=request.user,
                title='Nova Conversa'
            )
            
            return JsonResponse({
                'success': True,
                'conversation_id': new_conversation.id,
                'message': 'Nova conversa iniciada!'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteConversationView(LoginRequiredMixin, View):
    """Deleta uma conversa permanentemente"""
    
    def post(self, request, pk):
        try:
            conversation = get_object_or_404(
                Conversation,
                pk=pk,
                user=request.user
            )
            
            # Deletar conversa (cascade vai deletar mensagens)
            conversation.delete()
            
            # Criar nova conversa se era a ativa
            if not Conversation.objects.filter(user=request.user, is_active=True).exists():
                Conversation.objects.create(
                    user=request.user,
                    title='Nova Conversa'
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Conversa deletada com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteMessageView(LoginRequiredMixin, View):
    """Deleta uma mensagem específica"""
    
    def post(self, request, pk):
        try:
            message = get_object_or_404(
                Message,
                pk=pk,
                conversation__user=request.user
            )
            
            message.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Mensagem deletada!'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)