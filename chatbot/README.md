# 🤖 Chatbot Financeiro IA - Nebue

Assistente financeiro inteligente integrado ao sistema Nebue, powered by Claude AI.

## 🚀 Instalação

### 1. Copiar o app para o projeto
```bash
cp -r chatbot /caminho/do/seu/projeto/nebue-sy/
```

### 2. Adicionar ao INSTALLED_APPS
No arquivo `nebue-sy/settings.py`:

```python
INSTALLED_APPS = [
    # ... outros apps
    'chatbot',  # ← ADICIONAR AQUI
]
```

### 3. Adicionar URLs
No arquivo `nebue-sy/urls.py`:

```python
urlpatterns = [
    # ... outras urls
    path('chat/', include('chatbot.urls')),  # ← ADICIONAR AQUI
]
```

### 4. Rodar Migrations
```bash
python manage.py makemigrations chatbot
python manage.py migrate
```

### 5. Adicionar link no menu
No `templates/base.html`, adicione no navbar:

```html
<li><a href="{% url 'chatbot:chat' %}">
    <i class="fas fa-comments"></i> Assistente IA
</a></li>
```

### 6. Testar
Acesse: `http://localhost:8000/chat/`

---

## ✨ Funcionalidades

### O que o bot faz:

✅ **Responde perguntas:**
- "Quanto gastei este mês?"
- "Qual meu saldo total?"
- "Quais categorias gastei mais?"
- "Me dê dicas para economizar"

✅ **Dá insights personalizados:**
- Análise de gastos
- Comparações com meses anteriores
- Recomendações baseadas em "Pai Rico Pai Pobre"

✅ **Tem contexto financeiro:**
- Acessa seus dados reais
- Lembra da conversa
- Responde com base no seu perfil

✅ **Interface moderna:**
- Chat em tempo real
- Botões de ação rápida
- Design responsivo

---

## 🎨 Interface

### Tela Principal
- Chat estilo WhatsApp/ChatGPT
- Mensagens do usuário (roxo)
- Respostas do assistente (cinza)
- Botões de ações rápidas

### Recursos
- ✅ Scroll automático
- ✅ Enter para enviar
- ✅ Shift+Enter para quebra de linha
- ✅ Indicador de "digitando..."
- ✅ Histórico de conversas

---

## 🔧 Personalização

### Mudar personalidade do bot
Edite `chatbot/ai_assistant.py` na função `get_system_prompt()`.

### Adicionar comandos
Edite `chatbot/ai_assistant.py` na função `execute_command()`.

### Mudar modelo da IA
Em `ai_assistant.py`, linha do modelo:
```python
"model": "claude-sonnet-4-20250514"  # ← Trocar aqui
```

---

## 💡 Exemplos de uso

### Perguntas básicas:
- "Qual meu saldo?"
- "Quanto gastei em alimentação?"
- "Estou gastando muito?"

### Análises:
- "Compare meus gastos com o mês passado"
- "Quais categorias devo reduzir?"
- "Me mostre um resumo financeiro"

### Dicas:
- "Como posso economizar?"
- "Me dê uma dica de educação financeira"
- "Qual minha meta de economia ideal?"

---

## 🛠️ Tecnologias

- **Django** - Framework web
- **Claude AI** - Inteligência artificial
- **Tailwind CSS** - Estilização
- **JavaScript** - Interatividade
- **PostgreSQL/SQLite** - Banco de dados

---

## 📊 Estrutura de Dados

### Conversation
- Agrupa mensagens do usuário
- Histórico de conversas
- Título automático

### Message
- Tipo: USER, ASSISTANT, SYSTEM
- Conteúdo da mensagem
- Timestamp
- Metadados (JSON)

---

## 🔐 Segurança

- ✅ Login obrigatório (LoginRequiredMixin)
- ✅ Dados isolados por usuário
- ✅ CSRF protection
- ✅ Sanitização de entrada
- ✅ Rate limiting recomendado (adicionar)

---

## 🚀 Próximos Passos

### Melhorias futuras:
- [ ] Comandos por voz
- [ ] Anexar imagens/PDFs
- [ ] Exportar conversas
- [ ] Análises com gráficos no chat
- [ ] Notificações push
- [ ] WhatsApp integration

---

## 📞 Suporte

Dúvidas? Entre em contato ou abra uma issue!

**Desenvolvido com ❤️ para o Nebue**
