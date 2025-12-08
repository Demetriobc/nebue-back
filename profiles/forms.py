from django import forms

from accounts.models import Account
from categories.models import Category
from .models import Profile


class ProfileForm(forms.ModelForm):
    """Form for updating user profile information."""
    
    class Meta:
        model = Profile
        fields = ['full_name', 'phone']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all',
                'placeholder': 'Seu nome completo'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all',
                'placeholder': '(11) 98765-4321'
            }),
        }


class OFXImportForm(forms.Form):
    """
    Form for importing OFX/OFC bank statement files.
    
    Allows users to upload their bank statement files and select
    which account the transactions should be imported into.
    """
    
    ofx_file = forms.FileField(
        label='Arquivo OFX/OFC',
        help_text='Arquivo de extrato bancário em formato OFX ou OFC',
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'id': 'ofx-file-input',
            'accept': '.ofx,.OFX,.ofc,.OFC',
        })
    )
    
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),  # Will be set in __init__
        label='Conta de Destino',
        help_text='Selecione a conta onde as transações serão importadas',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all'
        })
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize form and filter accounts by user.
        
        Args:
            user: The current logged-in user (required)
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter accounts to show only user's accounts
            self.fields['account'].queryset = Account.objects.filter(
                user=user
            ).order_by('name')
    
    def clean_ofx_file(self):
        """
        Validate that the uploaded file is in OFX/OFC format.
        
        Returns:
            File: The validated file object
            
        Raises:
            ValidationError: If file extension is not .ofx or .ofc
        """
        ofx_file = self.cleaned_data.get('ofx_file')
        
        if ofx_file:
            # Check file extension
            file_name = ofx_file.name.lower()
            if not (file_name.endswith('.ofx') or file_name.endswith('.ofc')):
                raise forms.ValidationError(
                    'Arquivo inválido. Por favor, envie um arquivo .OFX ou .OFC'
                )
            
            # Check file size (max 5MB)
            if ofx_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    'Arquivo muito grande. O tamanho máximo é 5MB.'
                )
        
        return ofx_file


class OFXPreviewConfirmForm(forms.Form):
    """
    Form for confirming OFX import after preview.
    
    Allows users to review and modify category mappings before final import.
    Each transaction can have its category changed by the user.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Dynamically create category selection fields for each transaction.
        
        Args:
            transactions_data: List of parsed transaction dictionaries
            user: Current user (for filtering categories)
        """
        transactions_data = kwargs.pop('transactions_data', [])
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Get user categories grouped by type
            income_categories = Category.objects.filter(
                user=user, 
                category_type=Category.CategoryType.INCOME
            )
            expense_categories = Category.objects.filter(
                user=user, 
                category_type=Category.CategoryType.EXPENSE
            )
            
            # Create a field for each transaction
            for idx, trans_data in enumerate(transactions_data):
                # Select appropriate categories based on transaction type
                categories = income_categories if trans_data['type'] == 'INCOME' else expense_categories
                
                self.fields[f'category_{idx}'] = forms.ModelChoiceField(
                    queryset=categories,
                    initial=trans_data.get('category'),
                    label=f'Categoria',
                    widget=forms.Select(attrs={
                        'class': 'px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all'
                    })
                )
                
                # Store transaction data as hidden fields
                self.fields[f'date_{idx}'] = forms.CharField(
                    initial=trans_data['date'],
                    widget=forms.HiddenInput()
                )
                self.fields[f'description_{idx}'] = forms.CharField(
                    initial=trans_data['description'],
                    widget=forms.HiddenInput()
                )
                self.fields[f'amount_{idx}'] = forms.CharField(
                    initial=str(trans_data['amount']),
                    widget=forms.HiddenInput()
                )
                self.fields[f'type_{idx}'] = forms.CharField(
                    initial=trans_data['type'],
                    widget=forms.HiddenInput()
                )