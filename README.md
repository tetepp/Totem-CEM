# Totem CEM — Atualiza SUS

Totem de autoatendimento para verificação cadastral do SUS, desenvolvido para a
Centro de Especialidades Médicas de Três Lagoas/MS.

O cidadão informa **CPF** + **Captcha** + **primeiro nome da mãe**, consulta os dados vindos
da base do **SISREG** e confirma se o cadastro está
correto ou precisa de atualização. Ao clicar em **"Preciso atualizar"**, o
sistema envia **e-mail automático** com nome, CPF e data/hora do clique.

---

## Arquitetura

```
Navegador → FastAPI (uvicorn :8000) → SISREG 
                ↓
        PostgreSQL (respostas_cadastro)
        SMTP (e-mail CEM: cemtl.cadastro@gmail.com)
```

O **FastAPI serve tanto a API quanto o React buildado** na mesma porta (8000).
Não é necessário rodar `npm start` em produção.

---

## Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| Git | 2.30+ |

**Instalação (Ubuntu 22.04/24.04):**

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-full \
                    nodejs npm postgresql postgresql-contrib git
```

---

## Instalação

### 1) Clonar o repositório

```bash
cd /opt
git clone https://github.com/tetepp/Totem-CEM.git
cd Totem-CEM
```

### 2) Configurar o PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE USER totem_user WITH PASSWORD 'senha_forte_aqui';
CREATE DATABASE totem_sus OWNER totem_user;
GRANT ALL PRIVILEGES ON DATABASE totem_sus TO totem_user;
\q
```

> A tabela `respostas_cadastro` é criada automaticamente no primeiro boot do backend.

### 3) Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Crie o arquivo **`backend/.env`**:

```env
# Banco de dados
DATABASE_URL=postgresql+asyncpg://totem_user:senha_forte_aqui@localhost:5432/totem_sus

# SISREG 
SISREG_USUARIO=
SISREG_SENHA=
SISREG_URL_AMBULATORIAL=
SISREG_URL_MARCACAO=
SISREG_URL_HOSPITALAR=
SISREG_CODIGO_MUNICIPIO=
VERIFY_SSL=

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=cemtl.cadastro@gmail.com
SMTP_PASSWORD=senha_de_app_16_caracteres
EMAIL_DESTINO=cemtl.cadastro@gmail.com

```

Testar o backend:

```bash
uvicorn main:app --reload --port 8000
```

Saída esperada: `[BOOT] Banco de dados inicializado` + `Application startup complete`.

> Se aparecer `RuntimeError: Build do frontend não encontrado`, é esperado no
> primeiro boot. Siga para o passo 4.

### 4) Frontend

```bash
cd ../frontend
npm install
```

Crie o arquivo **`frontend/.env`**:

```env
REACT_APP_API_BASE_URL=/api
```

> ⚠️ Use `/api` (relativo), **não** `http://localhost:8000/api`. Como o FastAPI
> serve o React na mesma porta, o caminho relativo funciona em qualquer host.

Adicione o `proxy` no **`frontend/package.json`** (logo após `"version"`):

```json
"proxy": "http://localhost:8000",
```

Isso permite que `npm start` (porta 3000) redirecione chamadas `/api/*` para
o backend em desenvolvimento.

Gerar o build de produção:

```bash
npm run build
```

Cria a pasta `build/`. Avisos do ESLint **não impedem** o build.

### 5) Rodar em produção

```bash
cd ../backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Acesse: **`http://<IP-do-servidor>:8000/`**

> ⚠️ **Não use `--reload` em produção.** Ele reinicia o processo a cada alteração
> em `.py`, consumindo CPU desnecessariamente.

**Sempre que alterar o `src/` do frontend**, rode `npm run build` de novo e
reinicie o backend.

---

## Variáveis de ambiente — referência

**`backend/.env`**

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL PostgreSQL: `postgresql+asyncpg://user:senha@host:5432/banco` |
| `SISREG_USUARIO` / `SISREG_SENHA` | Credenciais fornecidas pelo Ministério da Saúde |
| `SISREG_URL_AMBULATORIAL` / `_MARCACAO` / `_HOSPITALAR` | URLs das 3 bases do SISREG |
| `SISREG_CODIGO_MUNICIPIO` | Código IBGE do município (500830 = Três Lagoas/MS) |
| `VERIFY_SSL` | `False` em geral; `True` se o servidor exigir validação SSL |
| `SMTP_HOST` / `SMTP_PORT` | Servidor SMTP (587 = STARTTLS, 465 = SSL) |
| `SMTP_USER` / `SMTP_PASSWORD` | Conta **remetente** + senha de app |
| `EMAIL_DESTINO` | Quem recebe o aviso |

**`frontend/.env`**

| Variável | Valor recomendado |
|---|---|
| `REACT_APP_API_BASE_URL` | `/api` |

---

## Configuração de e-mail (SMTP)

O sistema envia e-mail quando o cidadão clica em **"Preciso atualizar"**.

**Testar envio:**

```bash
curl http://localhost:8000/api/testar-email
```

Log esperado no uvicorn:

```
[EMAIL] Enviado para cem.cadastro@treslagoas.ms.gov.br — PACIENTE DE TESTE / 123.456.789-01
```

### Gmail / Google Workspace

1. Ative verificação em duas etapas: https://myaccount.google.com/security
2. Gere senha de app: https://myaccount.google.com/apppasswords
3. Use os 16 caracteres como `SMTP_PASSWORD`, `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`


> ⚠️ Alguns domínios institucionais bloqueiam SMTP externo. 

### Erros comuns

| Log | Causa | Solução |
|---|---|---|
| `SMTP não configurado` | `.env` faltando variáveis | Preencher e reiniciar |
| `SMTPAuthenticationError: (535...)` | Senha de app errada | Regerar |
| `ConnectionRefusedError` / `TimeoutError` | Firewall bloqueia porta 587 | Usar outra rede ou liberar |

---

## Solução de problemas

| Problema | Solução |
|---|---|
| `externally-managed-environment` no `pip` | Use `python3 -m venv venv && source venv/bin/activate` |
| `Address already in use` (porta 8000) | `sudo fuser -k 8000/tcp` |
| `ModuleNotFoundError: email.utils` | Existe um `email.py` na pasta — renomeie para `email_utils.py` |
| `RuntimeError: Build do frontend não encontrado` | Rode `cd frontend && npm run build` |
| `password authentication failed` | Senha do PostgreSQL errada no `.env` |
| "Nenhum cadastro encontrado" | CPF sem registro, ou SISREG com credenciais erradas — teste com `curl` |
| E-mail não chega mas log mostra `[EMAIL] Enviado` | Verificar spam ou filtros do destinatário |

---

### Ver dados salvos

```bash
psql -h localhost -U totem_user -d totem_sus
```

```sql
-- Últimas 50 respostas
SELECT * FROM respostas_cadastro ORDER BY id DESC LIMIT 50;

-- Contagem por tipo
SELECT
  COUNT(*) FILTER (WHERE cadastro_correto = true) AS "cadastro ok",
  COUNT(*) FILTER (WHERE precisa_atualizar = true) AS "precisa atualizar"
FROM respostas_cadastro;

-- Exportar CSV
\COPY (SELECT * FROM respostas_cadastro) TO '/tmp/respostas.csv' WITH CSV HEADER;
```

## Contato

**Desenvolvido por:** Ester Pazini Pacheco
**Instituição:** IFMS — Instituto Federal de Mato Grosso do Sul
**Contato técnico:** esterpazinipacheco@gmail.com