from datetime import datetime
import flet as ft
from config.theme import (
    BG_DARK, SURFACE_DARK, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, 
    SUCCESS, ERROR, BORDER_COLOR, create_glass_card
)
from services.event_service import get_company_events, create_event
from services.job_service import get_event_jobs, create_job
from services.admin_candidacy_service import get_event_candidacies, update_candidacy_status
from services.checkin_service import get_approved_staff_for_event, register_checkin, register_checkout
from services.financial_service import get_financial_summary_by_event, get_event_payroll
from services.export_service import export_payroll_pdf

def ResponsiveAdminDashboard(page: ft.Page, user: dict, on_navigate, on_logout):
    empresa_id = user.get('empresa_id')
    current_tab = [0]  # 0: Eventos, 1: Candidaturas, 2: Presença, 3: Financeiro

    content_area = ft.Container(expand=True, padding=15)

    def is_mobile():
        return (page.width or 800) < 768

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(
            content=ft.Text(msg, color="#FFFFFF"), 
            bgcolor=ERROR if is_error else SUCCESS
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- NAVEGAÇÃO DE ACORDO COM A TELA ---
    def on_tab_change(e):
        selected = e.control.selected_index
        current_tab[0] = selected
        render_content()

    # Sidebar para Desktop (Computador)
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        bgcolor=SURFACE_DARK,
        indicator_color=PRIMARY,
        on_change=on_tab_change,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.EVENT_OUTLINED, selected_icon=ft.Icons.EVENT, label="Eventos"),
            ft.NavigationRailDestination(icon=ft.Icons.PEOPLE_OUTLINE, selected_icon=ft.Icons.PEOPLE, label="Casting"),
            ft.NavigationRailDestination(icon=ft.Icons.TIMER_OUTLINED, selected_icon=ft.Icons.TIMER, label="Presença"),
            ft.NavigationRailDestination(icon=ft.Icons.ATTACH_MONEY_OUTLINED, selected_icon=ft.Icons.ATTACH_MONEY, label="Financeiro"),
        ]
    )

    # Navigation Bar para Celular
    bottom_nav = ft.NavigationBar(
        selected_index=0,
        bgcolor=SURFACE_DARK,
        indicator_color=PRIMARY,
        on_change=on_tab_change,
        destinations=[
            ft.NavigationDestination(icon=ft.Icons.EVENT, label="Eventos"),
            ft.NavigationDestination(icon=ft.Icons.PEOPLE, label="Casting"),
            ft.NavigationDestination(icon=ft.Icons.TIMER, label="Presença"),
            ft.NavigationDestination(icon=ft.Icons.ATTACH_MONEY, label="Financeiro"),
        ]
    )

    # --- RENDERIZADORES DE ABAS ---
    def render_eventos_view():
        events = get_company_events(empresa_id)
        cards = []
        for ev in events:
            c = create_glass_card([
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=2, controls=[
                            ft.Text(ev['nome'], size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(f"📍 {ev.get('local', 'Local N/I')}", size=12, color=TEXT_SECONDARY),
                        ]),
                        ft.Container(
                            content=ft.Text("Ativo", size=11, color="#FFFFFF"),
                            bgcolor=SUCCESS, padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=12
                        )
                    ]
                )
            ])
            cards.append(c)

        return ft.ListView(
            controls=[
                ft.Text("Gestão de Eventos", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Divider(color=BORDER_COLOR),
                *cards
            ],
            spacing=10, expand=True
        )

    def render_content():
        idx = current_tab[0]
        if idx == 0:
            content_area.content = render_eventos_view()
        elif idx == 1:
            content_area.content = ft.Text("Candidaturas / Casting", size=18, color=TEXT_PRIMARY)
        elif idx == 2:
            content_area.content = ft.Text("Controle de Presença (Check-in)", size=18, color=TEXT_PRIMARY)
        else:
            content_area.content = ft.Text("Folha de Pagamento & Relatórios", size=18, color=TEXT_PRIMARY)
        
        page.update()

    def handle_resize(e):
        # Reconstrói a estrutura ao girar o celular ou redimensionar a janela do PC
        build_layout()

    page.on_resized = handle_resize

    def build_layout():
        page.controls.clear()
        
        header = ft.Container(
            bgcolor=SURFACE_DARK, padding=15,
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(controls=[
                        ft.Icon(ft.Icons.FLASH_ON, color=PRIMARY, size=24),
                        ft.Text("Event Casting", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
                    ]),
                    ft.Row(controls=[
                        ft.ElevatedButton(
                            "Link Staff", icon=ft.Icons.LINK,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color="#000000"),
                            on_click=lambda _: page.set_clipboard(f"https://eventcasting.app/register_staff?empresa_id={empresa_id}")
                        ),
                        ft.IconButton(ft.Icons.LOGOUT, icon_color=ERROR, on_click=lambda _: on_logout())
                    ])
                ]
            )
        )

        if is_mobile():
            # Layout Smartphone: Header Topo + Conteúdo + Barra Inferior
            layout = ft.Column(
                expand=True, spacing=0,
                controls=[
                    header,
                    content_area,
                    bottom_nav
                ]
            )
        else:
            # Layout Desktop: Header Topo + [Sidebar + Conteúdo Principal]
            layout = ft.Column(
                expand=True, spacing=0,
                controls=[
                    header,
                    ft.Row(
                        expand=True, spacing=0,
                        controls=[
                            nav_rail,
                            ft.VerticalDivider(width=1, color=BORDER_COLOR),
                            content_area
                        ]
                    )
                ]
            )

        page.add(layout)
        render_content()

    build_layout()
