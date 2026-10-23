from datetime import datetime
from sqlalchemy import (
    String, Text, Boolean, Integer, BigInteger,
    DateTime, ForeignKey, func, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from db import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "perfil IN ('ADMINISTRADOR','GESTOR','OPERADOR')",
            name="chk_usuario_perfil",
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(Text, nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), nullable=False, default="OPERADOR")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class Log(Base):
    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    acao: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    data_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())