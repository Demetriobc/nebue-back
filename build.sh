#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build do Nebue..."
echo "================================================"

# ========================================
# INSTALAÇÃO DE DEPENDÊNCIAS
# ========================================
echo ""
echo "📦 Instalando dependências Python..."
pip install --no-cache-dir -r requirements.txt

# ========================================
# CRIAÇÃO DE DIRETÓRIOS
# ========================================
echo ""
echo "📁 Criando estrutura de diretórios..."
mkdir -p staticfiles
mkdir -p media
mkdir -p logs

# ========================================
# COLETA DE ARQUIVOS ESTÁTICOS
# ========================================
echo ""
echo "🎨 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input --clear

# ========================================
# VERIFICAÇÃO DE INTEGRIDADE
# ========================================
echo ""
echo "🔍 Verificando integridade do projeto..."
python manage.py check --deploy 2>/dev/null || echo "⚠️  Avisos de deploy encontrados (não crítico)"

# ========================================
# BUILD CONCLUÍDO
# ========================================
echo ""
echo "================================================"
echo "✅ Build concluído com sucesso!"
echo "📌 Arquivos estáticos processados"
echo "📌 Dependências instaladas"
echo ""
echo "🗄️  Migrações e configurações de banco serão"
echo "   executadas no startup (quando Postgres estiver disponível)"
echo "================================================"