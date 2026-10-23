import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from models import Usuario

SECRET_KEY = os.getenv("SECRET_KEY", "troque-no-env")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MIN = int(os.getenv("TOKEN_EXPIRE_MIN", "480"))
SENHA_PADRAO = os.getenv("SENHA_PADRAO", "123")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_senha(s: str) -> str:
    return pwd_context.hash(s)

def verificar_senha(s: str, h: str) -> bool:
    return pwd_context.verify(s, h)

def criar_token(login: str, perfil: str) -> str:
    payload = {
        "sub": login,
        "perfil": perfil,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    if not token:
        raise HTTPException(401, "Não autenticado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login = payload.get("sub")
    except JWTError:
        raise HTTPException(401, "Token inválido")
    result = await db.execute(select(Usuario).where(Usuario.login == login))
    user = result.scalar_one_or_none()
    if not user or not user.ativo:
        raise HTTPException(401, "Usuário inválido ou inativo")
    return user

def requer(*perfis):
    async def dep(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.perfil not in perfis:
            raise HTTPException(403, "Permissão insuficiente")
        return user
    return dep