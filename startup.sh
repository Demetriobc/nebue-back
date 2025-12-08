#!/usr/bin/env bash
set -o errexit
set -x

echo "🚀 STARTUP NEBUE - INÍCIO"
date

# Informações ambiente
echo "📊 Python: $(python --version)"
echo "🔐 DATABASE_URL: ${DATABASE_URL:0:30}..."

# Aguarda Postgres
MAX_RETRIES=30
RETRY_COUNT=0
until python manage.py check --database default > /dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "⏱️ Tentativa $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ ERRO: Postgres não conectou!"
    exit 1
fi

# Migrations
python manage.py showmigrations
python manage.py migrate --no-input --verbosity 2

# População de gamificação
NIVEIS_COUNT=$(python manage.py shell -c "
from gamification.models import NivelFinanceiro
print(NivelFinanceiro.objects.count())
" 2>&1 | tail -n 1)

if [ "$NIVEIS_COUNT" = "0" ]; then
    python manage.py popular_gamificacao 2>&1
else
    echo "✅ Gamificação já populada ($NIVEIS_COUNT níveis)"
    python manage.py atualizar_niveis 2>&1 || true
fi

# ============================================
# 🔍 TESTE DE INTEGRIDADE DOS APPS
# ============================================
echo "🔍 Testando integridade dos apps..."

python manage.py shell << 'PYEOF'
import sys
from django.contrib.auth import get_user_model

try:
    # Testa imports
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
    
    # Testa se todo usuário tem perfil de gamificação
    for user in User.objects.all():
        perfil, created = PerfilGamificacao.objects.get_or_create(
            user=user,
            defaults={'pontos': 0}
        )
        if created:
            print(f"⚠️ Criado perfil de gamificação para {user.email}")
    
    print("✅ TODOS OS APPS ESTÃO OK!")
    
except Exception as e:
    print(f"❌ ERRO ao testar apps: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ Erro na verificação dos apps! Abortando..."
    exit 1
fi

# ============================================
# 🚀 INICIA GUNICORN
# ============================================
echo "✅ Tudo pronto! Iniciando Gunicorn..."

exec gunicorn core.wsgi \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers ${WEB_CONCURRENCY:-2} \
    --threads ${PYTHON_MAX_THREADS:-4} \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output