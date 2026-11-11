import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv 

load_dotenv()  

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "esterpazinipacheco@gmail.com")


def _formatar_cpf(cpf: str) -> str:
    if not cpf:
        return "Não informado"
    limpo = "".join(c for c in str(cpf) if c.isdigit())
    if len(limpo) == 11:
        return f"{limpo[:3]}.{limpo[3:6]}.{limpo[6:9]}-{limpo[9:]}"
    return str(cpf)


def enviar_email_atualizacao(nome: str, cpf: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[EMAIL] SMTP não configurado no .env — envio ignorado", flush=True)
        return

    try:
        fuso = ZoneInfo("America/Campo_Grande")
        agora = datetime.now(fuso)
        data_formatada = agora.strftime("%d/%m/%Y às %H:%M:%S")

        cpf_fmt = _formatar_cpf(cpf)

        assunto = "TOTEM - ATUALIZA SUS"

        corpo = (
            "Olá,\n\n"
            "Um paciente clicou no botão \"Preciso atualizar\" no Totem Atualiza SUS.\n\n"
            "----------------------------------------\n"
            "Dados do paciente\n"
            "----------------------------------------\n"
            f"Nome completo : {nome or 'Não informado'}\n"
            f"CPF           : {cpf_fmt}\n"
            f"Data e hora   : {data_formatada}\n\n"
            "----------------------------------------\n"
            "Mensagem automática — não responda este email.\n"
            "Totem Atualiza SUS\n"
        )

        msg = EmailMessage()
        msg["Subject"] = assunto
        msg["From"] = SMTP_USER
        msg["To"] = EMAIL_DESTINO
        msg.set_content(corpo)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)

        print(f"[EMAIL] Enviado para {EMAIL_DESTINO} — {nome} / {cpf_fmt}", flush=True)

    except Exception as e:
        print(f"[EMAIL] Falha ao enviar: {type(e).__name__}: {e}", flush=True)