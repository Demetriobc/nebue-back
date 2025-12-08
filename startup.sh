#!/usr/bin/env bash
set -o errexit
set -x  # Mostra cada comando executado

echo ""
echo "=========================================="
echo "🚀 STARTUP NEBUE - INÍCIO"
echo "=========================================="
date
echo ""

# ========================================
# INFORMAÇÕES DO AMBIENTE
# ========================================
echo "📊 Informações do ambiente:"
echo "   • Python: $(python --version)"
echo "   • Django: $(python -c 'import django; print(django.get_version())')"
echo "   • Diretório: $(pwd)"
echo "   • Usuário: $(whoami)"
echo ""

# ========================================
# VERIFICAÇÃO DE VARIÁVEIS
# ========================================
echo "🔐 Variáveis de ambiente:"
echo "   • DATABASE_URL: ${DATABASE_URL:0:30}... (truncado)"
echo "   • DEBUG: ${DEBUG:-não definido}"
echo "   • ALLOWED_HOSTS: ${ALLOWED_HOSTS:-não definido}"
echo ""

# ========================================
# AGUARDA POSTGRES ESTAR PRONTO
# ========================================
echo "⏳ [1/6] Aguardando conexão com banco de dados..."

MAX_RETRIES=30
RETRY_COUNT=0

until python manage.py check --database default > /dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   ⏱️  Tentativa $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ ERRO FATAL: Não foi possível conectar ao banco de dados após $MAX_RETRIES tentativas!"
    echo "🔍 Tentando diagnóstico..."
    python manage.py check --database default || true
    exit 1
fi

echo "✅ Conexão com banco estabelecida após $RETRY_COUNT tentativas!"
echo ""

# ========================================
# SHOWMIGRATIONS (DIAGNÓSTICO)
# ========================================
echo "🔍 [2/6] Verificando status das migrations..."
python manage.py showmigrations || echo "⚠️ Erro ao mostrar migrations"
echo ""

# ========================================
# MIGRAÇÕES DO BANCO DE DADOS
# ========================================
echo "🗄️ [3/6] Aplicando migrações do banco de dados..."
python manage.py migrate --no-input --verbosity 2
echo "✅ Migrações aplicadas com sucesso!"
echo ""

# ========================================
# POPULAÇÃO DE GAMIFICAÇÃO
# ========================================
echo "🎮 [4/6] Configurando sistema de gamificação..."

echo "   🔍 Verificando níveis existentes..."
NIVEIS_COUNT=$(python manage.py shell -c "
from gamification.models import NivelFinanceiro
print(NivelFinanceiro.objects.count())
" 2>&1 | tail -n 1)

echo "   📊 Níveis encontrados: $NIVEIS_COUNT"

if [ "$NIVEIS_COUNT" = "0" ] || [ -z "$NIVEIS_COUNT" ]; then
    echo "   📊 Populando gamificação pela primeira vez..."
    python manage.py popular_gamificacao 2>&1 || echo "   ⚠️ Erro ao popular (continuando...)"
else
    echo "   ✅ Gamificação já populada ($NIVEIS_COUNT níveis)"
    echo "   🔄 Tentando atualizar níveis..."
    python manage.py atualizar_niveis 2>&1 || echo "   ℹ️ Comando atualizar_niveis não executado"
fi
echo ""

# ========================================
# ESTATÍSTICAS DO SISTEMA
# ========================================
echo "📊 [5/6] Coletando estatísticas do sistema..."

python manage.py shell << 'PYEOF' 2>&1 || echo "⚠️ Não foi possível coletar estatísticas"
from gamification.models import NivelFinanceiro, Conquista
from django.contrib.auth import get_user_model

try:
    User = get_user_model()
    niveis = NivelFinanceiro.objects.count()
    conquistas = Conquista.objects.count()
    usuarios = User.objects.count()
    
    print(f"   • Níveis: {niveis}")
    print(f"   • Conquistas: {conquistas}")
    print(f"   • Usuários: {usuarios}")
except Exception as e:
    print(f"   ⚠️ Erro: {e}")
PYEOF

echo ""

# ========================================
# COLLECTSTATIC (FALLBACK)
# ========================================
echo "🎨 [6/6] Verificando arquivos estáticos (fallback)..."
python manage.py collectstatic --no-input --clear > /dev/null 2>&1 && echo "✅ Collectstatic OK" || echo "ℹ️ Collectstatic já executado no build"
echo ""

# ========================================
# VERIFICAÇÃO FINAL ANTES DE INICIAR
# ========================================
echo "🔍 Verificação final do sistema..."
python manage.py check || echo "⚠️ Avisos encontrados"
echo ""

# ========================================
# INICIALIZAÇÃO CONCLUÍDA
# ========================================
echo "=========================================="
echo "🎉 STARTUP CONCLUÍDO COM SUCESSO!"
echo "=========================================="
date
echo ""
echo "🌐 Iniciando servidor Gunicorn..."
echo "   • Workers: ${WEB_CONCURRENCY:-2}"
echo "   • Threads: ${PYTHON_MAX_THREADS:-4}"
echo "   • Port: ${PORT:-8080}"
echo "=========================================="
echo ""

# ========================================
# INICIA O SERVIDOR GUNICORN
# ========================================
exec gunicorn core.wsgi \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers ${WEB_CONCURRENCY:-2} \
    --threads ${PYTHON_MAX_THREADS:-4} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug \
    --capture-output \
    --enable-stdio-inheritance