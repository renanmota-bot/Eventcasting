from database.database import execute_query

def get_event_jobs(evento_id):
    query = """
        SELECT id, funcao, valor_diaria, quantidade, descricao, status
        FROM vagas
        WHERE evento_id = %s
        ORDER BY id DESC;
    """
    return execute_query(query, (evento_id,), fetch_all=True) or []

def create_job(evento_id, funcao, valor_diaria, quantidade, descricao=""):
    query = """
        INSERT INTO vagas (evento_id, funcao, valor_diaria, quantidade, descricao, status)
        VALUES (%s, %s, %s, %s, %s, 'ABERTA')
        RETURNING id;
    """
    res = execute_query(query, (evento_id, funcao, valor_diaria, quantidade, descricao), fetch_one=True, commit=True)
    return res is not None