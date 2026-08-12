from database.database import execute_query

def ensure_event_address_columns():
    """Garante que a tabela de eventos tenha colunas de CEP e endereço detalhado."""
    query = """
        ALTER TABLE eventos 
        ADD COLUMN IF NOT EXISTS cep VARCHAR(10),
        ADD COLUMN IF NOT EXISTS endereco TEXT,
        ADD COLUMN IF NOT EXISTS numero VARCHAR(20),
        ADD COLUMN IF NOT EXISTS bairro VARCHAR(100),
        ADD COLUMN IF NOT EXISTS cidade VARCHAR(100),
        ADD COLUMN IF NOT EXISTS estado VARCHAR(2);
    """
    try:
        execute_query(query, commit=True)
    except Exception:
        pass

def create_event(empresa_id, nome, local, data_inicio, data_fim, cep=None, endereco=None, numero=None, bairro=None, cidade=None, estado=None):
    """Cria um novo evento vinculado à empresa com endereço completo."""
    ensure_event_address_columns()
    query = """
        INSERT INTO eventos (empresa_id, nome, local, data_inicio, data_fim, cep, endereco, numero, bairro, cidade, estado, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ATIVO')
        RETURNING id;
    """
    res = execute_query(
        query, 
        (empresa_id, nome, local, data_inicio, data_fim, cep, endereco, numero, bairro, cidade, estado), 
        fetch_one=True, 
        commit=True
    )
    return res is not None

def get_company_events(empresa_id):
    """Retorna todos os eventos cadastrados para a empresa."""
    ensure_event_address_columns()
    query = """
        SELECT id, nome, local, data_inicio, data_fim, status, cep, endereco, numero, bairro, cidade, estado
        FROM eventos
        WHERE empresa_id = %s
        ORDER BY data_inicio DESC;
    """
    return execute_query(query, (empresa_id,), fetch_all=True) or []