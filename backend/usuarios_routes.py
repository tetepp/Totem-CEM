from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import Usuario, Log
from auth import (
    get_current_user, requer, hash_senha, verificar_senha,
    criar_token, SENHA_PADRAO,
)

router = APIRouter(prefix="/api", tags=["usuarios"])

# ---------- Schemas ----------
class LoginIn(BaseModel):
    login: str
    senha: str

class UsuarioIn(BaseModel):
    nome: str
    login: str
    perfil: str = "OPERADOR"

class UsuarioPatch(BaseModel):
    nome: Optional[str] = None
    perfil: Optional[str] = None
    ativo: Optional[bool] = None

class SenhaIn(BaseModel):
    senha_atual: Optional[str] = None
    senha_nova: str

# ---------- Helpers ----------
def _u_out(u: Usuario) -> dict:
    return {
        "id": u.id, "nome": u.nome, "login": u.login,
        "perfil": u.perfil, "ativo": u.ativo,
        "criado_em": u.criado_em.isoformat() if u.criado_em else None,
        "atualizado_em": u.atualizado_em.isoformat() if u.atualizado_em else None,
    }

async def _log(db: AsyncSession, usuario_id: int | None, acao: str, descricao: str):
    db.add(Log(usuario_id=usuario_id, acao=acao, descricao=descricao))
    await db.commit()

# ---------- Auth ----------
@router.post("/auth/login")
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.login == body.login))
    user = result.scalar_one_or_none()
    if not user or not user.ativo or not verificar_senha(body.senha, user.senha_hash):
        raise HTTPException(401, "Login ou senha inválidos")
    token = criar_token(user.login, user.perfil)
    await _log(db, user.id, "LOGIN", f"Usuário {user.login} entrou no sistema")
    return {
        "access_token": token, "token_type": "bearer",
        "perfil": user.perfil, "nome": user.nome, "login": user.login,
    }

@router.get("/auth/me")
async def me(user: Usuario = Depends(get_current_user)):
    return _u_out(user)

# ---------- Usuários ----------
@router.get("/usuarios")
async def listar_usuarios(
    user: Usuario = Depends(requer("ADMINISTRADOR", "GESTOR")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Usuario).order_by(Usuario.id))
    return [_u_out(u) for u in result.scalars().all()]

@router.post("/usuarios")
async def criar_usuario(
    body: UsuarioIn,
    user: Usuario = Depends(requer("ADMINISTRADOR", "GESTOR")),
    db: AsyncSession = Depends(get_db),
):
    if body.perfil not in ("ADMINISTRADOR", "GESTOR", "OPERADOR"):
        raise HTTPException(400, "Perfil inválido")
    if user.perfil == "GESTOR" and body.perfil == "ADMINISTRADOR":
        raise HTTPException(403, "GESTOR não pode criar ADMINISTRADOR")

    existe = await db.execute(select(Usuario).where(Usuario.login == body.login))
    if existe.scalar_one_or_none():
        raise HTTPException(400, "Login já existe")

    novo = Usuario(
        nome=body.nome,
        login=body.login,
        perfil=body.perfil,
        senha_hash=hash_senha(SENHA_PADRAO),
        ativo=True,
    )
    db.add(novo)
    await db.commit()
    await db.refresh(novo)
    await _log(db, user.id, "CRIAR_USUARIO", f"Criou usuário {novo.login} ({novo.perfil})")
    return _u_out(novo)

@router.patch("/usuarios/{uid}")
async def atualizar_usuario(
    uid: int,
    body: UsuarioPatch,
    user: Usuario = Depends(requer("ADMINISTRADOR", "GESTOR")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Usuario).where(Usuario.id == uid))
    alvo = result.scalar_one_or_none()
    if not alvo:
        raise HTTPException(404, "Usuário não encontrado")
    if user.perfil == "GESTOR" and alvo.perfil == "ADMINISTRADOR":
        raise HTTPException(403, "GESTOR não pode editar ADMINISTRADOR")

    if body.nome is not None:
        alvo.nome = body.nome
    if body.perfil is not None:
        if body.perfil not in ("ADMINISTRADOR", "GESTOR", "OPERADOR"):
            raise HTTPException(400, "Perfil inválido")
        if user.perfil == "GESTOR" and body.perfil == "ADMINISTRADOR":
            raise HTTPException(403, "GESTOR não pode promover para ADMINISTRADOR")
        alvo.perfil = body.perfil
    if body.ativo is not None:
        alvo.ativo = body.ativo

    await db.commit()
    await db.refresh(alvo)
    await _log(db, user.id, "ATUALIZAR_USUARIO", f"Atualizou usuário {alvo.login}")
    return _u_out(alvo)

# ---------- Trocar a própria senha (todos os perfis) ----------
@router.post("/usuarios/me/senha")
async def resetar_minha_senha(
    body: SenhaIn,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.senha_atual:
        if not verificar_senha(body.senha_atual, user.senha_hash):
            raise HTTPException(400, "Senha atual incorreta")
    if len(body.senha_nova) < 3:
        raise HTTPException(400, "Senha muito curta (mínimo 3 caracteres)")
    user.senha_hash = hash_senha(body.senha_nova)
    await db.commit()
    await _log(db, user.id, "RESETAR_SENHA", f"Usuário {user.login} trocou a própria senha")
    return {"ok": True}

# ---------- Logs (ajuda a auditar usuários) ----------
@router.get("/logs")
async def listar_logs(
    limit: int = 100,
    user: Usuario = Depends(requer("ADMINISTRADOR", "GESTOR")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Log).order_by(desc(Log.id)).limit(limit))
    return [
        {
            "id": l.id, "usuario_id": l.usuario_id,
            "acao": l.acao, "descricao": l.descricao,
            "data_hora": l.data_hora.isoformat() if l.data_hora else None,
        }
        for l in result.scalars().all()
    ]