# Totem-CEM

# Como executar:

# 1️⃣ Configurando o Backend (API)

## Acesse a pasta do backend e prepare o ambiente Python:

## Entre na pasta
```bash
cd backend
```

## Crie um ambiente virtual
```bash
python3 -m venv venv
```

## Ative o ambiente virtual (Linux/Mac)
```bash
source .venv/bin/activate
```
## Ou (Windows)
```bash
.venv\Scripts\activate
```

## Inicie um projeto com FastAPI
```bash
pip install fastapi uvicorn
```

## 🔐 Variáveis de Ambiente (.env)

Crie um arquivo chamado .env na raiz da pasta backend e configure as credenciais de acesso:

```bash
SISREG_USUARIO=seu_usuario_sisreg
SISREG_SENHA=sua_senha_sisreg
```

## Rodando o Servidor:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

# 2️⃣ Configuração do Frontend (Interface)

Em um novo terminal, acesse a pasta do frontend:

## Entre na pasta frontend
```bash
cd frontend
```

## Crie um projeto React
```bash
npx create-react-app .
```

## 🔗 Conexão com a API (.env)

Crie um arquivo .env na raiz da pasta frontend para apontar para o seu backend local:

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

# Iniciando a Aplicação:

## Inicie o servidor de desenvolvimento
npm start

## ✅ O Frontend estará rodando em: http://localhost:3000
