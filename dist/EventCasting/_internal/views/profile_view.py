import base64
import threading
import cv2
import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
)
from services.auth_service import update_user_profile
from utils.validators import is_valid_whatsapp, is_strong_password

def ProfileView(page: ft.Page, user: dict, on_back):
    user_id = user.get('id')
    foto_base64_str = [user.get('foto_base64')]

    if foto_base64_str[0]:
        avatar_img = ft.CircleAvatar(foreground_image_src=f"data:image/jpeg;base64,{foto_base64_str[0]}", radius=45)
    else:
        avatar_img = ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON, size=40, color=COLOR_TEXT_SECONDARY), bgcolor="#0F172A", radius=45)

    def open_camera_thread():
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                show_snack("Nenhuma câmera encontrada.")
                return

            show_snack("Câmera aberta! ESPAÇO para capturar foto.", is_error=False)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                cv2.imshow("Atualizar Selfie — ESPACO: Capturar | ESC: Sair", frame)
                key = cv2.waitKey(1) & 0xFF

                if key == 32:  # ESPAÇO
                    _, buffer = cv2.imencode('.jpg', frame)
                    encoded_bytes = base64.b64encode(buffer).decode('utf-8')
                    foto_base64_str[0] = encoded_bytes
                    avatar_img.content = None
                    avatar_img.foreground_image_src = f"data:image/jpeg;base64,{encoded_bytes}"
                    page.update()
                    show_snack("Nova selfie capturada!", is_error=False)
                    break
                elif key == 27:  # ESC
                    break

            cap.release()
            cv2.destroyAllWindows()
        except Exception as ex:
            show_snack(f"Erro na câmera: {ex}")

    def take_selfie(_):
        threading.Thread(target=open_camera_thread, daemon=True).start()

    txt_nome = ft.TextField(
        label="Nome Completo", value=user.get('nome', ''), 
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, 
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_whatsapp = ft.TextField(
        label="WhatsApp", value=user.get('whatsapp', ''), 
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, 
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_chave_pix = ft.TextField(
        label="Chave Pix", value=user.get('chave_pix', ''), 
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, 
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_nova_senha = ft.TextField(
        label="Nova Senha (Opcional)", password=True, can_reveal_password=True, 
        hint_text="Deixe em branco para não alterar", border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), 
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )

    btn_selfie = ft.ElevatedButton(
        "Nova Selfie", icon=ft.Icons.CAMERA_ALT, 
        style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), 
        on_click=take_selfie
    )

    def handle_save(_):
        nome_val = txt_nome.value.strip() if txt_nome.value else ""
        whats_val = txt_whatsapp.value.strip() if txt_whatsapp.value else ""
        pix_val = txt_chave_pix.value.strip() if txt_chave_pix.value else ""
        senha_val = txt_nova_senha.value.strip() if txt_nova_senha.value else None

        if not nome_val:
            show_snack("Nome não pode ficar em branco.")
            return

        if whats_val and not is_valid_whatsapp(whats_val):
            show_snack("WhatsApp inválido. Use (DD) 9XXXX-XXXX.")
            return

        if senha_val:
            is_strong, msg_senha = is_strong_password(senha_val)
            if not is_strong:
                show_snack(msg_senha)
                return

        success = update_user_profile(
            user_id=user_id,
            nome=nome_val,
            whatsapp=whats_val,
            chave_pix=pix_val,
            senha=senha_val,
            foto_base64=foto_base64_str[0]
        )

        if success:
            user['nome'] = nome_val
            user['whatsapp'] = whats_val
            user['chave_pix'] = pix_val
            user['foto_base64'] = foto_base64_str[0]
            show_snack("Perfil atualizado com sucesso!", is_error=False)
            on_back()
        else:
            show_snack("Erro ao salvar alterações do perfil.")

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
                        ft.Text("Meu Perfil", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
                    ]),
                    ft.Row(controls=[avatar_img, btn_selfie], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                    txt_nome, txt_whatsapp, txt_chave_pix, txt_nova_senha,
                    ft.Container(height=10),
                    ft.ElevatedButton("Salvar Alterações", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), width=380, on_click=handle_save)
                ]
            )
        )
    )