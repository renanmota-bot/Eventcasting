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
        style=ft.ButtonStyle(bgcolor="#4CC9F0", color="white"),
        on_click=handle_copy_staff_link
    )

    card_link_staff = ft.Container(
        content=ft.Column([
            ft.Text("Link de Convite para Equipe (Staff)", weight="bold", size=16, color="white"),
            ft.Text("Compartilhe este link para cadastrar novos membros na sua empresa:", size=12, color="#94A3B8"),
            ft.Row([
                ft.TextField(value=staff_link, read_only=True, expand=True, text_size=13),
                btn_copiar_link
            ])
        ], spacing=10),
        bgcolor="#1E293B",
        padding=20,
        border_radius=10
    )

    cards_metricas = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("Membros Staff", color="#94A3B8"),
                txt_total_staff
            ]),
            bgcolor="#1E293B", padding=15, border_radius=8, expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Eventos Ativos", color="#94A3B8"),
                txt_eventos_ativos
            ]),
            bgcolor="#1E293B", padding=15, border_radius=8, expand=True
        )
    ], spacing=20)

    carregar_metricas()

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(f"Painel da Empresa — {nome_admin}", size=22, weight="bold", color="white"),
                    ft.Text("Gestão da equipe de eventos e convites", size=13, color="#94A3B8")
                ]),
                ft.ElevatedButton("Sair", on_click=lambda e: on_logout() if on_logout else None)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            cards_metricas,
            card_link_staff
        ], spacing=20, scroll=ft.ScrollMode.AUTO),
        padding=20,
        expand=True,
        bgcolor="#0B132B"
    )