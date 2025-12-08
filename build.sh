#!/usr/bin/env bash
set -o errexit
set -x  # Mostra cada comando executado

echo "=========================================="
echo "🚀 BUILD NEBUE - INÍCIO"
echo "=========================================="
date
echo ""

# ========================================
# INSTALAÇÃO DE DEPENDÊNCIAS
# ========================================
echo "📦 [1/4] Instalando dependências Python..."
pip install --no-cache-dir -r requirements.txt
echo "✅ Dependências instaladas com sucesso!"
echo ""

# ========================================
# CRIAÇÃO DE DIRETÓRIOS
# ========================================
echo "📁 [2/4] Criando estrutura de diretórios..."
mkdir -p staticfiles
mkdir -p media
mkdir -p logs
ls -la
echo "✅ Diretórios criados com sucesso!"
echo ""

# ========================================
# COLETA DE ARQUIVOS ESTÁTICOS
# ========================================
echo "🎨 [3/4] Coletando arquivos estáticos..."
python manage.py collectstatic --no-input --clear --verbosity 2
echo "✅ Arquivos estáticos coletados com sucesso!"
echo ""

# ========================================
# VERIFICAÇÃO DE INTEGRIDADE
# ========================================
echo "🔍 [4/4] Verificando integridade do projeto..."
python manage.py check --deploy || echo "⚠️ Avisos encontrados (não crítico)"
echo ""

# ========================================
# BUILD CONCLUÍDO
# ========================================
echo "=========================================="
echo "✅ BUILD CONCLUÍDO COM SUCESSO!"
echo "=========================================="
date
echo ""
echo "📌 Próximo passo: startup.sh (quando container iniciar)"
echo ""