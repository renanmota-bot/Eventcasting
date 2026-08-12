from database.database import execute_query

def get_saas_metrics_summary():
    """Calcula e retorna todas as métricas gerenciais do SaaS em tempo real."""
    query_empresas = """
        SELECT 
            COUNT(*) AS total_empresas,
            COUNT(CASE WHEN status = 'ATIVO' THEN 1 END) AS ativas,
            COUNT(CASE WHEN status = 'SUSPENSO' THEN 1 END) AS suspensas,
            COUNT(CASE WHEN status = 'PENDENTE' THEN 1 END) AS pendentes
        FROM empresas;
    """
    res_emp = execute_query(query_empresas, fetch_one=True) or {}

    query_financeiro = """
        SELECT 
            COALESCE(SUM(valor), 0) AS faturamento_total,
            COUNT(CASE WHEN status = 'PAGO' THEN 1 END) AS assinaturas_pagas,
            COALESCE(SUM(CASE WHEN data_criacao >= DATE_TRUNC('month', CURRENT_DATE) AND status = 'PAGO' THEN valor ELSE 0 END), 0) AS faturamento_mes_atual
        FROM assinaturas;
    """
    res_fin = execute_query(query_financeiro, fetch_one=True) or {}

    query_uso = """
        SELECT 
            (SELECT COUNT(*) FROM eventos) AS total_eventos,
            (SELECT COUNT(*) FROM vagas) AS total_vagas,
            (SELECT COUNT(*) FROM candidaturas) AS total_candidaturas,
            (SELECT COUNT(*) FROM usuarios WHERE perfil = 'STAFF') AS total_staffs;
    """
    res_uso = execute_query(query_uso, fetch_one=True) or {}

    return {
        "total_empresas": res_emp.get("total_empresas", 0),
        "empresas_ativas": res_emp.get("ativas", 0),
        "empresas_suspensas": res_emp.get("suspensas", 0),
        "empresas_pendentes": res_emp.get("pendentes", 0),
        "faturamento_total": float(res_fin.get("faturamento_total", 0.0)),
        "faturamento_mes_atual": float(res_fin.get("faturamento_mes_atual", 0.0)),
        "assinaturas_pagas": res_fin.get("assinaturas_pagas", 0),
        "total_eventos": res_uso.get("total_eventos", 0),
        "total_vagas": res_uso.get("total_vagas", 0),
        "total_candidaturas": res_uso.get("total_candidaturas", 0),
        "total_staffs": res_uso.get("total_staffs", 0)
    }

def get_companies_list_for_saas():
    """Retorna a lista detalhada de produtoras/empresas cadastradas para o Super Admin."""
    query = """
        SELECT 
            e.id, 
            e.nome_fantasia, 
            e.cnpj, 
            e.status, 
            e.data_criacao,
            COUNT(DISTINCT ev.id) AS total_eventos,
            COUNT(DISTINCT u.id) AS total_usuarios
        FROM empresas e
        LEFT JOIN eventos ev ON e.id = ev.empresa_id
        LEFT JOIN usuarios u ON e.id = u.empresa_id
        GROUP BY e.id, e.nome_fantasia, e.cnpj, e.status, e.data_criacao
        ORDER BY e.id DESC;
    """
    return execute_query(query, fetch_all=True) or []

def create_company_by_dev(nome_fantasia, cnpj, email_admin, senha_admin):
    """Cria uma nova empresa e seu usuário Admin já ativados pelo Dev."""
    query_emp = """
        INSERT INTO empresas (nome_fantasia, cnpj, status)
        VALUES (%s, %s, 'ATIVO')
        RETURNING id;
    """
    res_emp = execute_query(query_emp, (nome_fantasia, cnpj), fetch_one=True, commit=True)
    if not res_emp:
        return False, "Erro ao criar registro da empresa."

    empresa_id = res_emp['id']

    query_user = """
        INSERT INTO usuarios (empresa_id, nome, email, senha, perfil, status)
        VALUES (%s, %s, %s, %s, 'ADMIN', 'ATIVO');
    """
    execute_query(query_user, (empresa_id, f"Admin {nome_fantasia}", email_admin, senha_admin), commit=True)
    return True, "Empresa e Admin cadastrados e ativados com sucesso!"

def update_company_status(empresa_id, novo_status):
    """Altera o status da empresa (ATIVO, SUSPENSO, PENDENTE)."""
    query = "UPDATE empresas SET status = %s WHERE id = %s;"
    return execute_query(query, (novo_status, empresa_id), commit=True)

def delete_company_completely(empresa_id):
    """Remove completamente a empresa do banco de dados e todos os dados vinculados."""
    query = "DELETE FROM empresas WHERE id = %s;"
    return execute_query(query, (empresa_id,), commit=True)
