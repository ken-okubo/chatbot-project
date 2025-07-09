# Chatbot Inteligente para Atendimento via WhatsApp e Dashboard Web

Este projeto entrega um sistema completo de chatbot com backend em FastAPI, frontend em Streamlit e integração via WhatsApp Web. O objetivo foi construir uma solução robusta, personalizável e com análise de sentimento por inteligência artificial (OpenAI), pensada inicialmente para um projeto acadêmico, mas aplicável a diversos tipos de negócio.

---

## 🧠 Funcionalidades Principais / Main Features

- Classificação de mensagens e respostas automáticas via OpenAI
- Identificação do tipo de negócio pela conversa
- Análise de sentimento com retorno de `sentiment` e `score`
- Histórico de conversas com visualização no dashboard
- Integração com WhatsApp Web (via `venom-bot`)
- Dashboard administrativo com Streamlit

---

## 🗂 Estrutura do Projeto / Project Structure

```
chatbot/
├── app/                  # Backend FastAPI
│   ├── core/
│   ├── db/
│   ├── api/
│   ├── main.py
├── whatsapp/             # Integração com WhatsApp Web
│   ├── client.js
│   ├── api.js
│   └── index.js
├── frontend/        # Dashboard
│   └── dashboard.py
├── Dockerfile
├── docker-compose.yml
├── .env
├── README.md
```

---

## ⚙️ Como rodar o projeto localmente / Running Locally

### 1. Clonar o repositório / Clone the repository

```bash
git clone https://github.com/ken-okubo/chatbot-project
cd chatbot-projeto
```

### 2. Variáveis de ambiente / Environment variables

Crie um arquivo `.env` com o seguinte conteúdo:

```
OPENAI_API_KEY=sk-...
BACKEND_API_URL=http://localhost:8000/webhook
```

> 🔒 Nunca exponha sua chave da OpenAI em repositórios públicos.

---

### 3. Rodar com Docker / Run with Docker

```bash
docker-compose up --build
```

- A API estará disponível em: `http://localhost:8000`
- O painel estará em: `http://localhost:8501`
- O servidor WhatsApp estará em: `http://localhost:3001`

### Para criação do bando de dados

Com o container levantado, em um novo terminal em paralelo:
`docker compose exec app python`

Em seguida, o seguinte comando para criação do banco de dados:

```
from app.db.session import engine
from app.db import models
models.Base.metadata.create_all(bind=engine)
```

---

## 📱 Integração com WhatsApp via Venom / WhatsApp Integration (venom-bot)

Na pasta raíz do projeto, rode:

`npm install`
`npm audit fix --force`

A integração utiliza [venom-bot](https://github.com/orkestral/venom), que permite criar bots no WhatsApp Web de forma simples e robusta.

- Ao rodar o projeto, será gerado um QR code no terminal.
- Escaneie com o WhatsApp (de preferência um número secundário).
- O bot responderá automaticamente com base na API FastAPI.

> ⚠️ Recomenda-se o uso de um número descartável para testes, pois a conta pode ser bloqueada pelo WhatsApp.

---

### 📊 Rodando o Dashboard com Streamlit

Para rodar o dashboard localmente:

````bash
cd frontend
streamlit run dashboard.py

- Histórico de conversas
- Sentimentos por conversa
- Filtros por status, cliente, tipo de negócio, etc.

---

## 🧪 Testes manuais com cURL / Manual tests

```bash
curl -X POST http://localhost:8000/webhook   -H "Content-Type: application/json"   -d '{"user_number": "+551199999999", "message": "Quais sabores de pizza vocês têm?"}'
````

---

## ✍️ Observações

- O sistema está pronto para deploy (Railway, Render ou servidor próprio).
- A análise de sentimento é feita diretamente pelo ChatGPT (modelo gpt-3.5 ou superior).
- O projeto pode ser adaptado facilmente para outros setores além de delivery.

---

## 📁 .gitignore sugerido

```
.env
__pycache__/
*.pyc
venv/
output/
node_modules/
.whatsapp-session/
```

---

## 📌 Melhorias Futuras / Future Improvements

- Autenticação JWT no dashboard
- Treinamento de modelo local
- Integração com outras plataformas além do WhatsApp
