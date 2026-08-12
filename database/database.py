import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import DB_CONFIG

def get_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

# Alias para compatibilidade com os demais arquivos do projeto
get_db_connection = get_connection

def execute_query(query, params=None, fetch_all=False, fetch_one=False, commit=False):
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            result = None
            if fetch_all:
                result = cursor.fetchall()
            elif fetch_one:
                result = cursor.fetchone()
            if commit:
                conn.commit()
            return result
    except Exception as e:
        print(f"Erro na Query: {e}")
        if commit:
            conn.rollback()
        return None
    finally:
        conn.close()