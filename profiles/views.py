from decimal import Decimal
from datetime import datetime
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction as db_transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView, FormView, View

import ofxparse
from notifications.models import Notification
from accounts.models import Account
from categories.models import Category
from transactions.models import Transaction
from .forms import ProfileForm, OFXImportForm, OFXPreviewConfirmForm
from .models import Profile


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """
    View to display the profile of the authenticated user.

    Security:
    - LoginRequiredMixin ensures only authenticated users can access
    - get_object override ensures users can only view their own profile
    - No pk parameter needed in URL - always shows current user's profile
    """
    model = Profile
    template_name = 'profiles/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        """
        Override to always return the profile of the authenticated user.

        This ensures:
        1. User cannot access other users' profiles
        2. No need for pk in URL
        3. Simple and secure access pattern
        Optimized with select_related to avoid N+1 queries.

        Returns:
            Profile: The profile instance of the logged-in user
        """
        return Profile.objects.select_related('user').get(user=self.request.user)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating the profile of the authenticated user.

    Security:
    - LoginRequiredMixin ensures only authenticated users can access
    - get_object override ensures users can only edit their own profile
    - No pk parameter needed in URL - always edits current user's profile
    - Displays success message after successful update
    """
    model = Profile
    form_class = ProfileForm
    template_name = 'profiles/profile_form.html'
    success_url = reverse_lazy('profiles:profile_detail')

    def get_object(self, queryset=None):
        """
        Override to always return the profile of the authenticated user.

        This ensures users can only edit their own profile and prevents
        unauthorized access to other users' profiles.
        Optimized with select_related to avoid N+1 queries.

        Returns:
            Profile: The profile instance of the logged-in user
        """
        return Profile.objects.select_related('user').get(user=self.request.user)

    def form_valid(self, form):
        """
        Display success message after successful profile update.

        Args:
            form: The validated ProfileForm instance

        Returns:
            HttpResponse: Redirect to success_url after saving
        """
        messages.success(self.request, 'Perfil atualizado com sucesso!')
        return super().form_valid(form)


class ImportOFXView(LoginRequiredMixin, FormView):
    """
    Step 1: Upload OFX file and select account.
    
    This is the first step of a 2-step import process:
    1. Upload file → Parse → Show preview
    2. User confirms/adjusts categories → Import
    """
    form_class = OFXImportForm
    template_name = 'profiles/import_ofx.html'

    def get_form_kwargs(self):
        """Pass the current user to the form to filter accounts."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        Parse OFX file and show preview to user.
        
        Process:
        1. Parse OFX file
        2. Extract transaction data
        3. Map categories (automatically)
        4. Store in session
        5. Redirect to preview page
        """
        ofx_file = form.cleaned_data['ofx_file']
        account = form.cleaned_data['account']
        
        try:
            # Parse OFX file
            ofx = ofxparse.OfxParser.parse(ofx_file)
            
            # Get user's categories for mapping
            user_categories = self._get_user_categories()
            
            # Process transactions and prepare preview data
            transactions_data = []
            skipped_count = 0
            
            for ofx_transaction in ofx.account.statement.transactions:
                # Check for duplicates
                if self._is_duplicate(account, ofx_transaction):
                    skipped_count += 1
                    continue
                
                # Determine transaction type and amount
                amount = abs(Decimal(str(ofx_transaction.amount)))
                transaction_type = (
                    'INCOME'
                    if ofx_transaction.amount > 0 
                    else 'EXPENSE'
                )
                
                # Map to category
                category = self._map_category(
                    ofx_transaction.memo or ofx_transaction.payee,
                    transaction_type,
                    user_categories
                )
                
                # Prepare transaction data
                transactions_data.append({
                    'date': ofx_transaction.date.date().isoformat(),
                    'description': self._format_description(ofx_transaction),
                    'amount': float(amount),
                    'type': transaction_type,
                    'category': category.id,
                    'category_name': category.name,
                    'category_color': category.color,
                })
            
            # Store in session for next step
            self.request.session['ofx_import_data'] = {
                'account_id': account.id,
                'transactions': transactions_data,
                'skipped_count': skipped_count,
            }
            
            # Redirect to preview page
            return redirect('profiles:import_ofx_preview')
            
        except Exception as e:
            messages.error(
                self.request,
                f'Erro ao processar arquivo OFX: {str(e)}. '
                'Verifique se o arquivo está no formato correto.'
            )
            return self.form_invalid(form)

    def _get_user_categories(self):
        """Get all categories belonging to the user, organized by type."""
        categories = Category.objects.filter(user=self.request.user)
        return {
            'income': list(categories.filter(category_type=Category.CategoryType.INCOME)),
            'expense': list(categories.filter(category_type=Category.CategoryType.EXPENSE))
        }

    def _is_duplicate(self, account, ofx_transaction):
        """Check if a transaction already exists (duplicate detection)."""
        amount = abs(Decimal(str(ofx_transaction.amount)))
        description = self._format_description(ofx_transaction)
        
        return Transaction.objects.filter(
            account=account,
            transaction_date=ofx_transaction.date.date(),
            amount=amount,
            description__icontains=description[:50]
        ).exists()

    def _map_category(self, description, transaction_type, user_categories):
        """Intelligently map transaction description to a category using keywords."""
        if not description:
            return self._get_default_category(transaction_type, user_categories)
        
        description_upper = description.upper()
        
        # Keyword mapping for expense categories
        expense_keywords = {
            'ALIMENTACAO': ['MERCADO', 'SUPERMERCADO', 'PADARIA', 'RESTAURANTE', 'LANCHONETE', 'IFOOD', 'UBER EATS', 'RAPPI'],
            'TRANSPORTE': ['POSTO', 'COMBUSTIVEL', 'UBER', '99', 'METRO', 'ONIBUS', 'ESTACIONAMENTO', 'PEDÁGIO'],
            'SAUDE': ['FARMACIA', 'DROGARIA', 'HOSPITAL', 'CLINICA', 'MEDICO', 'LABORATORIO', 'CONSULTA'],
            'MORADIA': ['ALUGUEL', 'CONDOMINIO', 'IPTU', 'LUZ', 'AGUA', 'GAS', 'ENERGIA', 'INTERNET'],
            'EDUCACAO': ['ESCOLA', 'FACULDADE', 'CURSO', 'LIVRO', 'MATERIAL ESCOLAR', 'UNIVERSIDADE'],
            'LAZER': ['CINEMA', 'TEATRO', 'NETFLIX', 'SPOTIFY', 'AMAZON', 'STREAMING', 'INGRESSO'],
            'VESTUARIO': ['ROUPA', 'CALCADO', 'LOJA', 'MAGAZINE', 'SHOPPING', 'ZARA', 'C&A'],
        }
        
        # Keyword mapping for income categories
        income_keywords = {
            'SALARIO': ['SALARIO', 'PAGAMENTO', 'FOLHA', 'VENCIMENTO', 'REMUNERACAO'],
            'FREELANCE': ['FREELANCE', 'FREELA', 'AUTONOMO', 'SERVICO', 'PRESTACAO'],
            'INVESTIMENTO': ['DIVIDENDO', 'RENDIMENTO', 'JUROS', 'RESGATE', 'APLICACAO'],
        }
        
        # Select appropriate keyword set
        keywords_map = income_keywords if transaction_type == 'INCOME' else expense_keywords
        category_list = user_categories['income'] if transaction_type == 'INCOME' else user_categories['expense']
        
        # Try to match keywords
        for category_name, keywords in keywords_map.items():
            if any(keyword in description_upper for keyword in keywords):
                for category in category_list:
                    if category_name.lower() in category.name.lower():
                        return category
        
        # If no keyword match, try direct category name matching
        for category in category_list:
            if category.name.upper() in description_upper:
                return category
        
        # Return default category if no match found
        return self._get_default_category(transaction_type, user_categories)

    def _get_default_category(self, transaction_type, user_categories):
        """Get or create a default category for transactions without clear mapping."""
        category_list = user_categories['income'] if transaction_type == 'INCOME' else user_categories['expense']
        
        if category_list:
            return category_list[0]
        
        # Create default category if user has none
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
        """Format transaction description from OFX data."""
        parts = []
        if ofx_transaction.payee:
            parts.append(ofx_transaction.payee)
        if ofx_transaction.memo and ofx_transaction.memo != ofx_transaction.payee:
            parts.append(ofx_transaction.memo)
        
        return ' - '.join(parts) if parts else 'Transação importada'


