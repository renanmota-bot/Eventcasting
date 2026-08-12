from database.database import execute_query

def get_all_companies():
    query = "SELECT * FROM empresas ORDER BY id DESC"
    return execute_query(query, fetch_all=True) or []

def create_company(nome_fantasia, razao_social, cnpj):
    query = """
        INSERT INTO empresas (nome_fantasia, razao_social, cnpj, status)
        VALUES (%s, %s, %s, 'ATIVO') RETURNING id
    """
    return execute_query(query, (nome_fantasia, razao_social, cnpj), fetch_one=True, commit=True)

def get_all_users_global():
    query = """
        SELECT u.*, e.nome_fantasia as empresa_nome 
        FROM usuarios u 
        LEFT JOIN empresas e ON u.empresa_id = e.id 
        ORDER BY u.id DESC
    """
    return execute_query(query, fetch_all=True) or []

def toggle_user_status(user_id, current_status):
    new_status = 'INATIVO' if current_status == 'ATIVO' else 'ATIVO'
    query = "UPDATE usuarios SET status = %s WHERE id = %s"
    return execute_query(query, (new_status, user_id), commit=True) is not None
