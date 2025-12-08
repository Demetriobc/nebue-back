#!/usr/bin/env bash
set -o errexit

echo ""
echo "🚀 Iniciando aplicação Nebue..."
echo "================================================"

# ========================================
# AGUARDA POSTGRES ESTAR PRONTO
# ========================================
echo ""
echo "⏳ Aguardando conexão com banco de dados..."

MAX_RETRIES=30
RETRY_COUNT=0

until python manage.py check --database default > /dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   Tentativa $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ ERRO: Não foi possível conectar ao banco de dados!"
    exit 1
fi

echo "✅ Conexão com banco estabelecida!"

# ========================================
# MIGRAÇÕES DO BANCO DE DADOS
# ========================================
echo ""
echo "🗄️  Aplicando migrações do banco de dados..."
python manage.py migrate --no-input

# ========================================
# POPULAÇÃO DE GAMIFICAÇÃO (IDEMPOTENTE)
# ========================================
echo ""
echo "🎮 Configurando sistema de gamificação..."

# Verifica quantos níveis existem
NIVEIS_COUNT=$(python manage.py shell -c "
from gamification.models import NivelFinanceiro
print(NivelFinanceiro.objects.count())
" 2>/dev/null || echo "0")

echo "   • Níveis existentes: $NIVEIS_COUNT"

# Se não tem níveis, popula tudo
if [ "$NIVEIS_COUNT" -eq "0" ]; then
    echo "   📊 Populando níveis e conquistas pela primeira vez..."
    python manage.py popular_gamificacao 2>&1 || echo "   ⚠️  Aviso: Erro ao popular (pode já existir)"
else
    echo "   ✅ Níveis já existem no banco"
    
    # Tenta atualizar níveis existentes
    echo "   🔄 Atualizando níveis com possíveis mudanças..."
    python manage.py atualizar_niveis 2>&1 || echo "   ℹ️  Comando atualizar_niveis não disponível"
fi

# ========================================
# ESTATÍSTICAS DO SISTEMA
# ========================================
echo ""
echo "📊 Estatísticas do sistema:"

python manage.py shell << 'PYEOF' 2>/dev/null || echo "   ⚠️  Não foi possível coletar estatísticas"
from gamification.models import NivelFinanceiro, Conquista
from django.contrib.auth import get_user_model

try:
    User = get_user_model()
    niveis = NivelFinanceiro.objects.count()
    conquistas = Conquista.objects.count()
    usuarios = User.objects.count()
    
    print(f"   • Níveis cadastrados: {niveis}")
    print(f"   • Conquistas cadastradas: {conquistas}")
    print(f"   • Usuários no sistema: {usuarios}")
except Exception as e:
    print(f"   ⚠️  Erro ao coletar stats: {e}")
PYEOF

# ========================================
# COLETA DE ARQUIVOS ESTÁTICOS (FALLBACK)
# ========================================
echo ""
echo "🎨 Verificando arquivos estáticos..."
python manage.py collectstatic --no-input --clear > /dev/null 2>&1 || echo "   ℹ️  Arquivos estáticos já processados no build"

# ========================================
# INICIALIZAÇÃO CONCLUÍDA
# ========================================
echo ""
echo "================================================"
echo "🎉 Inicialização concluída com sucesso!"
echo "🌐 Servidor Gunicorn iniciando..."
echo "================================================"
echo ""

# ========================================
# INICIA O SERVIDOR GUNICORN
# ========================================
exec gunicorn core.wsgi \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers ${WEB_CONCURRENCY:-2} \
    --threads ${PYTHON_MAX_THREADS:-4} \
    --timeout 120 \
    -