import flet as ft
from database.connection import execute_query

def SuperAdminDashboardView(page: ft.Page, user=None, on_logout=None):
    
    # --- CONSULTAS AO BANCO DE DADOS (POSTGRESQL) ---
    def buscar_metricas():
        q_empresas = "SELECT COUNT(*) as total FROM empresas;"
        q_usuarios = "SELECT COUNT(*) as total FROM usuarios;"
        q_eventos = "SELECT COUNT(*) as total FROM eventos;" # Ajuste o nome da tabela se for diferente
        
        tot_emp = execute_query(q_empresas, fetch_one=True) or {'total': 0}
        tot_usr = execute_query(q_usuarios, fetch_one=True) or {'total': 0}
        tot_evt = execute_query(q_eventos, fetch_one=True) or {'total': 0}
        
        return tot_emp['total'], tot_usr['total'], tot_evt['total']

    # --- COMPONENTES DE EMPRESAS ---
    tabela_empresas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color="#8D99AE")),
            ft.DataColumn(ft.Text("Razão Social / Nome", color="#8D99AE")),
            ft.DataColumn(ft.Text("CNPJ", color="#8D99AE")),
            ft.DataColumn(ft.Text("Status", color="#8D99AE")),
            ft.DataColumn(ft.Text("Ações", color="#8D99AE")),
        ],
        rows=[]
    )

    def alternar_status_empresa(emp_id, status_atual):
        novo_status = False if status_atual else True
        query = "UPDATE empresas SET ativa = %s WHERE id = %s;"
        execute_query(query, (novo_status, emp_id), commit=True)
        carregar_empresas(busca_empresa.value or "")

    def carregar_empresas(filtro=""):
        tabela_empresas.rows.clear()
        query = """
            SELECT id, nome_fantasia, razao_social, cnpj, COALESCE(ativa, true) as ativa 
            FROM empresas 
            WHERE nome_fantasia ILIKE %s OR razao_social ILIKE %s OR cnpj ILIKE %s
            ORDER BY id DESC;
        """
        param = f"%{filtro}%"
        empresas = execute_query(query, (param, param, param), fetch_all=True) or []

        for emp in empresas:
            is_ativa = emp.get('ativa', True)
            tabela_empresas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(emp['id']))),
                        ft.DataCell(ft.Text(emp.get('nome_fantasia') or emp.get('razao_social') or "Sem Nome", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(emp.get('cnpj') or "N/A")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text("Ativa" if is_ativa else "Bloqueada", color="white", size=12),
                                bgcolor="#2A9D8F" if is_ativa else "#E76F51",
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                border_radius=10
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    ft.icons.BLOCK if is_ativa else ft.icons.CHECK_CIRCLE,
                                    tooltip="Bloquear/Ativar",
                                    icon_color="#E76F51" if is_ativa else "#2A9D8F",
                                    on_click=lambda e, eid=emp['id'], st=is_ativa: alternar_status_empresa(eid, st)
                                )
                            ])
                        )
                    ]
                )
            )
        page.update()

    busca_empresa = ft.TextField(
        hint_text="Buscar por Nome ou CNPJ...",
        prefix_icon=ft.icons.SEARCH,
        bgcolor="#1C2541",
        border_color="#3A506B",
        on_change=lambda e: carregar_empresas(e.control.value),
        expand=True
    )

    # --- COMPONENTES DE USUÁRIOS ---
    tabela_usuarios = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color="#8D99AE")),
            ft.DataColumn(ft.Text("Nome", color="#8D99AE")),
            ft.DataColumn(ft.Text("E-mail", color="#8D99AE")),
            ft.DataColumn(ft.Text("Perfil", color="#8D99AE")),
            ft.DataColumn(ft.Text("Ações", color="#8D99AE")),
        ],
        rows=[]
    )

    def deletar_usuario(usr_id):
        query = "DELETE FROM usuarios WHERE id = %s;"
        execute_query(query, (usr_id,), commit=True)
        carregar_usuarios(busca_usuario.value or "")

    def carregar_usuarios(filtro=""):
        tabela_usuarios.rows.clear()
        query = """
            SELECT id, nome, email, perfil 
            FROM usuarios 
            WHERE nome ILIKE %s OR email ILIKE %s
            ORDER BY id DESC;
        """
        param = f"%{filtro}%"
        usuarios = execute_query(query, (param, param), fetch_all=True) or []

        for usr in usuarios:
            tabela_usuarios.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(usr['id']))),
                        ft.DataCell(ft.Text(usr.get('nome') or "Sem Nome", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(usr.get('email') or "N/A")),
                        ft.DataCell(ft.Chip(label=ft.Text(usr.get('perfil') or "STAFF"))),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    ft.icons.DELETE_FOREVER,
                                    tooltip="Excluir Usuário",
                                    icon_color="#E76F51",
                                    on_click=lambda e, uid=usr['id']: deletar_usuario(uid)
                                )
                            ])
                        )
                    ]
                )
            )
        page.update()

    busca_usuario = ft.TextField(
        hint_text="Buscar usuário por Nome ou E-mail...",
        prefix_icon=ft.icons.SEARCH,
        bgcolor="#1C2541",
        border_color="#3A506B",
        on_change=lambda e: carregar_usuarios(e.control.value),
        expand=True
    )

    # Carga Inicial de Dados
    tot_emp, tot_usr, tot_evt = buscar_metricas()
    carregar_empresas()
    carregar_usuarios()

    # --- MÉTRICAS VISUAIS ---
    cards_metricas = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("Empresas Cadastradas", color="#8D99AE", size=12),
                ft.Text(str(tot_emp), color="white", size=24, weight="bold")
            ]),
            bgcolor="#1C2541", padding=15, border_radius=10, expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Usuários Globais", color="#8D99AE", size=12),
                ft.Text(str(tot_usr), color="white", size=24, weight="bold")
            ]),
            bgcolor="#1C2541", padding=15, border_radius=10, expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Eventos Criados", color="#8D99AE", size=12),
                ft.Text(str(tot_evt), color="white", size=24, weight="bold")
            ]),
            bgcolor="#1C2541", padding=15, border_radius=10, expand=True
        ),
    ], spacing=15)

    # --- ESTRUTURA PRINCIPAL COM ABAS ---
    aba_empresas = ft.Column([
        ft.Row([busca_empresa]),
        ft.Column([tabela_empresas], scroll=ft.ScrollMode.AUTO, expand=True)
    ], spacing=15)

    aba_usuarios = ft.Column([
        ft.Row([busca_usuario]),
        ft.Column([tabela_usuarios], scroll=ft.ScrollMode.AUTO, expand=True)
    ], spacing=15)

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Empresas / Tenants", icon=ft.icons.BUSINESS, content=aba_empresas),
            ft.Tab(text="Usuários do Sistema", icon=ft.icons.PEOPLE, content=aba_usuarios),
        ],
        expand=True
    )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Painel do Desenvolvedor (Super Admin)", size=22, weight="bold", color="white"),
                ft.ElevatedButton("Sair / Logout", icon=ft.icons.LOGOUT, on_click=lambda e: on_logout() if on_logout else None)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            cards_metricas,
            ft.Divider(color="#3A506B"),
            tabs
        ], spacing=20),
        padding=25,
        expand=True,
        bgcolor="#0B132B"
    )