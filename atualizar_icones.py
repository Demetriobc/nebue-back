"""
Script para atualizar ícones dos níveis
Salve como: atualizar_icones.py (na raiz do projeto)
Execute: python atualizar_icones.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from gamification.models import NivelFinanceiro

# Mapeamento dos ícones
icones = {
    1: ('fa-seedling', '#10b981', 'Iniciante'),
    2: ('fa-book-open', '#3b82f6', 'Aprendiz'),
    3: ('fa-clipboard-list', '#8b5cf6', 'Organizador'),
    4: ('fa-chart-line', '#06b6d4', 'Disciplinado'),
    5: ('fa-piggy-bank', '#ec4899', 'Poupador'),
    6: ('fa-balance-scale', '#14b8a6', 'Equilibrado'),
    7: ('fa-trophy', '#f59e0b', 'Campeão'),
    8: ('fa-graduation-cap', '#a855f7', 'Expert'),
    9: ('fa-shield-alt', '#ef4444', 'Guardião'),
    10: ('fa-crown', '#fbbf24', 'Mestre'),
}

print('\n' + '='*60)
print('🎨 ATUALIZANDO ÍCONES DOS NÍVEIS')
print('='*60 + '\n')

atualizados = 0

for numero, (icone, cor, nome_sugerido) in icones.items():
    try:
        nivel = NivelFinanceiro.objects.get(numero=numero)
        nivel.icone = icone
        nivel.cor = cor
        nivel.save()
        
        print(f'✅ Nível {numero:2d} - {nivel.nome:20s} → {icone:20s} | {cor}')
        atualizados += 1
        
    except NivelFinanceiro.DoesNotExist:
        print(f'❌ Nível {numero} não encontrado no banco')

print('\n' + '='*60)
print(f'🎉 {atualizados} níveis atualizados com sucesso!')
print('='*60 + '\n')

# Verificar os dados
print('📊 VERIFICAÇÃO FINAL:')
print('-'*60)
for nivel in NivelFinanceiro.objects.all().order_by('numero'):
    print(f'Nível {nivel.numero} - {nivel.nome:20s} | {nivel.icone:20s} | {nivel.cor}')
print('-'*60 + '\n')