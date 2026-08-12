import sqlite3
from database.database import get_db_connection

def apply_to_job(job_id: int, user_id: int) -> tuple[bool, str]:
    """Registra a candidatura de um colaborador a uma vaga."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO candidaturas (vaga_id, usuario_id, status)
            VALUES (?, ?, 'PENDENTE')
        """, (job_id, user_id))
        conn.commit()
        return True, "Candidatura enviada com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Você já se candidatou a esta vaga."
    except Exception as e:
        return False, f"Erro ao candidatar-se: {e}"
    finally:
        conn.close()

def get_open_jobs_for_staff(user_id: int) -> list:
    """Busca todas as vagas abertas e identifica se o colaborador já se candidatou."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            v.*, 
            e.nome AS evento_nome, e.data_inicio, e.local, e.cidade, e.estado,
            c.id AS candidatura_id, c.status AS candidatura_status
        FROM vagas v
        JOIN eventos e ON v.evento_id = e.id
        LEFT JOIN candidaturas c ON v.id = c.vaga_id AND c.usuario_id = ?
        WHERE v.status = 'ABERTA' AND e.status = 'PUBLICADO'
        ORDER BY e.data_inicio ASC
    """, (user_id,))
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs

def get_candidates_by_job(job_id: int) -> list:
    """Retorna todos os colaboradores inscritos em uma determinada vaga."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.id AS candidatura_id, c.status AS candidatura_status, c.data_candidatura,
            u.id AS usuario_id, u.nome, u.cpf, u.whatsapp, u.cidade, u.estado, u.funcao_principal, u.experiencia, u.chave_pix
        FROM candidaturas c
        JOIN usuarios u ON c.usuario_id = u.id
        WHERE c.vaga_id = ?
        ORDER BY c.data_candidatura ASC
    """, (job_id,))
    candidates = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return candidates

def update_application_status(candidatura_id: int, new_status: str) -> bool:
    """Atualiza o status da candidatura (APROVADA ou RECUSADA)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE candidaturas SET status = ? WHERE id = ?", (new_status, candidatura_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()
