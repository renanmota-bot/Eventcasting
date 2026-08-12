import random
import smtplib
from email.mime.text import MIMEText

# Dicionário em memória para guardar códigos temporários: { email: codigo }
VERIFICATION_CODES = {}

def generate_verification_code(email: str) -> str:
    """Gera um código numérico de 6 dígitos para o e-mail."""
    code = f"{random.randint(100000, 999999)}"
    VERIFICATION_CODES[email.lower().strip()] = code
    return code

def verify_code(email: str, input_code: str) -> bool:
    """Verifica se o código digitado pelo usuário está correto."""
    email_clean = email.lower().strip()
    stored_code = VERIFICATION_CODES.get(email_clean)
    if stored_code and stored_code == input_code.strip():
        del VERIFICATION_CODES[email_clean]  # Remove após uso
        return True
    return False

def send_email_code(email_destino: str, codigo: str) -> bool:
    """
    Envia o e-mail com o código. 
    Se não houver SMTP configurado, o código será exibido no terminal para testes.
    """
    # IMPORTANTE: Para enviar e-mails reais, preencha as credenciais SMTP abaixo
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = ""  # Seu e-mail (ex: seuemail@gmail.com)
    SMTP_PASS = ""  # Sua senha de app do Gmail

    if not SMTP_USER or not SMTP_PASS:
        print(f"\n==========================================")
        print(f"[VERIFICAÇÃO DEMO] Código para {email_destino}: {codigo}")
        print(f"==========================================\n")
        return True

    try:
        msg = MIMEText(f"Seu código de verificação no Event Casting é: {codigo}")
        msg['Subject'] = "Código de Verificação - Event Casting"
        msg['From'] = SMTP_USER
        msg['To'] = email_destino

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [email_destino], msg.as_string())
        server.quit()
        return True
    except Exception as ex:
        print(f"Erro ao enviar e-mail: {ex}")
        return False
