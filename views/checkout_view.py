import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
)
from services.payment_service import (
    process_pix_payment, process_card_payment, confirm_payment_and_activate
)

def CheckoutView(page: ft.Page, user: dict, on_success):
    empresa_id = user.get('empresa_id', 1) if user else 1
    user_email = user.get('email', 'admin@empresa.com') if user else 'admin@empresa.com'
    pix_charge = [None]
    payment_method = ["PIX"]

    # --- CONTROLES PIX ---
    txt_copia_cola = ft.TextField(
        label="Pix Copia e Cola (R$ 100,00)", read_only=True, multiline=True, min_lines=2, max_lines=3,
        border_color=COLOR_TEXT_SECONDARY, text_size=12, color=COLOR_TEXT_PRIMARY
    )
    pix_box = ft.Column(visible=False, spacing=10, controls=[
        txt_copia_cola,
        ft.ElevatedButton(
            "Copiar Código Pix", icon=ft.Icons.COPY,
            style=ft.ButtonStyle(bgcolor=COLOR_SURFACE, color=COLOR_TEXT_PRIMARY),
            on_click=lambda _: copy_pix()
        ),
        ft.ElevatedButton(
            "Confirmar / Ativar Pagamento", icon=ft.Icons.CHECK_CIRCLE,
            style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"),
            on_click=lambda _: handle_confirm_pix()
        )
    ])

    # --- CONTROLES CARTÃO ---
    txt_card_num = ft.TextField(label="Número do Cartão", max_length=19, border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY)
    txt_card_holder = ft.TextField(label="Nome Impresso no Cartão", border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY)
    txt_card_exp_month = ft.TextField(label="Mês (MM)", max_length=2, border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY)
    txt_card_exp_year = ft.TextField(label="Ano (AA)", max_length=2, border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY)
    txt_card_cvc = ft.TextField(label="CVC / CVV", max_length=4, password=True, border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY)

    card_box = ft.Column(visible=False, spacing=10, controls=[
        txt_card_num, txt_card_holder,
        ft.Row(controls=[txt_card_exp_month, txt_card_exp_year, txt_card_cvc], expand=True),
        ft.ElevatedButton(
            "Pagar R$ 100,00 no Cartão", icon=ft.Icons.CREDIT_CARD,
            style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"),
            width=380,
            on_click=lambda _: handle_pay_card()
        )
    ])

    def copy_pix():
        if pix_charge[0]:
            page.set_clipboard(pix_charge[0]["pix_copia_cola"])
            show_snack("Código Pix copiado!", is_error=False)

    def handle_confirm_pix():
        if confirm_payment_and_activate(empresa_id, pix_charge[0]["id"] if pix_charge[0] else None):
            show_snack("Pagamento confirmado com sucesso! Empresa ativada.", is_error=False)
            on_success()

    def handle_pay_card():
        success, msg = process_card_payment(
            empresa_id=empresa_id,
            email=user_email,
            card_number=txt_card_num.value,
            card_holder=txt_card_holder.value,
            exp_month=txt_card_exp_month.value,
            exp_year=txt_card_exp_year.value,
            cvc=txt_card_cvc.value
        )
        if success:
            show_snack("Pagamento no Cartão aprovado! Ativando empresa...", is_error=False)
            on_success()
        else:
            show_snack(msg)

    def switch_method(method):
        payment_method[0] = method
        if method == "PIX":
            btn_tab_pix.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000")
            btn_tab_card.style = ft.ButtonStyle(bgcolor=COLOR_SURFACE, color=COLOR_TEXT_PRIMARY)
            
            if not pix_charge[0]:
                pix_charge[0] = process_pix_payment(empresa_id, user_email)
                txt_copia_cola.value = pix_charge[0]["pix_copia_cola"]
            
            pix_box.visible = True
            card_box.visible = False
        else:
            btn_tab_pix.style = ft.ButtonStyle(bgcolor=COLOR_SURFACE, color=COLOR_TEXT_PRIMARY)
            btn_tab_card.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000")
            pix_box.visible = False
            card_box.visible = True
        page.update()

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=COLOR_ERROR if is_error else COLOR_SUCCESS)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    btn_tab_pix = ft.ElevatedButton("Pagamento Pix", icon=ft.Icons.PIX, on_click=lambda _: switch_method("PIX"))
    btn_tab_card = ft.ElevatedButton("Cartão de Crédito", icon=ft.Icons.CREDIT_CARD, on_click=lambda _: switch_method("CARD"))

    switch_method("PIX")

    return ft.Container(
        expand=True, alignment=ft.Alignment(0, 0), padding=20,
        content=ft.Container(
            width=480, bgcolor="#0B132B", padding=30, border_radius=12,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text("Assinatura Event Casting", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                    ft.Text("Ative sua licença mensal de R$ 100,00 escolhendo a forma de pagamento.", size=12, color=COLOR_TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                    ft.Row(controls=[btn_tab_pix, btn_tab_card], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    ft.Divider(color="#334155"),
                    pix_box,
                    card_box
                ]
            )
        )
    )