import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING
)
from services.user_service import get_all_staff, update_user_status

def AdminEquipeView(page: ft.Page, on_back):
    selected_status = "TODOS"
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def get_status_color(status):
        if status == "APROVADO": return COLOR_SUCCESS
        if status == "PENDENTE": return COLOR_WARNING
        return COLOR_ERROR

    def reload_staff_list():
        list_container.controls.clear()
        staff_members = get_all_staff(selected_status)

        if not staff_members:
            list_container.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhum colaborador encontrado nesta categoria.", color=COLOR_TEXT_SECONDARY)
                )
            )
        else:
            for user in staff_members:
                u_id = user['id']
                u_status = user['status']
                
                actions = []
                if u_status == "PENDENTE":
                    actions.extend([
                        ft.Button(
                            "Aprovar",
                            style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"),
                            on_click=lambda _, uid=u_id: change_status(uid, "APROVADO")
                        ),
                        ft.Button(
                            "Recusar",
                            style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color="#FFFFFF"),
                            on_click=lambda _, uid=u_id: change_status(uid, "RECUSADO")
                        )
                    ])
                elif u_status == "APROVADO":
                    actions.append(
                        ft.OutlinedButton(
                            "Bloquear",
                            style=ft.ButtonStyle(color=COLOR_ERROR),
                            on_click=lambda _, uid=u_id: change_status(uid, "BLOQUEADO")
                        )
                    )
                else:
                    actions.append(
                        ft.OutlinedButton(
                            "Reativar",
                            style=ft.ButtonStyle(color=COLOR_SUCCESS),
                            on_click=lambda _, uid=u_id: change_status(uid, "APROVADO")
                        )
                    )

                card = ft.Container(
                    bgcolor=COLOR_SURFACE,
                    padding=15,
                    border_radius=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Row(controls=[
                                        ft.Text(user['nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                                        ft.Container(
                                            content=ft.Text(u_status, size=11, color="#000000", weight=ft.FontWeight.BOLD),
                                            bgcolor=get_status_color(u_status),
                                            padding=6,
                                            border_radius=10
                                        )
                                    ]),
                                    ft.Text(f"Função: {user['funcao_principal']} | CPF: {user['cpf']}", size=13, color=COLOR_TEXT_SECONDARY),
                                    ft.Text(f"Contato: {user['whatsapp']} | Cidade: {user['cidade']}/{user['estado']}", size=12, color=COLOR_TEXT_SECONDARY),
                                    ft.Text(f"Pix: {user['chave_pix']} | Experiência: {user['experiencia']}", size=12, color=COLOR_TEXT_SECONDARY),
                                ]
                            ),
                            ft.Row(controls=actions, spacing=8)
                        ]
                    )
                )
                list_container.controls.append(card)
        page.update()

    def change_status(user_id, new_status):
        if update_user_status(user_id, new_status):
            reload_staff_list()

    def filter_changed(e):
        nonlocal selected_status
        selected_status = filter_dropdown.value
        reload_staff_list()

    filter_dropdown = ft.Dropdown(
        value="TODOS",
        width=180,
        options=[
            ft.dropdown.Option("TODOS"),
            ft.dropdown.Option("PENDENTE"),
            ft.dropdown.Option("APROVADO"),
            ft.dropdown.Option("RECUSADO"),
            ft.dropdown.Option("BLOQUEADO"),
        ]
    )
    filter_dropdown.on_change = filter_changed

    reload_staff_list()

    return ft.Container(
        expand=True,
        padding=25,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                            ft.Text("Gestão de Colaboradores", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                        ]),
                        filter_dropdown
                    ]
                ),
                list_container
            ]
        )
    )