import re

def is_valid_email(email: str) -> bool:
    """Valida se o formato do e-mail é válido."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email.strip()))

def is_valid_cpf(cpf: str) -> bool:
    """Valida os dígitos verificadores de um CPF brasileiro real."""
    cpf_digits = [int(digit) for digit in re.sub(r'\D', '', cpf)]
    
    if len(cpf_digits) != 11 or len(set(cpf_digits)) == 1:
        return False
        
    sum_first = sum(cpf_digits[i] * (10 - i) for i in range(9))
    first_digit = (sum_first * 10 % 11) % 10
    if cpf_digits[9] != first_digit:
        return False
        
    sum_second = sum(cpf_digits[i] * (11 - i) for i in range(10))
    second_digit = (sum_second * 10 % 11) % 10
    return cpf_digits[10] == second_digit

def is_valid_whatsapp(phone: str) -> bool:
    """Valida número de WhatsApp brasileiro no formato (DD) 9XXXX-XXXX."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) != 11:
        return False
    ddd = int(digits[:2])
    if ddd < 11 or ddd > 99:
        return False
    return digits[2] == '9'

def is_strong_password(password: str) -> tuple[bool, str]:
    """
    Valida se a senha atende aos critérios de segurança:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    """
    if len(password) < 8:
        return False, "A senha deve ter no mínimo 8 caracteres."
    if not re.search(r'[A-Z]', password):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r'[a-z]', password):
        return False, "A senha deve conter pelo menos uma letra minúscula."
    if not re.search(r'[0-9]', password):
        return False, "A senha deve conter pelo menos um número."
    if not re.search(r'[@#$%^&+=!_*-]', password):
        return False, "A senha deve conter pelo menos um caractere especial (@, #, $, %, etc.)."
    
    return True, "Senha forte!"
