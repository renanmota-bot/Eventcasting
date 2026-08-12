import sqlite3
from database.database import get_db_connection

def get_all_staff(status_filter: str = None) -> list:
    """Busca todos os colaboradores do tipo STAFF, com filtro opcional por status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if status_filter and status_filter != "TODOS":
        cursor.execute("SELECT * FROM usuarios WHERE perfil = 'STAFF' AND status = ? ORDER BY data_cadastro DESC", (status_filter,))
    else:
        cursor.execute("SELECT * FROM usuarios WHERE perfil = 'STAFF' ORDER BY data_cadastro DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def update_user_status(user_id: int, new_status: str) -> bool:
    """Atualiza o status do colaborador (APROVADO, RECUSADO, BLOQUEADO)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE usuarios SET status = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> dict:
    """Retorna os dados atualizados de um determinado usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None
