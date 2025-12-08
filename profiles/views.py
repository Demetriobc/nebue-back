from decimal import Decimal
from datetime import datetime
import json
import os

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView, FormView, View
from django.http import JsonResponse

import ofxparse
from notifications.models import Notification
from accounts.models import Account
from categories.models import Category
from transactions.models import Transaction
from .forms import ProfileForm, OFXImportForm, OFXPreviewConfirmForm
from .models import Profile


# ========================================
# VIEWS MODERNAS DE PERFIL
# ========================================

@login_required
def perfil_view(request):
    """Visualizar perfil completo do usuário"""
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profiles/perfil.html', context)


@login_required
def editar_perfil(request):
    """Editar informações completas do perfil"""
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Atualiza campos do CustomUser
        user.nome_completo = request.POST.get('nome_completo', '').strip()
        user.nome_usuario = request.POST.get('nome_usuario', '').strip()
        user.telefone = request.POST.get('telefone', '').strip()
        user.bio = request.POST.get('bio', '').strip()
        
        # Atualiza campos do Profile (compatibilidade)
        profile.full_name = user.nome_completo
        profile.phone = user.telefone
        
        # Valida nome de usuário único
        nome_usuario = user.nome_usuario
        if nome_usuario:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(nome_usuario=nome_usuario).exclude(id=user.id).exists():
                messages.error(request, '❌ Este nome de usuário já está em uso!')
                return redirect('profile:editar_perfil')
        
        # Upload de foto
        if 'foto_perfil' in request.FILES:
            foto = request.FILES['foto_perfil']
            
            # Valida tamanho (5MB)
            if foto.size > 5 * 1024 * 1024:
                messages.error(request, '❌ A imagem deve ter no máximo 5MB!')
                return redirect('profile:editar_perfil')
            
            # Valida formato
            ext = os.path.splitext(foto.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                messages.error(request, '❌ Formato inválido! Use JPG, PNG ou GIF.')
                return redirect('profile:editar_perfil')
            
            # Remove foto antiga se existir
            if user.foto_perfil:
                try:
                    if os.path.isfile(user.foto_perfil.path):
                        os.remove(user.foto_perfil.path)
                except:
                    pass
            
            # Salva nova foto
            user.foto_perfil = foto
        
        # Opção para remover foto
        if request.POST.get('remover_foto') == 'true':
            if user.foto_perfil:
                try:
                    if os.path.isfile(user.foto_perfil.path):
                        os.remove(user.foto_perfil.path)
                except:
                    pass
                user.foto_perfil = None
        
        user.save()
        profile.save()
        messages.success(request, '✅ Perfil atualizado com sucesso!')
        return redirect('profile:profile')
    
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profiles/editar_perfil.html', context)


@login_required
def trocar_senha(request):
    """Página para trocar senha"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantém o usuário logado
            messages.success(request, '✅ Senha alterada com sucesso!')
            return redirect('profile:profile')
        else:
            for error in form.errors.values():
                messages.error(request, f'❌ {error[0]}')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'profiles/trocar_senha.html', context)


@login_required
def deletar_foto(request):
    """Remove foto de perfil (via AJAX)"""
    if request.method == 'POST':
        user = request.user
        if user.foto_perfil:
            try:
                if os.path.isfile(user.foto_perfil.path):
                    os.remove(user.foto_perfil.path)
            except:
                pass
            user.foto_perfil = None
            user.save()
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# ========================================
# VIEWS ANTIGAS (MANTIDAS)
# ========================================

class ProfileDetailView(LoginRequiredMixin, DetailView):
    """View to display the profile of the authenticated user (ANTIGA - REDIRECIONA)"""
    model = Profile
    template_name = 'profiles/profile_detail.html'
    context_object_name = 'profile'

    def get(self, request, *args, **kwargs):
        # Redireciona para a nova view moderna
        return redirect('profile:profile')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating the profile (ANTIGA - REDIRECIONA)"""
    model = Profile
    form_class = ProfileForm
    template_name = 'profiles/profile_form.html'
    success_url = reverse_lazy('profile:profile')

    def get(self, request, *args, **kwargs):
        # Redireciona para a nova view moderna
        return redirect('profile:editar_perfil')


# ========================================
# VIEWS DE IMPORT OFX (MANTIDAS)
# ========================================

class ImportOFXView(LoginRequiredMixin, FormView):
    """Step 1: Upload OFX file and select account."""
    form_class = OFXImportForm
    template_name = 'profiles/import_ofx.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        ofx_file = form.cleaned_data['ofx_file']
        account = form.cleaned_data['account']
        
        try:
            ofx = ofxparse.OfxParser.parse(ofx_file)
            user_categories = self._get_user_categories()
            transactions_data = []
            skipped_count = 0
            
            for ofx_transaction in ofx.account.statement.transactions:
                if self._is_duplicate(account, ofx_transaction):
                    skipped_count += 1
                    continue
                
                amount = abs(Decimal(str(ofx_transaction.amount)))
                transaction_type = 'INCOME' if ofx_transaction.amount > 0 else 'EXPENSE'
                category = self._map_category(
                    ofx_transaction.memo or ofx_transaction.payee,
                    transaction_type,
                    user_categories
                )
                
                transactions_data.append({
                    'date': ofx_transaction.date.date().isoformat(),
                    'description': self._format_description(ofx_transaction),
                    'amount': float(amount),
                    'type': transaction_type,
                    'category': category.id,
                    'category_name': category.name,
                    'category_color': category.color,
                })
            
            self.request.session['ofx_import_data'] = {
                'account_id': account.id,
                'transactions': transactions_data,
                'skipped_count': skipped_count,
            }
            
            return redirect('profile:import_ofx_preview')
            
        except Exception as e:
            messages.error(
                self.request,
                f'Erro ao processar arquivo OFX: {str(e)}. '
                'Verifique se o arquivo está no formato correto.'
            )
            return self.form_invalid(form)

    def _get_user_categories(self):
        categories = Category.objects.filter(user=self.request.user)
        return {
            'income': list(categories.filter(category_type=Category.CategoryType.INCOME)),
            'expense': list(categories.filter(category_type=Category.CategoryType.EXPENSE))
        }

    def _is_duplicate(self, account, ofx_transaction):
        amount = abs(Decimal(str(ofx_transaction.amount)))
        description = self._format_description(ofx_transaction)
        
        return Transaction.objects.filter(
            account=account,
            transaction_date=ofx_transaction.date.date(),
            amount=amount,
            description__icontains=description[:50]
        ).exists()

    def _map_category(self, description, transaction_type, user_categories):
        if not description:
            return self._get_default_category(transaction_type, user_categories)
        
        description_upper = description.upper()
        
        expense_keywords = {
            'ALIMENTACAO': ['MERCADO', 'SUPERMERCADO', 'PADARIA', 'RESTAURANTE', 'LANCHONETE', 'IFOOD', 'UBER EATS', 'RAPPI'],
            'TRANSPORTE': ['POSTO', 'COMBUSTIVEL', 'UBER', '99', 'METRO', 'ONIBUS', 'ESTACIONAMENTO', 'PEDÁGIO'],
            'SAUDE': ['FARMACIA', 'DROGARIA', 'HOSPITAL', 'CLINICA', 'MEDICO', 'LABORATORIO', 'CONSULTA'],
            'MORADIA': ['ALUGUEL', 'CONDOMINIO', 'IPTU', 'LUZ', 'AGUA', 'GAS', 'ENERGIA', 'INTERNET'],
            'EDUCACAO': ['ESCOLA', 'FACULDADE', 'CURSO', 'LIVRO', 'MATERIAL ESCOLAR', 'UNIVERSIDADE'],
            'LAZER': ['CINEMA', 'TEATRO', 'NETFLIX', 'SPOTIFY', 'AMAZON', 'STREAMING', 'INGRESSO'],
            'VESTUARIO': ['ROUPA', 'CALCADO', 'LOJA', 'MAGAZINE', 'SHOPPING', 'ZARA', 'C&A'],
        }
        
        income_keywords = {
            'SALARIO': ['SALARIO', 'PAGAMENTO', 'FOLHA', 'VENCIMENTO', 'REMUNERACAO'],
            'FREELANCE': ['FREELANCE', 'FREELA', 'AUTONOMO', 'SERVICO', 'PRESTACAO'],
            'INVESTIMENTO': ['DIVIDENDO', 'RENDIMENTO', 'JUROS', 'RESGATE', 'APLICACAO'],
        }
        
        keywords_map = income_keywords if transaction_type == 'INCOME' else expense_keywords
        category_list = user_categories['income'] if transaction_type == 'INCOME' else user_categories['expense']
        
        for category_name, keywords in keywords_map.items():
            if any(keyword in description_upper for keyword in keywords):
                for category in category_list:
                    if category_name.lower() in category.name.lower():
                        return category
        
        for category in category_list:
            if category.name.upper() in description_upper:
                return category
        
        return self._get_default_category(transaction_type, user_categories)

    def _get_default_category(self, transaction_type, user_categories):
        category_list = user_categories['income'] if transaction_type == 'INCOME' else user_categories['expense']
        
        if category_list:
            return category_list[0]
        
        category_type = Category.CategoryType.INCOME if transaction_type == 'INCOME' else Category.CategoryType.EXPENSE
        default_name = "Entrada Geral" if transaction_type == 'INCOME' else "Despesa Geral"
        
        category, _ = Category.objects.get_or_create(
            user=self.request.user,
            name=default_name,
            defaults={
                'category_type': category_type,
                'color': '#6B7280'
            }
        )
        return category

    def _format_description(self, ofx_transaction):
        parts = []
        if ofx_transaction.payee:
            parts.append(ofx_transaction.payee)
        if ofx_transaction.memo and ofx_transaction.memo != ofx_transaction.payee:
            parts.append(ofx_transaction.memo)
        
        return ' - '.join(parts) if parts else 'Transação importada'


class ImportOFXPreviewView(LoginRequiredMixin, View):
    """Step 2: Preview transactions and confirm import."""
    template_name = 'profiles/import_ofx_preview.html'

    def get(self, request):
        import_data = request.session.get('ofx_import_data')
        
        if not import_data:
            messages.warning(request, 'Nenhum arquivo para visualizar. Por favor, faça upload primeiro.')
            return redirect('profile:import_ofx')
        
        try:
            account = Account.objects.get(id=import_data['account_id'], user=request.user)
        except Account.DoesNotExist:
            messages.error(request, 'Conta não encontrada.')
            return redirect('profile:import_ofx')
        
        form = OFXPreviewConfirmForm(
            transactions_data=import_data['transactions'],
            user=request.user
        )
        
        transactions_with_fields = []
        for idx, trans_data in enumerate(import_data['transactions']):
            transactions_with_fields.append({
                'data': trans_data,
                'category_field': form[f'category_{idx}'],
                'date_field': form[f'date_{idx}'],
                'description_field': form[f'description_{idx}'],
                'amount_field': form[f'amount_{idx}'],
                'type_field': form[f'type_{idx}'],
            })
        
        context = {
            'form': form,
            'account': account,
            'transactions_with_fields': transactions_with_fields,
            'total_transactions': len(import_data['transactions']),
            'skipped_count': import_data.get('skipped_count', 0),
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        import_data = request.session.get('ofx_import_data')
        
        if not import_data:
            messages.warning(request, 'Sessão expirada. Por favor, faça upload novamente.')
            return redirect('profile:import_ofx')
        
        try:
            account = Account.objects.get(id=import_data['account_id'], user=request.user)
        except Account.DoesNotExist:
            messages.error(request, 'Conta não encontrada.')
            return redirect('profile:import_ofx')
        
        form = OFXPreviewConfirmForm(
            request.POST,
            transactions_data=import_data['transactions'],
            user=request.user
        )
        
        if form.is_valid():
            created_count = 0
            error_count = 0
            
            try:
                with db_transaction.atomic():
                    for idx, trans_data in enumerate(import_data['transactions']):
                        try:
                            category = form.cleaned_data[f'category_{idx}']
                            
                            Transaction.objects.create(
                                account=account,
                                category=category,
                                transaction_type=trans_data['type'],
                                amount=Decimal(str(trans_data['amount'])),
                                transaction_date=trans_data['date'],
                                description=trans_data['description']
                            )
                            created_count += 1
                            
                        except Exception as e:
                            error_count += 1
                            print(f"Error creating transaction: {e}")
                            continue
                
                del request.session['ofx_import_data']
                
                if created_count > 0:
                    messages.success(
                        request,
                        f'✅ Sucesso! {created_count} transação(ões) importada(s).'
                    )
                    
                    Notification.create_import_success(
                        user=request.user,
                        count=created_count
                    )
                
                if import_data.get('skipped_count', 0) > 0:
                    messages.info(
                        request,
                        f'ℹ️ {import_data["skipped_count"]} transação(ões) duplicada(s) ignorada(s).'
                    )
                
                if error_count > 0:
                    messages.warning(
                        request,
                        f'⚠️ {error_count} transação(ões) com erro.'
                    )
                
                return redirect('profile:profile')
                
            except Exception as e:
                messages.error(request, f'Erro ao importar transações: {str(e)}')
                return redirect('profile:import_ofx')
        
        context = {
            'form': form,
            'account': account,
            'transactions': import_data['transactions'],
            'total_transactions': len(import_data['transactions']),
            'skipped_count': import_data.get('skipped_count', 0),
        }
        return render(request, self.template_name, context)