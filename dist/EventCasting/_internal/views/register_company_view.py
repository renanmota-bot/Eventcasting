import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
)
from database.database import execute_query
from utils.validators import is_valid_email, is_strong_password

def register_company_and_admin(nome_fantasia, cnpj, nome_admin, email, senha):
    """Cria a empresa e o primeiro usuário ADMIN vinculado a ela."""
    # Garante a tabela de empresas
    query_emp = """
        CREATE TABLE IF NOT EXISTS empresas (
            id SERIAL PRIMARY KEY,
            nome_fantasia VARCHAR(150) NOT NULL,
            cnpj VARCHAR(20),
            status VARCHAR(20) DEFAULT 'PENDENTE',
            data_criacao TIMESTAMP DEFAULT NOW()
        );
    """
    execute_query(query_emp, commit=True)

    # Insere a Empresa
    insert_emp = """
        INSERT INTO empresas (nome_fantasia, cnpj, status)
        VALUES (%s, %s, 'PENDENTE')
        RETURNING id;
    """
    emp_res = execute_query(insert_emp, (nome_fantasia, cnpj), fetch_one=True, commit=True)
    if not emp_res:
        return None

    empresa_id = emp_res['id']

    # Insere o Admin da Empresa
    insert_user = """
        INSERT INTO usuarios (empresa_id, nome, email, senha, perfil, status)
        VALUES (%s, %s, %s, %s, 'ADMIN', 'ATIVO')
        RETURNING id, empresa_id, nome, email, perfil;
    """
    user_res = execute_query(insert_user, (empresa_id, nome_admin, email, senha), fetch_one=True, commit=True)
    return user_res

def RegisterCompanyView(page: ft.Page, on_back, on_registered_success):
    txt_nome_empresa = ft.TextField(
        label="Nome Fantasia da Empresa / Produtora", 
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, 
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_cnpj = ft.TextField(
        label="CNPJ / CPF do Responsável", 
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, 
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_nome_admin = ft.TextField(
        label="Seu Nome Completo (Administrador)", 
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, 
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_email = ft.TextField(
        label="E-mail de Acesso", 
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, 
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_senha = ft.TextField(
        label="Senha de Acesso", password=True, can_reveal_password=True, 
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, 
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )

    def handle_submit(_):
        emp_nome = (txt_nome_empresa.value or "").strip()
        admin_nome = (txt_nome_admin.value or "").strip()
        email_val = (txt_email.value or "").strip()
        senha_val = (txt_senha.value or "").strip()

        if not all([emp_nome, admin_nome, email_val, senha_val]):
            show_snack("Preencha todos os campos do cadastro da empresa.")
            return

        if not is_valid_email(email_val):
            show_snack("E-mail com formato inválido.")
            return

        is_strong, msg_senha = is_strong_password(senha_val)
        if not is_strong:
            show_snack(msg_senha)
            return

        user_created = register_company_and_admin(
            nome_fantasia=emp_nome,
            cnpj=txt_cnpj.value.strip() if txt_cnpj.value else "",
            nome_admin=admin_nome,
            email=email_val,
            senha=senha_val
        )

        if user_created:
            show_snack("Empresa cadastrada! Redirecionando para o pagamento do plano...", is_error=False)
            on_registered_success(user_created)
        else:
            show_snack("Erro ao cadastrar empresa ou e-mail já existente.")

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=COLOR_ERROR if is_error else COLOR_SUCCESS)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    return ft.Container(
        expand=True, alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=440, bgcolor=COLOR_SURFACE, padding=30, border_radius=12,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12, scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(controls=[
                        ft.IconButton(ft.Icons.ARROW_BACK, icon_color=COLOR_TEXT_PRIMARY, on_click=lambda _: on_back()),
                        ft.Text("Cadastrar Produtora (Empresa)", size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
                    ]),
                    ft.Text("Crie sua conta de produtora para publicar vagas e gerenciar casting.", size=12, color=COLOR_TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                    ft.Divider(color="#334155"),
                    txt_nome_empresa, txt_cnpj, txt_nome_admin, txt_email, txt_senha,
                    ft.Container(height=10),
                    ft.ElevatedButton("Cadastrar e Ir Para Pagamento (R$ 100/mês)", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), width=380, on_click=handle_submit)
                ]
            )
        )
    )
