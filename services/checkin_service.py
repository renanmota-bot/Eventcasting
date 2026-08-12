from database.database import execute_query

def ensure_checkin_columns():
    """Garante que as colunas checkin e checkout existam na tabela candidaturas."""
    query = """
        ALTER TABLE candidaturas 
        ADD COLUMN IF NOT EXISTS checkin TIMESTAMP,
        ADD COLUMN IF NOT EXISTS checkout TIMESTAMP;
    """
    try:
        execute_query(query, commit=True)
    except Exception:
        pass

def get_approved_staff_for_event(empresa_id, evento_id=None):
    """Busca os membros da equipe aprovados para os eventos da empresa."""
    ensure_checkin_columns()
    query = """
        SELECT 
            c.id AS candidatura_id,
            u.id AS usuario_id,
            u.nome AS staff_nome,
            u.whatsapp AS staff_whatsapp,
            v.funcao,
            v.valor_diaria,
            e.id AS evento_id,
            e.nome AS evento_nome,
            e.data_inicio,
            e.data_fim,
            c.checkin,
            c.checkout
        FROM candidaturas c
        JOIN usuarios u ON c.usuario_id = u.id
        JOIN vagas v ON c.vaga_id = v.id
        JOIN eventos e ON v.evento_id = e.id
        WHERE e.empresa_id = %s AND UPPER(TRIM(c.status)) = 'APROVADO'
    """
    params = [empresa_id]
    if evento_id:
        query += " AND e.id = %s"
        params.append(evento_id)
        
    query += " ORDER BY e.data_inicio DESC, u.nome ASC;"
    return execute_query(query, tuple(params), fetch_all=True) or []

def register_checkin(candidatura_id):
    """Registra o horário de entrada do colaborador."""
    ensure_checkin_columns()
    query = """
        UPDATE candidaturas
        SET checkin = NOW()
        WHERE id = %s
        RETURNING id;
    """
    res = execute_query(query, (candidatura_id,), fetch_one=True, commit=True)
    return res is not None

def register_checkout(candidatura_id):
    """Registra o horário de saída do colaborador."""
    ensure_checkin_columns()
    query = """
        UPDATE candidaturas
        SET checkout = NOW()
        WHERE id = %s
        RETURNING id;
    """
    res = execute_query(query, (candidatura_id,), fetch_one=True, commit=True)
    return res is not None

def get_staff_approved_schedules(usuario_id):
    """Busca as escalas confirmadas para a visão do Staff."""
    ensure_checkin_columns()
    query = """
        SELECT 
            e.nome AS evento_nome,
            e.local AS evento_local,
            e.data_inicio,
            e.data_fim,
            v.funcao,
            v.valor_diaria,
            emp.nome_fantasia AS empresa_nome,
            c.checkin,
            c.checkout
        FROM candidaturas c
        JOIN vagas v ON c.vaga_id = v.id
        JOIN eventos e ON v.evento_id = e.id
        JOIN empresas emp ON e.empresa_id = emp.id
        WHERE c.usuario_id = %s AND UPPER(TRIM(c.status)) = 'APROVADO'
        ORDER BY e.data_inicio ASC;
    """
    return execute_query(query, (usuario_id,), fetch_all=True) or []