import os
import psycopg2
from psycopg2 import pool

DATABASE_URL = os.getenv("DATABASE_URL")

# Pool de conexões permanentes para evitar o delay de reconexão (mín 1, máx 10)
db_pool = None

def get_pool():
    global db_pool
    if db_pool is None and DATABASE_URL:
        try:
            db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
        except Exception as e:
            print(f"Erro ao criar pool de conexões: {e}")
    return db_pool

def execute_query(query, params=None, fetch_all=False, commit=False):
    pool_obj = get_pool()
    conn = None
    if pool_obj:
        conn = pool_obj.getconn()
    else:
        conn = psycopg2.connect(DATABASE_URL)

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            if commit:
                conn.commit()
            if fetch_all:
                return cur.fetchall()
            return None
    finally:
        if pool_obj and conn:
            pool_obj.putconn(conn)
        elif conn:
            conn.close()