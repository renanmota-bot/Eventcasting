import flet as ft

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query

def SuperAdminDashboardView(page: ft.Page, user=None, on_logout=None):
    
    def carregar_empresas(filtro=""):
        tabela_empresas.rows.clear()
        query = """
            SELECT id, nome_fantasia, razao_social, cnpj, COALESCE(ativa, true) as ativa 
            FROM empresas 
            WHERE nome_fantasia ILIKE %s OR cnpj ILIKE %s OR razao_social ILIKE %s
            ORDER BY id DESC;
        """
        param = f"%{filtro}%"
        empresas = execute_query(query, (param, param, param), fetch_all=True) or []

        for emp in empresas:
            is_ativa = emp.get('ativa', True)
            tabela_empresas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(emp.get('id', '')))),
                        ft.DataCell(ft.Text(emp.get('nome_fantasia') or emp.get('razao_social') or "Sem Nome", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(emp.get('cnpj') or "N/A")),
                        ft.DataCell(
                            ft.Text("Ativa" if is_ativa else "Bloqueada", color="#2A9D8F" if is_ativa else "#E76F51")
                        ),
                        ft.DataCell(
                            ft.IconButton(
                                icon="block" if is_ativa else "check_circle",
                                icon_color="#E76F51" if is_ativa else "#2A9D8F",
                                on_click=lambda e, eid=emp['id'], st=is_ativa: alternar_status(eid, st)
                            )
                        )
                    ]
                )
            )
        page.update()

    def alternar_status(emp_id, status_atual):
        execute_query("UPDATE empresas SET ativa = %s WHERE id = %s;", (not status_atual, emp_id), commit=True)
        carregar_empresas(busca_empresa.value or "")

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
                        ft.DataCell(ft.Text(str(usr.get('id', '')))),
                        ft.DataCell(ft.Text(usr.get('nome') or "Sem Nome", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(usr.get('email') or "N/A")),
                        ft.DataCell(ft.Chip(label=ft.Text(usr.get('perfil') or "STAFF"))),
                        ft.DataCell(
                            ft.IconButton(
                                icon="delete",
                                icon_color="#E76F51",
                                on_click=lambda e, uid=usr['id']: deletar_usr(uid)
                            )
                        )
                    ]
                )
            )
        page.update()

    def deletar_usr(uid):
        execute_query("DELETE FROM usuarios WHERE id = %s;", (uid,), commit=True)
        carregar_usuarios(busca_usuario.value or "")

    tabela_empresas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nome / Razão")),
            ft.DataColumn(ft.Text("CNPJ")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Ações")),
        ], rows=[]
    )

    tabela_usuarios = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nome")),
            ft.DataColumn(ft.Text("E-mail")),
            ft.DataColumn(ft.Text("Perfil")),
            ft.DataColumn(ft.Text("Ações")),
        ], rows=[]
    )

    busca_empresa = ft.TextField(hint_text="Filtrar Empresas por Nome ou CNPJ...", on_change=lambda e: carregar_empresas(e.control.value), expand=True)
    busca_usuario = ft.TextField(hint_text="Filtrar Usuários por Nome ou Email...", on_change=lambda e: carregar_usuarios(e.control.value), expand=True)

    carregar_empresas()
    carregar_usuarios()

    tab1 = ft.Tab()
    tab1.text = "Empresas (Tenants)"
    tab1.icon = "business"
    tab1.content = ft.Column([busca_empresa, ft.Column([tabela_empresas], scroll=ft.ScrollMode.AUTO)])

    tab2 = ft.Tab()
    tab2.text = "Usuários Globais"
    tab2.icon = "people"
    tab2.content = ft.Column([busca_usuario, ft.Column([tabela_usuarios], scroll=ft.ScrollMode.AUTO)])

    tabs = ft.Tabs(
        selected_index=0,
        expand=True
    )
    tabs.tabs = [tab1, tab2]

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Painel Master — Controle Total do SaaS", size=22, weight="bold", color="white"),
                ft.ElevatedButton("Sair", icon="logout", on_click=lambda e: on_logout() if on_logout else None)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            tabs
        ], spacing=20),
        padding=20, expand=True, bgcolor="#0B132B"
    )