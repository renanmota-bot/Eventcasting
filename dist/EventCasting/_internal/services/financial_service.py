from database.database import execute_query

def get_financial_summary_by_event(empresa_id):
    """Retorna o resumo financeiro agrupado por evento."""
    query = """
        SELECT 
            e.id AS evento_id,
            e.nome AS evento_nome,
            e.data_inicio,
            e.data_fim,
            COUNT(c.id) AS total_aprovados,
            SUM(v.valor_diaria) AS total_investido
        FROM eventos e
        JOIN vagas v ON v.evento_id = e.id
        JOIN candidaturas c ON c.vaga_id = v.id
        WHERE e.empresa_id = %s AND UPPER(TRIM(c.status)) = 'APROVADO'
        GROUP BY e.id, e.nome, e.data_inicio, e.data_fim
        ORDER BY e.data_inicio DESC;
    """
    return execute_query(query, (empresa_id,), fetch_all=True) or []

def get_event_payroll(evento_id):
    """Retorna a lista de colaboradores com valor de diária, chave Pix e status de presença."""
    query = """
        SELECT 
            c.id AS candidatura_id,
            u.nome AS staff_nome,
            u.cpf AS staff_cpf,
            u.chave_pix,
            v.funcao,
            v.valor_diaria
        FROM candidaturas c
        JOIN usuarios u ON c.usuario_id = u.id
        JOIN vagas v ON c.vaga_id = v.id
        WHERE v.evento_id = %s AND UPPER(TRIM(c.status)) = 'APROVADO'
        ORDER BY u.nome ASC;
    """
    return execute_query(query, (evento_id,), fetch_all=True) or []