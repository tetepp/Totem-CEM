
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from unicodedata import normalize
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db import init_db, get_db
from models import RespostaCadastro
from email_utils import enviar_email_atualizacao

import os
import re
import asyncio
import httpx


load_dotenv()

USUARIO = os.getenv("SISREG_USUARIO")
SENHA = os.getenv("SISREG_SENHA")
CODIGO_MUNICIPIO = os.getenv("SISREG_CODIGO_MUNICIPIO", "500830")
VERIFY_SSL = os.getenv("VERIFY_SSL", "False").lower() == "true"
ORIGINS = os.getenv("ORIGINS_PERMITIDAS", "*").split(",")

URL_SOLICITACOES = os.getenv("SISREG_URL_AMBULATORIAL")
URL_MARCACOES = os.getenv("SISREG_URL_MARCACAO")
URL_HOSPITALAR = os.getenv("SISREG_URL_HOSPITALAR")

if not USUARIO or not SENHA:
    raise RuntimeError("Credenciais SISREG não configuradas.")

if not URL_SOLICITACOES or not URL_MARCACOES or not URL_HOSPITALAR:
    raise RuntimeError("URLs do SISREG não configuradas.")


# ---------------- CAMINHO DO FRONTEND ----------------

FRONTEND_BUILD_DIR = (
    Path(__file__).resolve().parent.parent / "frontend" / "build"
)


# ---------------- INICIALIZAÇÃO ----------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[BOOT] Banco de dados inicializado.", flush=True)
    yield
    print("[SHUTDOWN] Encerrando aplicação.", flush=True)


app = FastAPI(
    title="Totem CEM - Consulta SUS",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- HELPERS ----------------

def normalizar(texto: str) -> str:
    if not texto:
        return ""

    return (
        normalize("NFKD", str(texto))
        .encode("ASCII", "ignore")
        .decode()
        .lower()
        .strip()
    )


def apenas_digitos(v) -> str:
    return re.sub(r"\D", "", str(v or ""))


def normalizar_data_iso(data_str) -> str:
    """
    Converte qualquer formato de data vindo do SISREG
    para YYYY-MM-DD.
    Evita problemas de fuso horário no frontend.
    """
    if not data_str:
        return ""

    dt = str(data_str).strip()

    if "T" in dt:
        dt = dt.split("T")[0]
    elif " " in dt:
        dt = dt.split(" ")[0]

    if "/" in dt:
        partes = dt.split("/")

        if len(partes) == 3:
            a, b, c = partes[0], partes[1], partes[2]

            if len(a) == 4:
                dt = f"{a[:4]}-{b.zfill(2)}-{c.zfill(2)}"
            else:
                dt = f"{c[:4]}-{b.zfill(2)}-{a.zfill(2)}"

    return dt


def montar_endereco(obj: dict) -> str:

    def g(k):
        v = obj.get(k)
        return str(v).strip() if v and str(v).strip() else ""

    tipo = g("tipo_logradouro_paciente_residencia")
    logradouro = g("endereco_paciente_residencia")

    rua = " ".join(t for t in [tipo, logradouro] if t)

    if not rua:
        return ""

    numero = g("numero_paciente_residencia")
    num = f", nº {numero}" if numero else ", s/n"

    bairro = g("bairro_paciente_residencia")
    bairro_str = f", {bairro}" if bairro else ""

    comp = g("complemento_paciente_residencia")
    comp_str = f", {comp}" if comp else ""

    cidade = g("municipio_paciente_residencia")
    uf = g("uf_paciente_residencia")

    cidade_uf = (
        f", {cidade} - {uf}"
        if cidade and uf
        else (f", {cidade}" if cidade else "")
    )

    cep = apenas_digitos(g("cep_paciente_residencia"))

    cep_str = (
        f", CEP: {cep[:5]}-{cep[5:]}"
        if len(cep) == 8
        else (f", CEP: {cep}" if cep else "")
    )

    return (
        f"{rua}{num}{comp_str}{bairro_str}{cidade_uf}{cep_str}"
    ).upper()


def extrair_telefones(*objetos) -> list[str]:

    chaves = [
        "telefone_paciente",
        "telefone",
        "telefone_unidade_executante",
        "telefone_unificado"
    ]

    encontrados = []

    for obj in objetos:
        if not obj:
            continue

        for k in chaves:
            v = obj.get(k)

            if not v:
                continue

            for parte in re.split(r"[,;/\s\\-]+", str(v)):
                num = apenas_digitos(parte)

                if num and len(num) in (10, 11) and num not in encontrados:
                    encontrados.append(num)

    return encontrados


# ---------------- CONSULTA SISREG ----------------

@app.get("/api/consulta/{cpf}")
async def consultar_cpf(
    cpf: str,
    nome_mae: str = Query(...)
):

    cpf_limpo = apenas_digitos(cpf)

    if len(cpf_limpo) != 11:
        raise HTTPException(400, "CPF inválido")

    payload = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"cpf_usuario": cpf_limpo}}
                ]
            }
        },
        "size": 100,
    }

    headers = {"Content-Type": "application/json"}
    auth = (USUARIO, SENHA)

    async def buscar(url):

        async with httpx.AsyncClient(
            timeout=30.0,
            verify=VERIFY_SSL
        ) as c:

            try:
                r = await c.post(
                    f"{url}/_search",
                    json=payload,
                    headers=headers,
                    auth=auth
                )

                if r.status_code == 200:
                    return r.json().get("hits", {}).get("hits", [])

            except Exception as e:
                print(f"[SISREG] Erro na consulta: {e}", flush=True)

        return []

    resultados = await asyncio.gather(
        buscar(URL_SOLICITACOES),
        buscar(URL_MARCACOES),
        buscar(URL_HOSPITALAR),
    )

    registros = [
        hit
        for lista in resultados
        for hit in lista
    ]

    if not registros:
        raise HTTPException(
            404,
            "Nenhum registro encontrado para este CPF"
        )

    # ---------- VALIDA NOME DA MÃE ----------

    nome_mae_banco = ""

    for hit in registros:
        m = hit.get("_source", {}).get("no_mae_usuario")

        if m and str(m).strip():
            nome_mae_banco = str(m).strip()
            break

    if not nome_mae_banco:
        raise HTTPException(
            403,
            "Dados cadastrais incompletos no sistema."
        )

    primeiro_real = normalizar(nome_mae_banco).split()[0]

    primeiro_digitado = (
        normalizar(nome_mae).split()[0]
        if nome_mae
        else ""
    )

    if primeiro_real != primeiro_digitado:
        raise HTTPException(403, "Nome da mãe incorreto")

    base = registros[0].get("_source", {})

    todos_sources = [
        h.get("_source", {})
        for h in registros
    ]

    endereco = ""

    for s in todos_sources:
        endereco = montar_endereco(s)

        if endereco:
            break

    telefones = extrair_telefones(*todos_sources)

    data_nasc = normalizar_data_iso(
        base.get("dt_nascimento_usuario")
    )

    return {
        "nome": base.get("no_usuario") or base.get("nome_usuario") or "",
        "cpf": cpf_limpo,
        "data_nascimento": data_nasc,
        "nome_mae": nome_mae_banco,
        "endereco_completo": endereco or "Endereço não informado",
        "telefones": telefones or ["Não informado"],
    }


