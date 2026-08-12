import flet as ft

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query

def AdminDashboardView(page: ft.Page, user=None, on_logout=None, on_navigate=None):
    nome_admin = user.get('nome', 'Administrador') if user else 'Administrador'
    empresa_id = user.get('empresa_id') if user else None

    # Link oficial configurado para o Render
    staff_link = f"https://eventcasting.onrender.com/?register&empresa={empresa_id}" if empresa_id else "https://eventcasting.onrender.com/?register"

    def handle_copy_staff_link(e):
        try:
            page.clipboard = staff_link
        except Exception:
            try:
                page.set_clipboard_async(staff_link)
            except Exception as ex:
                print(f"Erro ao copiar para clipboard: {ex}")

        snack = ft.SnackBar(
            content=ft.Text("Link do Staff copiado para a área de transferência!"),
            bgcolor="#2A9D8F"
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    txt_total_staff = ft.Text("0", size=22, weight="bold", color="#4CC9F0")
    txt_eventos_ativos = ft.Text("0", size=22, weight="bold", color="#2A9D8F")

    def carregar_metricas():
        if not empresa_id:
            return
        try:
            res_staff = execute_query(
                "SELECT COUNT(*) as qtd FROM usuarios WHERE empresa_id = %s AND perfil = 'STAFF';", 
                (empresa_id,), fetch_all=True
            )
            if res_staff:
                txt_total_staff.value = str(res_staff[0].get('qtd', 0))
        except Exception:
            pass
        page.update()

    btn_copiar_link = ft.ElevatedButton(
        "Copiar Link do Staff",
        style=ft.ButtonStyle(bgcolor="#4CC9F0", color="white", shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=handle_copy_staff_link,
        height=45
    )

    card_link_staff = ft.Container(
        content=ft.Column([
            ft.Text("Link de Convite para Equipe (Staff)", weight="bold", size=15, color="white"),
            ft.Text("Compartilhe este link para cadastrar novos membros na sua empresa:", size=12, color="#94A3B8"),
            ft.TextField(value=staff_link, read_only=True, text_size=12, border_radius=8),
            btn_copiar_link
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        bgcolor="#1E293B",
        padding=15,
        border_radius=12
    )

    cards_metricas = ft.ResponsiveRow([
        ft.Container(
            content=ft.Column([
                ft.Text("Membros Staff", color="#94A3B8", size=12),
                txt_total_staff
            ]),
            bgcolor="#1E293B", padding=15, border_radius=10, col={"xs": 6, "sm": 6}
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Eventos Ativos", color="#94A3B8", size=12),
                txt_eventos_ativos
            ]),
            bgcolor="#1E293B", padding=15, border_radius=10, col={"xs": 6, "sm": 6}
        )
    ], spacing=10)

    carregar_metricas()

    # Layout fluído que se adapta perfeitamente ao celular e ao computador
    return ft.Container(
        expand=True,
        bgcolor="#0B132B",
        padding=12,
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(f"Painel — {nome_admin}", size=18, weight="bold", color="white"),
                    ft.Text("Gestão da equipe de eventos", size=12, color="#94A3B8")
                ], expand=True),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color="#E76F51",
                    tooltip="Sair",
                    on_click=lambda e: on_logout() if on_logout else None
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            cards_metricas,
            card_link_staff
        ], spacing=15, scroll=ft.ScrollMode.AUTO)
    )