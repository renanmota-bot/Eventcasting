import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
)
from services.auth_service import authenticate_user

def LoginView(page: ft.Page, on_login_success, on_navigate_register):
    txt_email = ft.TextField(
        label="E-mail", 
        border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, 
        color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_senha = ft.TextField(
        label="Senha", 
        password=True, 
        can_reveal_password=True,
        border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, 
        color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )

    def handle_login(_):
        email = txt_email.value.strip() if txt_email.value else ""
        senha = txt_senha.value.strip() if txt_senha.value else ""

        if not email or not senha:
            show_snack("Preencha e-mail e senha.")
            return

        user = authenticate_user(email, senha)
        if user:
            show_snack(f"Bem-vindo, {user.get('nome')}!", is_error=False)
            on_login_success(user)
        else:
            show_snack("E-mail ou senha incorretos / Conta inativa.")

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=COLOR_ERROR if is_error else COLOR_SUCCESS
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    return ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=380,
            bgcolor=COLOR_SURFACE,
            padding=35,
            border_radius=12,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
                tight=True,
                controls=[
                    ft.Text("EVENT CASTING", size=24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                    ft.Text("Gestão de Equipes e Eventos", size=13, color=COLOR_TEXT_SECONDARY),
                    ft.Divider(color="#334155"),
                    txt_email,
                    txt_senha,
                    ft.ElevatedButton(
                        "Entrar",
                        style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"),
                        width=320,
                        on_click=handle_login
                    ),
                    ft.TextButton(
                        "Cadastrar Empresa / Produtora",
                        style=ft.ButtonStyle(color=COLOR_PRIMARY),
                        on_click=lambda _: on_navigate_register()
                    )
                ]
            )
        )
    )