#!/usr/bin/env bash
# ============================================
# 🚀 NEBUE STARTUP - ROBUSTO E DEFINITIVO
# ============================================
set -e  # Para em qualquer erro
set -x  # Mostra comandos sendo executados

echo "=============================================="
echo "🚀 NEBUE STARTUP - INÍCIO"
echo "=============================================="
date
echo ""

# ============================================
# INFORMAÇÕES DO AMBIENTE
# ============================================
echo "📊 Informações do Ambiente:"
echo "   Python: $(python --version)"
echo "   Django: $(python -c 'import django; print(django.get_version())')"
echo "   DATABASE_URL: ${DATABASE_URL:0:50}..."
echo ""

# ============================================
# AGUARDA POSTGRES FICAR DISPONÍVEL
# ============================================
echo "⏳ Aguardando PostgreSQL ficar disponível..."

MAX_RETRIES=60
RETRY_COUNT=0
WAIT_TIME=2

while ! python manage.py check --database default > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ ERRO: PostgreSQL não conectou após $MAX_RETRIES tentativas!"
        echo "❌ Verifique a variável DATABASE_URL e o serviço PostgreSQL no Railway"
        exit 1
    fi
    
    echo "   ⏱️  Tentativa $RETRY_COUNT/$MAX_RETRIES... (aguardando ${WAIT_TIME}s)"
    sleep $WAIT_TIME
done

echo "✅ PostgreSQL conectado com sucesso!"
echo ""

# ============================================
# APLICA MIGRATIONS
# ============================================
echo "📊 Aplicando migrations do banco de dados..."

# Mostra quais migrations existem
python manage.py showmigrations

# Aplica migrations com verbose para ver o progresso
python manage.py migrate --no-input --verbosity 2

if [ $? -eq 0 ]; then
    echo "✅ Migrations aplicadas com sucesso!"
else
    echo "❌ ERRO ao aplicar migrations!"
    exit 1
fi
echo ""

# ============================================
# COLETA ARQUIVOS ESTÁTICOS
# ============================================
echo "📦 Coletando arquivos estáticos..."

python manage.py collectstatic --no-input --clear

if [ $? -eq 0 ]; then
    echo "✅ Arquivos estáticos coletados!"
else
    echo "⚠️  Erro ao coletar estáticos (continuando...)"
fi
echo ""

# ============================================
# POPULA GAMIFICAÇÃO (SE NECESSÁRIO)
# ============================================
echo "🎮 Verificando gamificação..."

# Conta níveis de forma mais robusta
NIVEIS_COUNT=$(python manage.py shell <<EOF 2>&1 | grep -o '[0-9]\+' | tail -1
from gamification.models import NivelFinanceiro
print(NivelFinanceiro.objects.count())
EOF
)

echo "   Níveis encontrados: $NIVEIS_COUNT"

if [ "$NIVEIS_COUNT" = "0" ] || [ -z "$NIVEIS_COUNT" ]; then
    echo "   📝 Populando sistema de gamificação..."
    python manage.py popular_gamificacao 2>&1
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Gamificação populada!"
    else
        echo "   ⚠️  Erro ao popular gamificação (continuando...)"
    fi
else
    echo "   ✅ Gamificação já populada ($NIVEIS_COUNT níveis)"
    
    # Tenta atualizar níveis (não crítico)
    python manage.py atualizar_niveis 2>&1 || echo "   ⚠️  Comando atualizar_niveis não disponível"
fi
echo ""

# ============================================
# VERIFICA INTEGRIDADE DOS APPS
# ============================================
echo "🔍 Verificando integridade dos apps..."

python manage.py shell <<'PYEOF'
import sys
from django.contrib.auth import get_user_model

try:
    # Imports dos models
    from gamification.models import NivelFinanceiro, Conquista, PerfilGamificacao
    from notifications.models import Notification
    from transactions.models import Transaction
    from accounts.models import Account
    
    User = get_user_model()
    
    # Estatísticas
    print(f"✅ Usuários: {User.objects.count()}")
    print(f"✅ Níveis: {NivelFinanceiro.objects.count()}")
    print(f"✅ Conquistas: {Conquista.objects.count()}")
    print(f"✅ Notificações: {Notification.objects.count()}")
    print(f"✅ Contas: {Account.objects.count()}")
    print(f"✅ Transações: {Transaction.objects.count()}")
    
    # Garante que todos os usuários têm perfil de gamificação
    users_without_profile = 0
    for user in User.objects.all():
        perfil, created = PerfilGamificacao.objects.get_or_create(
            user=user,
            defaults={'pontos': 0}
        )
        if created:
            users_without_profile += 1
            print(f"⚠️  Criado perfil de gamificação para {user.email}")
    
    if users_without_profile > 0:
        print(f"⚠️  {users_without_profile} perfis de gamificação criados")
    
    print("✅ TODOS OS APPS ESTÃO OK!")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ ERRO ao testar apps: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ Erro na verificação dos apps!"
    echo "❌ Sistema não está pronto para iniciar"
    exit 1
fi
echo ""

# ============================================
# RESUMO ANTES DE INICIAR
# ============================================
echo "=============================================="
echo "📋 RESUMO PRÉ-INICIALIZAÇÃO:"
echo "=============================================="
echo "✅ PostgreSQL: Conectado"
echo "✅ Migrations: Aplicadas"
echo "✅ Arquivos estáticos: Coletados"
echo "✅ Gamificação: Configurada"
echo "✅ Apps: Verificados e OK"
echo "=============================================="
echo ""

# ============================================
# INICIA GUNICORN
# ============================================
echo "🚀 Iniciando Gunicorn..."
echo "   Workers: ${WEB_CONCURRENCY:-2}"
echo "   Threads por worker: ${PYTHON_MAX_THREADS:-4}"
echo "   Porta: ${PORT:-8080}"
echo "   Timeout: 120s"
echo ""

exec gunicorn core.wsgi \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers ${WEB_CONCURRENCY:-2} \
    --threads ${PYTHON_MAX_THREADS:-4} \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --preload