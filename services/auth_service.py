from database.database import execute_query

def ensure_address_columns():
    """Garante que as colunas necessárias existam na tabela usuarios."""
    query = """
        ALTER TABLE usuarios 
        ADD COLUMN IF NOT EXISTS foto_base64 TEXT,
        ADD COLUMN IF NOT EXISTS cep VARCHAR(10),
        ADD COLUMN IF NOT EXISTS endereco TEXT,
        ADD COLUMN IF NOT EXISTS numero VARCHAR(20),
        ADD COLUMN IF NOT EXISTS bairro VARCHAR(100),
        ADD COLUMN IF NOT EXISTS cidade VARCHAR(100),
        ADD COLUMN IF NOT EXISTS estado VARCHAR(2);
    """
    try:
        execute_query(query, commit=True)
    except Exception:
        pass

def authenticate_user(email, senha):
    """Autentica o usuário pelo e-mail e senha no banco de dados."""
    ensure_address_columns()
    query = """
        SELECT id, empresa_id, nome, email, perfil, status, foto_base64,
               cep, endereco, numero, bairro, cidade, estado
        FROM usuarios
        WHERE email = %s AND senha = %s AND status = 'ATIVO';
    """
    return execute_query(query, (email, senha), fetch_one=True)

def register_staff_user(empresa_id, nome, email, senha, cpf, whatsapp, chave_pix, 
                        cep=None, endereco=None, numero=None, bairro=None, cidade=None, estado=None, foto_base64=None):
    """Cadastra um novo usuário STAFF com seu endereço completo."""
    ensure_address_columns()
    query = """
        INSERT INTO usuarios (
            empresa_id, nome, email, senha, cpf, whatsapp, chave_pix, 
            cep, endereco, numero, bairro, cidade, estado, foto_base64, perfil, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'STAFF', 'ATIVO')
        RETURNING id;
    """
    res = execute_query(
        query, 
        (empresa_id, nome, email, senha, cpf, whatsapp, chave_pix, 
         cep, endereco, numero, bairro, cidade, estado, foto_base64), 
        fetch_one=True, 
        commit=True
    )
    return res is not None

def update_user_profile(user_id, nome, whatsapp, chave_pix, cep=None, endereco=None, 
                        numero=None, bairro=None, cidade=None, estado=None, senha=None, foto_base64=None):
    """Atualiza as informações, endereço e foto do perfil do usuário."""
    ensure_address_columns()
    if senha and senha.strip():
        query = """
            UPDATE usuarios
            SET nome = %s, whatsapp = %s, chave_pix = %s, 
                cep = %s, endereco = %s, numero = %s, bairro = %s, cidade = %s, estado = %s,
                senha = %s, foto_base64 = COALESCE(%s, foto_base64)
            WHERE id = %s;
        """
        params = (nome, whatsapp, chave_pix, cep, endereco, numero, bairro, cidade, estado, senha.strip(), foto_base64, user_id)
    else:
        query = """
            UPDATE usuarios
            SET nome = %s, whatsapp = %s, chave_pix = %s, 
                cep = %s, endereco = %s, numero = %s, bairro = %s, cidade = %s, estado = %s,
                foto_base64 = COALESCE(%s, foto_base64)
            WHERE id = %s;
        """
        params = (nome, whatsapp, chave_pix, cep, endereco, numero, bairro, cidade, estado, foto_base64, user_id)

    res = execute_query(query, params, commit=True)
    return res is not None