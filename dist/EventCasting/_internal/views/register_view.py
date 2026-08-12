import base64
import threading
import cv2
import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
)
from services.auth_service import register_staff_user
from services.verification_service import generate_verification_code, send_email_code, verify_code
from utils.validators import is_valid_cpf, is_valid_email, is_valid_whatsapp, is_strong_password

def RegisterView(page: ft.Page, on_back, default_empresa_id=1):
    foto_base64_str = [None]

    avatar_img = ft.CircleAvatar(
        content=ft.Icon(ft.Icons.PERSON, size=40, color=COLOR_TEXT_SECONDARY),
        bgcolor="#0F172A", radius=45
    )

    def open_camera_thread():
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened(): cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                show_snack("Nenhuma câmera encontrada.")
                return

            show_snack("Câmera aberta! ESPAÇO para tirar a foto.", is_error=False)

            while True:
                ret, frame = cap.read()
                if not ret: break

                cv2.imshow("Tirar Selfie — ESPACO: Capturar | ESC: Sair", frame)
                key = cv2.waitKey(1) & 0xFF

                if key == 32:  # ESPAÇO
                    _, buffer = cv2.imencode('.jpg', frame)
                    encoded_bytes = base64.b64encode(buffer).decode('utf-8')
                    foto_base64_str[0] = encoded_bytes
                    avatar_img.content = None
                    avatar_img.foreground_image_src = f"data:image/jpeg;base64,{encoded_bytes}"
                    page.update()
                    show_snack("Selfie capturada!", is_error=False)
                    break
                elif key == 27:  # ESC
                    break

            cap.release()
            cv2.destroyAllWindows()
        except Exception as ex:
            show_snack(f"Erro ao abrir câmera: {ex}")

    def take_selfie(_):
        threading.Thread(target=open_camera_thread, daemon=True).start()

    # Campo de Código da Empresa Fixado e Bloqueado para Leitura
    txt_empresa_id = ft.TextField(
        label="Código da Produtora (Fixado)", value=str(default_empresa_id), read_only=True,
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_nome = ft.TextField(label="Nome Completo", border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY))
    txt_email = ft.TextField(label="E-mail Real", border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY))
    txt_senha = ft.TextField(label="Senha Forte", hint_text="Ex: Mín 8 chars, A-Z, a-z, 0-9, @#$", password=True, can_reveal_password=True, border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY))

    def format_cpf(e):
        val = "".join(filter(str.isdigit, e.control.value or ""))[:11]
        formatted = val
        if len(val) > 3: formatted = val[:3] + "." + val[3:]
        if len(val) > 6: formatted = val[:3] + "." + val[3:6] + "." + val[6:]
        if len(val) > 9: formatted = val[:3] + "." + val[3:6] + "." + val[6:9] + "-" + val[9:]
        e.control.value = formatted
        page.update()

    def format_phone(e):
        val = "".join(filter(str.isdigit, e.control.value or ""))[:11]
        formatted = val
        if len(val) > 2: formatted = "(" + val[:2] + ") " + val[2:]
        if len(val) > 7: formatted = "(" + val[:2] + ") " + val[2:7] + "-" + val[7:]
        e.control.value = formatted
        page.update()

    txt_cpf = ft.TextField(label="CPF Válido", max_length=14, border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY), on_change=format_cpf)
    txt_whatsapp = ft.TextField(label="WhatsApp (DDD + Número)", max_length=15, border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY), on_change=format_phone)
    txt_chave_pix = ft.TextField(label="Chave Pix", border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY))

    btn_tirar_selfie = ft.ElevatedButton("Tirar Selfie (Câmera)", icon=ft.Icons.CAMERA_ALT, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=take_selfie)

    txt_codigo_validacao = ft.TextField(label="Código de 6 dígitos", max_length=6, text_align=ft.TextAlign.CENTER, text_size=18)

    def confirm_registration(_):
        email_val = txt_email.value.strip()
        if not verify_code(email_val, txt_codigo_validacao.value or ""):
            show_snack("Código de verificação incorreto!")
            return

        success = register_staff_user(
            empresa_id=int(txt_empresa_id.value),
            nome=txt_nome.value.strip(),
            email=email_val,
            senha=txt_senha.value.strip(),
            cpf=txt_cpf.value.strip(),
            whatsapp=txt_whatsapp.value.strip(),
            chave_pix=txt_chave_pix.value.strip(),
            foto_base64=foto_base64_str[0]
        )

        page.close(dlg_confirmacao)

        if success:
            show_snack("Conta de Staff criada com sucesso!", is_error=False)
            on_back()
        else:
            show_snack("Erro ao cadastrar. E-mail ou CPF já cadastrados.")

    dlg_confirmacao = ft.AlertDialog(
        title=ft.Text("Verificação de E-mail"),
        content=ft.Column(tight=True, controls=[
            ft.Text("Enviamos um código de verificação para o seu e-mail.", size=13, color=COLOR_TEXT_SECONDARY),
            txt_codigo_validacao
        ]),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg_confirmacao)),
            ft.ElevatedButton("Confirmar e Criar Conta", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=confirm_registration)
        ]
    )

    def handle_register(_):
        email_val = (txt_email.value or "").strip()
        senha_val = (txt_senha.value or "").strip()
        cpf_val = (txt_cpf.value or "").strip()
        whats_val = (txt_whatsapp.value or "").strip()

        if not all([txt_nome.value, email_val, senha_val, cpf_val, whats_val]):
            show_snack("Preencha todos os campos do cadastro.")
            return

        if not foto_base64_str[0]:
            show_snack("A selfie é obrigatória!")
            return

        if not is_valid_email(email_val):
            show_snack("Formato de e-mail inválido!")
            return

        is_strong, msg_senha = is_strong_password(senha_val)
        if not is_strong:
            show_snack(msg_senha)
            return

        if not is_valid_cpf(cpf_val):
            show_snack("CPF inválido! Insira um CPF verdadeiro.")
            return

        if not is_valid_whatsapp(whats_val):
            show_snack("WhatsApp inválido! Use o formato (DD) 9XXXX-XXXX.")
            return

        codigo = generate_verification_code(email_val)
        send_email_code(email_val, codigo)
        page.open(dlg_confirmacao)

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=COLOR_ERROR if is_error else COLOR_SUCCESS)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    return ft.Container(
        expand=True, alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=420, bgcolor=COLOR_SURFACE, padding=30, border_radius=12,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12, scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(controls=[
                        ft.IconButton(ft.Icons.ARROW_BACK, icon_color=COLOR_TEXT_PRIMARY, on_click=lambda _: on_back()),
                        ft.Text("Inscrição de Staff", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
                    ]),
                    ft.Row(controls=[avatar_img, btn_tirar_selfie], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                    txt_empresa_id, txt_nome, txt_email, txt_senha, txt_cpf, txt_whatsapp, txt_chave_pix,
                    ft.Container(height=10),
                    ft.ElevatedButton("Validar Dados e Concluir", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), width=380, on_click=handle_register)
                ]
            )
        )
    )