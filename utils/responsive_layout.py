import flet as ft

def MobileAppLayout(content, max_width=420, padding=15, bgcolor="#0B132B"):
    """
    Transforma qualquer View em um layout responsivo estilo App Mobile:
    - No celular: ocupa 100% da largura com rolagem suave.
    - No computador/tablet: centraliza a tela com limite de largura elegante (max_width).
    """
    return ft.Container(
        expand=True,
        bgcolor=bgcolor,
        alignment=ft.Alignment(0, 0),
        padding=padding,
        content=ft.Container(
            max_width=max_width,
            expand=True,
            content=ft.Column(
                controls=[content],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        )
    )
