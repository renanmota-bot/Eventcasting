from database.database import execute_query

def get_event_candidacies(empresa_id):
    """Busca todas as candidaturas incluindo a foto do staff."""
    query = """
        SELECT 
            c.id AS candidatura_id,
            c.status AS status_candidatura,
            u.id AS usuario_id,
            u.nome AS staff_nome,
            u.email AS staff_email,
            u.whatsapp AS staff_whatsapp,
            u.chave_pix,
            u.foto_base64,
            v.funcao,
            v.valor_diaria,
            e.nome AS evento_nome
        FROM candidaturas c
        JOIN usuarios u ON c.usuario_id = u.id
        JOIN vagas v ON c.vaga_id = v.id
        JOIN eventos e ON v.evento_id = e.id
        WHERE e.empresa_id = %s
        ORDER BY c.id DESC;
    """
    return execute_query(query, (empresa_id,), fetch_all=True) or []

def update_candidacy_status(candidatura_id, novo_status):
    """Atualiza o status da candidatura (APROVADO / RECUSADO)."""
    status_limpo = str(novo_status).strip().upper()
    query = """
        UPDATE candidaturas
        SET status = %s
        WHERE id = %s
        RETURNING id;
    """
    res = execute_query(query, (status_limpo, candidatura_id), fetch_one=True, commit=True)
    return res is not None