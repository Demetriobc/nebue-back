#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build do Nebue..."

# ========================================
# INSTALAÇÃO DE DEPENDÊNCIAS
# ========================================
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# ========================================
# CRIAÇÃO DE DIRETÓRIOS
# ========================================
echo "📁 Criando diretórios necessários..."
mkdir -p staticfiles
mkdir -p media

# ========================================
# COLETA DE ARQUIVOS ESTÁTICOS
# ========================================
echo "🎨 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input --clear

# ========================================
# MIGRAÇÕES DO BANCO DE DADOS
# ========================================
echo "🗄️  Aplicando migrações..."
python manage.py migrate --no-input

# ========================================
# POPULAÇÃO DE DADOS INICIAIS - GAMIFICAÇÃO
# ========================================
echo "🎮 Verificando sistema de gamificação..."

# Verifica se já existem níveis no banco
NIVEIS_COUNT=$(python manage.py shell -c "from gamification.models import NivelFinanceiro; print(NivelFinanceiro.objects.count())" 2>/dev/null || echo "0")

if [ "$NIVEIS_COUNT" -eq "0" ]; then
    echo "📊 Populando níveis financeiros..."
    python manage.py popular_gamificacao || echo "⚠️  Aviso: Erro ao popular gamificação (pode já existir)"
else
    echo "✅ Níveis já existem no banco (total: $NIVEIS_COUNT)"
    
    # Atualiza os níveis caso tenham mudanças
    echo "🔄 Atualizando níveis existentes..."
    python manage.py atualizar_niveis || echo "⚠️  Aviso: Comando atualizar_niveis não executado"
fi

# ========================================
# VERIFICAÇÃO FINAL
# ========================================
echo ""
echo "✅ Build concluído com sucesso!"
echo "📊 Estatísticas do sistema:"

python manage.py shell << EOF 2>/dev/null || true
from gamification.models import NivelFinanceiro, Conquista
from django.contrib.auth import get_user_model

User = get_user_model()

niveis = NivelFinanceiro.objects.count()
conquistas = Conquista.objects.count()
usuarios = User.objects.count()

print(f"   • Níveis cadastrados: {niveis}")
print(f"   • Conquistas cadastradas: {conquistas}")
print(f"   • Usuários no sistema: {usuarios}")
EOF

echo ""
echo "🎉 Sistema pronto para uso!"