# ---------------- REGISTRAR RESPOSTA DO CIDADÃO ----------------

class RespostaIn(BaseModel):
    nome: str
    cpf: Optional[str] = None
    cadastro_correto: bool = False
    precisa_atualizar: bool = False


@app.post("/api/respostas")
async def salvar_resposta(
    body: RespostaIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):

    print(
        f"[RESPOSTA] Recebido: nome={body.nome!r} "
        f"cpf={body.cpf!r} "
        f"correto={body.cadastro_correto} "
        f"atualizar={body.precisa_atualizar}",
        flush=True,
    )

    if not body.cadastro_correto and not body.precisa_atualizar:
        raise HTTPException(400, "Marque uma das opções")

    if body.cadastro_correto and body.precisa_atualizar:
        raise HTTPException(400, "Só pode marcar uma das opções")

    nova = RespostaCadastro(
        nome_paciente=body.nome,
        cadastro_correto=body.cadastro_correto,
        precisa_atualizar=body.precisa_atualizar,
    )

    db.add(nova)

    await db.commit()
    await db.refresh(nova)

    if body.precisa_atualizar:

        print(
            f"[RESPOSTA] Agendando email para {body.nome}",
            flush=True
        )

        background_tasks.add_task(
            enviar_email_atualizacao,
            body.nome,
            body.cpf or "",
        )

    return {
        "id": nova.id,
        "ok": True
    }


@app.get("/api/respostas")
async def listar_respostas(
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(RespostaCadastro)
        .order_by(desc(RespostaCadastro.id))
        .limit(1000)
    )

    return [
        {
            "id": r.id,
            "nome_paciente": r.nome_paciente,
            "cadastro_correto": r.cadastro_correto,
            "precisa_atualizar": r.precisa_atualizar,
            "data_hora": (
                r.data_hora.isoformat()
                if r.data_hora
                else None
            ),
        }
        for r in result.scalars().all()
    ]


# ---------------- ROTA DE TESTE DE EMAIL ----------------

@app.get("/api/testar-email")
async def testar_email(
    background_tasks: BackgroundTasks
):

    background_tasks.add_task(
        enviar_email_atualizacao,
        "PACIENTE DE TESTE",
        "12345678901",
    )

    return {
        "ok": True,
        "msg": "Email em background. Confira o log do uvicorn."
    }


# ---------------- HEALTH CHECK ----------------

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "servico": "Totem CEM - Consulta SUS"
    }


# ---------------- FRONTEND REACT ----------------
if not FRONTEND_BUILD_DIR.is_dir():
    raise RuntimeError(
        f"Build do frontend não encontrado: {FRONTEND_BUILD_DIR}"
    )

app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_BUILD_DIR,
        html=True
    ),
    name="frontend"
)
