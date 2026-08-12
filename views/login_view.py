import flet as ft
import bcrypt
import threading

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query

def LoginView(page: ft.Page, on_login_success=None, on_navigate_register=None):
    txt_email = ft.TextField(
        label="E-mail",
        width=320,
        text_size=14,
        autofocus=True
    )
    
    txt_senha = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        width=320,
        text_size=14
    )

    btn_entrar = ft.ElevatedButton(
        content=ft.Text("Entrar", size=16, weight="bold"),
        style=ft.ButtonStyle(bgcolor="#4CC9F0", color="white"),
        width=320,
        height=45
    )

    def processar_login():
        email_val = txt_email.value.strip()
        senha_val = txt_senha.value.strip()

        try:
            query = "SELECT id, nome, email, senha, perfil, empresa_id FROM usuarios WHERE email = %s LIMIT 1;"
            usuarios = execute_query(query, (email_val,), fetch_all=True)

            if not usuarios:
                restaurar_botao()
                show_snack("E-mail ou senha incorretos.")
                return

            usuario = usuarios[0]
            senha_hash_db = usuario.get('senha', '')

            senha_valida = False
            if senha_hash_db.startswith('$2b$') or senha_hash_db.startswith('$2a$'):
                senha_valida = bcrypt.checkpw(senha_val.encode('utf-8'), senha_hash_db.encode('utf-8'))
            else:
                senha_valida = (senha_val == senha_hash_db)

            if senha_valida:
                if on_login_success:
                    on_login_success(usuario)
            else:
                restaurar_botao()
                show_snack("E-mail ou senha incorretos.")

        except Exception as ex:
            restaurar_botao()
            show_snack(f"Erro ao conectar: {ex}")

    def handle_login(e):
        email_val = txt_email.value.strip()
        senha_val = txt_senha.value.strip()

        if not email_val or not senha_val:
            show_snack("Preencha e-mail e senha!")
            return

        btn_entrar.disabled = True
        btn_entrar.content = ft.Row(
            [
                ft.ProgressRing(width=20, height=20, stroke_width=2, color="white"),
                ft.Text("Acessando...", size=14, weight="bold")
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        page.update()

        threading.Thread(target=processar_login, daemon=True).start()

    def restaurar_botao():
        btn_entrar.disabled = False
        btn_entrar.content = ft.Text("Entrar", size=16, weight="bold")
        page.update()

    def show_snack(msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#E76F51")
        page.overlay.append(snack)
        snack.open = True
        page.update()

    btn_entrar.on_click = handle_login

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Event Casting", size=28, weight="bold", color="#4CC9F0"),
                ft.Text("Acesse sua conta para continuar", size=14, color="#94A3B8"),
                ft.Container(height=10),
                txt_email,
                txt_senha,
                ft.Container(height=10),
                btn_entrar,
                ft.TextButton(
                    "Cadastrar Minha Empresa / Produtora",
                    style=ft.ButtonStyle(color="#2A9D8F"),
                    on_click=lambda _: on_navigate_register() if on_navigate_register else None
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        ),
        expand=True,
        alignment=ft.Alignment(0, 0),
        bgcolor="#0B132B"
    )