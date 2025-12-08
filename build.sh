#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Criar pastas necessárias
mkdir -p staticfiles
mkdir -p media

python manage.py collectstatic --no-input --clear
python manage.py migrate