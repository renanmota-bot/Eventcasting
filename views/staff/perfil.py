import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR
)
from utils.formatters import date_to_br

def StaffPerfilView(page: ft.Page, user: dict, on_back):
    def get_status_color(status):
        if status == "APROVADO": return COLOR_SUCCESS
        if status == "PENDENTE": return COLOR_WARNING
        return COLOR_ERROR

    return ft.Container(
        expand=True,
        padding=25,
        alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=550,
            padding=25,
            bgcolor=COLOR_SURFACE,
            border_radius=12,
            content=ft.Column(
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(controls=[
                        ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                        ft.Text("Meu Perfil", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
                    ]),
                    ft.Divider(height=1, color="#334155"),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(controls=[
                                ft.Text(user['nome'], size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                                ft.Text(f"Função: {user['funcao_principal']}", size=14, color=COLOR_PRIMARY)
                            ]),
                            ft.Container(
                                content=ft.Text(user['status'], size=12, color="#000000", weight=ft.FontWeight.BOLD),
                                bgcolor=get_status_color(user['status']),
                                padding=8,
                                border_radius=12
                            )
                        ]
                    ),
                    ft.Divider(height=1, color="#334155"),
                    ft.Text("Dados Pessoais", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                    ft.Text(f"CPF: {user['cpf']}", size=13, color=COLOR_TEXT_SECONDARY),
                    ft.Text(f"Data de Nascimento: {date_to_br(user.get('data_nascimento'))}", size=13, color=COLOR_TEXT_SECONDARY),
                    ft.Text(f"E-mail: {user['email']}", size=13, color=COLOR_TEXT_SECONDARY),
                    ft.Text(f"WhatsApp: {user['whatsapp']}", size=13, color=COLOR_TEXT_SECONDARY),
                    ft.Text(f"Cidade/Estado: {user['cidade']} - {user['estado']}", size=13, color=COLOR_TEXT_SECONDARY),
                    ft.Divider(height=1, color="#334155"),
                    ft.Text("Dados Profissionais e Pagamento", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                    ft.Text(f"Experiência: {user['experiencia'] or 'Não informada'}", size=13, color=COLOR_TEXT_SECONDARY),
                    ft.Text(f"Chave Pix: {user['chave_pix'] or 'Não informada'}", size=13, color=COLOR_TEXT_SECONDARY),
                ]
            )
        )
    )