class ImportOFXPreviewView(LoginRequiredMixin, View):
    """
    Step 2: Preview transactions and confirm import.
    
    Allows user to review all transactions before importing and
    adjust category mappings if needed.
    """
    template_name = 'profiles/import_ofx_preview.html'

    def get(self, request):
        """Display preview of transactions to be imported."""
        # Get data from session
        import_data = request.session.get('ofx_import_data')
        
        if not import_data:
            messages.warning(request, 'Nenhum arquivo para visualizar. Por favor, faça upload primeiro.')
            return redirect('profiles:import_ofx')
        
        # Get account
        try:
            account = Account.objects.get(id=import_data['account_id'], user=request.user)
        except Account.DoesNotExist:
            messages.error(request, 'Conta não encontrada.')
            return redirect('profiles:import_ofx')
        
        # Create form with transaction data
        form = OFXPreviewConfirmForm(
            transactions_data=import_data['transactions'],
            user=request.user
        )
        
        # Prepare transactions with their form fields
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
        
        # Prepare context
        context = {
            'form': form,
            'account': account,
            'transactions_with_fields': transactions_with_fields,
            'total_transactions': len(import_data['transactions']),
            'skipped_count': import_data.get('skipped_count', 0),
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        """Process confirmed import with user-selected categories."""
        # Get data from session
        import_data = request.session.get('ofx_import_data')
        
        if not import_data:
            messages.warning(request, 'Sessão expirada. Por favor, faça upload novamente.')
            return redirect('profiles:import_ofx')
        
        # Get account
        try:
            account = Account.objects.get(id=import_data['account_id'], user=request.user)
        except Account.DoesNotExist:
            messages.error(request, 'Conta não encontrada.')
            return redirect('profiles:import_ofx')
        
        # Create form with posted data
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
                            # Get user-selected category
                            category = form.cleaned_data[f'category_{idx}']
                            
                            # Create transaction
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
                
                # Clear session data
                del request.session['ofx_import_data']
                
                # Show statistics
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
                
                return redirect('profiles:profile_detail')
                
            except Exception as e:
                messages.error(request, f'Erro ao importar transações: {str(e)}')
                return redirect('profiles:import_ofx')
        
        # If form invalid, show preview again
        context = {
            'form': form,
            'account': account,
            'transactions': import_data['transactions'],
            'total_transactions': len(import_data['transactions']),
            'skipped_count': import_data.get('skipped_count', 0),
        }
        return render(request, self.template_name, context)