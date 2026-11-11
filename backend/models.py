from datetime import datetime
from sqlalchemy import String, Boolean, BigInteger, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from db import Base

class RespostaCadastro(Base):
    __tablename__ = "respostas_cadastro"
    __table_args__ = (
        CheckConstraint(
            "(cadastro_correto = TRUE AND precisa_atualizar = FALSE) OR "
            "(cadastro_correto = FALSE AND precisa_atualizar = TRUE)",
            name="chk_uma_escolha",
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome_paciente: Mapped[str] = mapped_column(String(200), nullable=False)
    cadastro_correto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    precisa_atualizar: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())