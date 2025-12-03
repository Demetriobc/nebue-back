# 📊 Analytics App - Instalação

## 🚀 Passos para instalar:

### 1. Copiar o app para o projeto
```bash
# Copie a pasta 'analytics' para dentro do seu projeto nebue-sy/
cp -r analytics /caminho/do/seu/projeto/nebue-sy/
```

### 2. Adicionar ao INSTALLED_APPS
No arquivo `nebue-sy/settings.py`, adicione:

```python
INSTALLED_APPS = [
    # ... outros apps
    'analytics',  # ← ADICIONAR AQUI
]
```

### 3. Adicionar URLs
No arquivo `nebue-sy/urls.py`, adicione:

```python
urlpatterns = [
    # ... outras urls
    path('insights/', include('analytics.urls')),  # ← ADICIONAR AQUI
]
```

### 4. Instalar dependências
```bash
pip install python-dateutil --break-system-packages
```

### 5. Adicionar link no menu
No arquivo `templates/base.html`, dentro do navbar, adicione:

```html
<li><a href="{% url 'analytics:insights' %}">
    <i class="fas fa-chart-line"></i> Insights
</a></li>
```

### 6. Rodar o servidor
```bash
python manage.py runserver
```

### 7. Acessar
Acesse: `http://localhost:8000/insights/`

---

## 📁 Estrutura do app:

```
analytics/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── views.py           # View principal InsightsView
├── urls.py            # Rotas do app
├── utils.py           # Classe FinancialAnalytics com todas as funções
├── tests.py
└── templates/
    └── analytics/
        └── insights.html   # Template da página
```

---

## ✨ Funcionalidades:

- 📊 **Projeção de Gastos** (baseado nos últimos 3 meses)
- 💡 **Simulador "E se..."** (economia com investimento)
- ⚠️ **Alertas Inteligentes** (gastos acima da média)
- 📈 **Score de Saúde Financeira** (0-10)
- 🔥 **Streak de dias** (controle financeiro)
- 📅 **Comparação Mensal** (últimos 6 meses)
- 💰 **Recomendações de Economia** (por categoria)
- 📊 **Tendências por Categoria**

---

## 🎯 Pronto para usar!

Qualquer dúvida, me chama! 🚀
