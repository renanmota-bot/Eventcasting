import sqlite3
from database.database import get_db_connection

def get_confirmed_team_by_event(evento_id: int) -> list:
    """Retorna os colaboradores escalados no evento (Aprovados, Presentes, Pagos ou Faltas)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.id AS candidatura_id, c.status AS status_candidatura,
            v.funcao, v.valor_diaria, v.horario_inicio, v.horario_fim,
            u.id AS usuario_id, u.nome, u.cpf, u.whatsapp, u.chave_pix
        FROM candidaturas c
        JOIN vagas v ON c.vaga_id = v.id
        JOIN usuarios u ON c.usuario_id = u.id
        WHERE v.evento_id = ? AND c.status IN ('APROVADA', 'PRESENTE', 'FALTOU', 'PAGO')
        ORDER BY v.funcao ASC, u.nome ASC
    """, (evento_id,))
    team = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return team

def get_staff_schedule(user_id: int) -> list:
    """Retorna os eventos em que o colaborador está confirmado ou participou."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.id AS candidatura_id, c.status AS status_candidatura,
            v.funcao, v.valor_diaria, v.horario_inicio, v.horario_fim,
            e.nome AS evento_nome, e.data_inicio, e.data_fim, e.local, e.cidade, e.estado
        FROM candidaturas c
        JOIN vagas v ON c.vaga_id = v.id
        JOIN eventos e ON v.evento_id = e.id
        WHERE c.usuario_id = ? AND c.status IN ('APROVADA', 'PRESENTE', 'PAGO')
        ORDER BY e.data_inicio ASC
    """, (user_id,))
    schedule = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return schedule