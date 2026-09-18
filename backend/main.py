from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from unicodedata import normalize
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
    raise RuntimeError("Credenciais SISREG não configuradas no .env")
if not URL_SOLICITACOES or not URL_MARCACOES or not URL_HOSPITALAR:
    raise RuntimeError("URLs do SISREG não configuradas no .env")

app = FastAPI(title="Totem CEM - Consulta SUS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Helpers ----------------

def normalizar(texto: str) -> str:
    if not texto:
        return ""
    return normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode().lower().strip()

def apenas_digitos(v) -> str:
    return re.sub(r"\D", "", str(v or ""))

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
    cidade_uf = f", {cidade} - {uf}" if cidade and uf else (f", {cidade}" if cidade else "")
    cep = apenas_digitos(g("cep_paciente_residencia"))
    cep_str = f", CEP: {cep[:5]}-{cep[5:]}" if len(cep) == 8 else (f", CEP: {cep}" if cep else "")

    return f"{rua}{num}{comp_str}{bairro_str}{cidade_uf}{cep_str}".upper()

def extrair_telefones(*objetos) -> list[str]:
    chaves = ["telefone_paciente", "telefone", "telefone_unidade_executante"]
    encontrados = []
    for obj in objetos:
        if not obj:
            continue
        for k in chaves:
            v = obj.get(k)
            if not v:
                continue
            for parte in re.split(r"[,;/]", str(v)):
                num = apenas_digitos(parte)
                if num and num not in encontrados:
                    encontrados.append(num)
    return encontrados

# ---------------- Rota principal ----------------

@app.get("/api/consulta/{cpf}")
async def consultar_cpf(cpf: str, nome_mae: str = Query(...)):
    cpf_limpo = apenas_digitos(cpf)
    if len(cpf_limpo) != 11:
        raise HTTPException(400, "CPF inválido")

    payload = {
        "query": {"bool": {"must": [{"term": {"cpf_usuario": cpf_limpo}}]}},
        "size": 100,
    }
    headers = {"Content-Type": "application/json"}
    auth = (USUARIO, SENHA)

    async def buscar(url):
        async with httpx.AsyncClient(timeout=30.0, verify=VERIFY_SSL) as c:
            try:
                r = await c.post(f"{url}/_search", json=payload, headers=headers, auth=auth)
                if r.status_code == 200:
                    return r.json().get("hits", {}).get("hits", [])
            except Exception:
                return []
        return []

    resultados = await asyncio.gather(
        buscar(URL_SOLICITACOES),
        buscar(URL_MARCACOES),
        buscar(URL_HOSPITALAR),
    )

    registros = [hit for lista in resultados for hit in lista]
    if not registros:
        raise HTTPException(404, "Nenhum registro encontrado para este CPF")

    # ---------- valida nome da mãe ----------
    nome_mae_banco = ""
    for hit in registros:
        m = hit.get("_source", {}).get("no_mae_usuario")
        if m and str(m).strip():
            nome_mae_banco = str(m).strip()
            break

    if not nome_mae_banco:
        raise HTTPException(403, "Dados cadastrais incompletos no sistema.")

    primeiro_real = normalizar(nome_mae_banco).split()[0]
    primeiro_digitado = normalizar(nome_mae).split()[0] if nome_mae else ""

    if primeiro_real != primeiro_digitado:
        raise HTTPException(403, "Nome da mãe incorreto")

    # ---------- pega dados cadastrais (do 1º hit) ----------
    base = registros[0].get("_source", {})

    # Telefones e endereço podem estar em qualquer uma das bases;
    # junta tudo o que achar.
    todos_sources = [h.get("_source", {}) for h in registros]

    endereco = ""
    for s in todos_sources:
        endereco = montar_endereco(s)
        if endereco:
            break

    telefones = extrair_telefones(*todos_sources)

    return {
        "nome": base.get("no_usuario") or base.get("nome_usuario") or "",
        "cpf": cpf_limpo,
        "data_nascimento": base.get("dt_nascimento_usuario") or "",
        "nome_mae": nome_mae_banco,
        "endereco_completo": endereco or "Endereço não informado",
        "telefones": telefones or ["Não informado"],
    }