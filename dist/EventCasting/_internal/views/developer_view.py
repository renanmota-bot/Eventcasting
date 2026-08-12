import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
)
from services.developer_service import get_all_companies, create_company, get_all_users_global, toggle_user_status

def DeveloperView(page: ft.Page, on_back):
    active_tab = "empresas"

    txt_nome_fantasia = ft.TextField(
        label="Nome Fantasia", 
        border_color=COLOR_TEXT_SECONDARY, 
        text_size=14,
        color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_razao_social = ft.TextField(
        label="Razão Social", 
        border_color=COLOR_TEXT_SECONDARY, 
        text_size=14,
        color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_cnpj = ft.TextField(
        label="CNPJ", 
        border_color=COLOR_TEXT_SECONDARY, 
        text_size=14,
        color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    
    list_empresas = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    list_usuarios = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    content_area = ft.Container(expand=True)

    def reload_companies():
        list_empresas.controls.clear()
        companies = get_all_companies()
        for comp in companies:
            card = ft.Container(
                bgcolor=COLOR_SURFACE,
                padding=12,
                border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=2, controls=[
                            ft.Text(f"#{comp['id']} - {comp['nome_fantasia']}", weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                            ft.Text(f"CNPJ: {comp['cnpj']} | Status: {comp['status']}", size=12, color=COLOR_TEXT_SECONDARY)
                        ]),
                        ft.Container(
                            content=ft.Text(comp['status'], size=10, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                            bgcolor=COLOR_SUCCESS if comp['status'] == 'ATIVO' else COLOR_ERROR,
                            padding=6, border_radius=6
                        )
                    ]
                )
            )
            list_empresas.controls.append(card)

    def reload_users():
        list_usuarios.controls.clear()
        users = get_all_users_global()
        for u in users:
            card = ft.Container(
                bgcolor=COLOR_SURFACE,
                padding=12,
                border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=2, controls=[
                            ft.Text(f"{u['nome']} ({u['perfil']})", weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                            ft.Text(f"E-mail: {u['email']} | Empresa: {u['empresa_nome'] or 'Nenhuma'}", size=12, color=COLOR_TEXT_SECONDARY)
                        ]),
                        ft.ElevatedButton(
                            "Bloquear" if u['status'] == 'ATIVO' else "Ativar",
                            style=ft.ButtonStyle(
                                bgcolor=COLOR_ERROR if u['status'] == 'ATIVO' else COLOR_SUCCESS, 
                                color="#FFFFFF"
                            ),
                            on_click=lambda _, uid=u['id'], st=u['status']: handle_toggle_user(uid, st)
                        )
                    ]
                )
            )
            list_usuarios.controls.append(card)

    def handle_add_company(_):
        if not txt_nome_fantasia.value.strip():
            return
        create_company(txt_nome_fantasia.value.strip(), txt_razao_social.value.strip(), txt_cnpj.value.strip())
        txt_nome_fantasia.value = ""
        txt_razao_social.value = ""
        txt_cnpj.value = ""
        reload_companies()
        render_tab()

    def handle_toggle_user(uid, current_status):
        toggle_user_status(uid, current_status)
        reload_users()
        render_tab()

    def set_tab(tab_name):
        nonlocal active_tab
        active_tab = tab_name
        render_tab()

    def render_tab():
        if active_tab == "empresas":
            btn_tab_empresas.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000")
            btn_tab_usuarios.style = ft.ButtonStyle(bgcolor=COLOR_SURFACE, color=COLOR_TEXT_PRIMARY)
            content_area.content = ft.Column(
                expand=True,
                spacing=15,
                controls=[
                    ft.Container(
                        bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                        content=ft.Column(controls=[
                            ft.Text("Cadastrar Nova Empresa", weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                            txt_nome_fantasia, txt_razao_social, txt_cnpj,
                            ft.ElevatedButton(
                                "Criar Empresa", 
                                icon=ft.Icons.ADD, 
                                style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), 
                                on_click=handle_add_company
                            )
                        ])
                    ),
                    list_empresas
                ]
            )
        else:
            btn_tab_empresas.style = ft.ButtonStyle(bgcolor=COLOR_SURFACE, color=COLOR_TEXT_PRIMARY)
            btn_tab_usuarios.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000")
            content_area.content = list_usuarios
        
        page.update()

    btn_tab_empresas = ft.ElevatedButton("Empresas (Tenants)", on_click=lambda _: set_tab("empresas"))
    btn_tab_usuarios = ft.ElevatedButton("Todos os Usuários", on_click=lambda _: set_tab("usuarios"))

    reload_companies()
    reload_users()
    render_tab()

    return ft.Container(
        expand=True,
        padding=25,
        content=ft.Column(
            expand=True,
            spacing=15,
            controls=[
                ft.Row(controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                    ft.Text("Painel do Desenvolvedor (Super Admin)", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
                ]),
                ft.Row(controls=[btn_tab_empresas, btn_tab_usuarios], spacing=10),
                content_area
            ]
        )
    )