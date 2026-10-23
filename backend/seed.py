import asyncio
from sqlalchemy import select
from db import SessionLocal, init_db
from models import Usuario
from auth import hash_senha, SENHA_PADRAO

async def main():
    await init_db()
    async with SessionLocal() as db:
        r = await db.execute(select(Usuario).where(Usuario.login == "admin"))
        if r.scalar_one_or_none():
            print("admin já existe — nada a fazer")
            return
        db.add(Usuario(
            nome="Administrador",
            login="admin",
            perfil="ADMINISTRADOR",
            senha_hash=hash_senha(SENHA_PADRAO),
            ativo=True,
        ))
        await db.commit()
        print(f"✅ admin criado com senha padrão '{SENHA_PADRAO}'")

if __name__ == "__main__":
    asyncio.run(main())