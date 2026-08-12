from database.database import execute_query

def get_open_jobs_for_staff(usuario_id):
    """Busca todas as vagas abertas no sistema com o status da candidatura do usuário."""
    query = """
        SELECT 
            v.id AS vaga_id,
            v.funcao,
            v.valor_diaria,
            v.quantidade,
            e.nome AS evento_nome,
            e.local AS evento_local,
            e.data_inicio,
            e.data_fim,
            emp.nome_fantasia AS empresa_nome,
            c.status AS candidato_status
        FROM vagas v
        JOIN eventos e ON v.evento_id = e.id
        JOIN empresas emp ON e.empresa_id = emp.id
        LEFT JOIN candidaturas c ON c.vaga_id = v.id AND c.usuario_id = %s
        WHERE v.status = 'ABERTA' AND e.status = 'ATIVO'
        ORDER BY v.id DESC;
    """
    return execute_query(query, (usuario_id,), fetch_all=True) or []

def apply_for_job(vaga_id, usuario_id):
    """Insere ou atualiza a candidatura do colaborador para PENDENTE."""
    query = """
        INSERT INTO candidaturas (vaga_id, usuario_id, status)
        VALUES (%s, %s, 'PENDENTE')
        ON CONFLICT (vaga_id, usuario_id) 
        DO UPDATE SET status = 'PENDENTE'
        RETURNING id;
    """
    res = execute_query(query, (vaga_id, usuario_id), fetch_one=True, commit=True)
    return res is not None