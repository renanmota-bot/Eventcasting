import flet as ft
import base64

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query

def RegisterView(page: ft.Page, on_back=None, default_empresa_id=1):
    doc_base64 = [None]

    txt_nome = ft.TextField(label="Nome Completo *", text_size=13, border_radius=8)
    txt_email = ft.TextField(label="E-mail *", text_size=13, border_radius=8)
    txt_senha = ft.TextField(label="Senha *", password=True, can_reveal_password=True, text_size=13, border_radius=8)
    txt_cpf = ft.TextField(label="CPF (Obrigatório) *", text_size=13, border_radius=8)
    txt_rg = ft.TextField(label="RG (Obrigatório) *", text_size=13, border_radius=8)
    txt_whatsapp = ft.TextField(label="WhatsApp *", text_size=13, border_radius=8)

    lbl_doc_status = ft.Text("Nenhum documento anexado", size=12, color="#E76F51", weight="bold")

    def handle_file_picker_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_picked = e.files[0]
            try:
                # Caso esteja executando via Web ou Local com caminho do arquivo
                if file_picked.path:
                    with open(file_picked.path, "rb") as f:
                        doc_base64[0] = base64.b64encode(f.read()).decode('utf-8')
                lbl_doc_status.value = f"✓ Documento anexado: {file_picked.name}"
                lbl_doc_status.color = "#2A9D8F"
                page.update()
            except Exception as ex:
                show_snack(f"Erro ao ler arquivo: {ex}")

    file_picker = ft.FilePicker(on_result=handle_file_picker_result)
    page.overlay.append(file_picker)

    btn_anexar_doc = ft.ElevatedButton(
        "Anexar Foto do RG/CPF (Obrigatório)",
        icon=ft.Icons.UPLOAD_FILE,
        style=ft.ButtonStyle(bgcolor="#1E293B", color="#4CC9F0"),
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg", "pdf"])
    )

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#E76F51" if is_error else "#2A9D8F")
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def handle_cadastrar(e):
        nome_val = txt_nome.value.strip() if txt_nome.value else ""
        email_val = txt_email.value.strip() if txt_email.value else ""
        senha_val = txt_senha.value.strip() if txt_senha.value else ""
        cpf_val = txt_cpf.value.strip() if txt_cpf.value else ""
        rg_val = txt_rg.value.strip() if txt_rg.value else ""
        whatsapp_val = txt_whatsapp.value.strip() if txt_whatsapp.value else ""

        # Trava os campos obrigatórios
        if not all([nome_val, email_val, senha_val, cpf_val, rg_val, whatsapp_val]):
            show_snack("Todos os campos de texto (incluindo RG e CPF) são obrigatórios!")
            return

        if not doc_base64[0]:
            show_snack("É OBRIGATÓRIO anexar o documento (RG/CPF) em foto ou PDF!")
            return

        try:
            # Garante que a tabela tem as colunas rg e documento_base64
            query_insert = """
                INSERT INTO usuarios (empresa_id, nome, email, senha, cpf, rg, whatsapp, foto_base64, perfil, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'STAFF', 'ATIVO');
            """
            execute_query(
                query_insert, 
                (default_empresa_id, nome_val, email_val, senha_val, cpf_val, rg_val, whatsapp_val, doc_base64[0])
            )
            show_snack("Cadastro de Staff realizado com sucesso!", is_error=False)
            if on_back:
                on_back()
        except Exception as ex:
            show_snack(f"Erro ao salvar cadastro: {ex}")

    return ft.Container(
        expand=True, bgcolor="#0B132B", padding=20, alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=400, bgcolor="#1E293B", padding=20, border_radius=12,
            content=ft.Column([
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white", on_click=lambda _: on_back() if on_back else None),
                    ft.Text("Cadastro de Staff", size=18, weight="bold", color="white")
                ]),
                txt_nome, txt_email, txt_senha, txt_cpf, txt_rg, txt_whatsapp,
                btn_anexar_doc,
                lbl_doc_status,
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Finalizar Cadastro", 
                    style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"), 
                    width=360, height=45,
                    on_click=handle_cadastrar
                )
            ], spacing=10, scroll=ft.ScrollMode.AUTO)
        )
    )