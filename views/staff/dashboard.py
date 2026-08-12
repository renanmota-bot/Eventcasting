import urllib.parse
import urllib.request
import json
from datetime import datetime
import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO
)
from services.candidacy_service import get_open_jobs_for_staff, apply_for_job
from services.checkin_service import get_staff_approved_schedules

def StaffDashboardView(page: ft.Page, user: dict, on_navigate=None, on_logout=None):
    usuario_id = user.get('id') if user else None
    nome_user = user.get('nome', 'Staff') if user else 'Staff'
    foto_b64 = user.get('foto_base64') if user else None
    active_tab = "vagas"

    list_vagas = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    list_escalas = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    main_content_area = ft.Container(expand=True)

    if foto_b64:
        user_avatar = ft.CircleAvatar(foreground_image_src=f"data:image/jpeg;base64,{foto_b64}", radius=18)
    else:
        user_avatar = ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON, color=COLOR_TEXT_PRIMARY, size=18), bgcolor="#0F172A", radius=18)

    def validate_address_exists(endereco_str: str) -> bool:
        if not endereco_str or len(endereco_str.strip()) < 5:
            return False
        try:
            query = urllib.parse.quote(endereco_str)
            url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&limit=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'EventCastingApp/1.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                return len(data) > 0
        except Exception:
            return bool(endereco_str and len(endereco_str) > 5)

    def open_google_maps(endereco):
        if not endereco or endereco.strip() in ["Local a definir", "S/N", ""]:
            show_snack("Endereço não encontrado", is_error=True)
            return

        if not validate_address_exists(endereco):
            show_snack("Endereço não encontrado", is_error=True)
            return

        query = urllib.parse.quote(endereco)
        maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"
        page.launch_url(maps_url)

    def reload_available_jobs():
        list_vagas.controls.clear()
        vagas = get_open_jobs_for_staff(usuario_id) if usuario_id else []

        if not vagas:
            list_vagas.controls.append(
                ft.Container(
                    bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text("Nenhuma vaga aberta disponível no momento.", color=COLOR_TEXT_SECONDARY, size=13)
                )
            )
            return

        for v in vagas:
            d_inicio_str = str(v['data_inicio'])
            d_fim_str = str(v['data_fim'])
            try:
                d_inicio_br = datetime.strptime(d_inicio_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                d_fim_br = datetime.strptime(d_fim_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                d_inicio_br, d_fim_br = d_inicio_str, d_fim_str

            status_candidatura = v.get('candidato_status')

            if status_candidatura:
                st_upper = str(status_candidatura).upper()
                bg_col = COLOR_INFO if st_upper == 'PENDENTE' else (COLOR_SUCCESS if st_upper == 'APROVADO' else COLOR_ERROR)
                btn_acao = ft.Container(
                    content=ft.Text(f"Status: {st_upper}", size=11, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                    bgcolor=bg_col, padding=6, border_radius=6, alignment=ft.Alignment(0, 0)
                )
            else:
                btn_acao = ft.ElevatedButton(
                    "Candidatar-se",
                    icon=ft.Icons.CHECK_CIRCLE,
                    style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"),
                    height=38,
                    on_click=lambda _, vid=v['vaga_id']: handle_apply(vid)
                )

            local_evento = v.get('evento_local') or "Local a definir"

            btn_maps = ft.TextButton(
                "Ver no Google Maps 📍",
                style=ft.ButtonStyle(color=COLOR_PRIMARY),
                on_click=lambda _, loc=local_evento: open_google_maps(loc)
            )

            card = ft.Container(
                bgcolor=COLOR_SURFACE, padding=12, border_radius=10,
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(v['funcao'], weight=ft.FontWeight.BOLD, size=15, color=COLOR_TEXT_PRIMARY),
                        ft.Text(f"🎪 {v['evento_nome']} ({v['empresa_nome']})", size=12, color=COLOR_TEXT_PRIMARY),
                        ft.Text(f"📍 Local: {local_evento}", size=12, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD),
                        btn_maps,
                        ft.Text(f"📅 Período: {d_inicio_br} até {d_fim_br}", size=11, color=COLOR_TEXT_SECONDARY),
                        ft.Text(f"💰 Diária: R$ {v['valor_diaria']} | Qtd: {v['quantidade']} vagas", size=12, color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD),
                        ft.Container(height=4),
                        btn_acao
                    ]
                )
            )
            list_vagas.controls.append(card)

    def reload_schedules():
        list_escalas.controls.clear()
        schedules = get_staff_approved_schedules(usuario_id) if usuario_id else []

        if not schedules:
            list_escalas.controls.append(
                ft.Container(
                    bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text("Você ainda não possui escalas aprovadas.", color=COLOR_TEXT_SECONDARY, size=13)
                )
            )
            return

        for s in schedules:
            d_inicio_str = str(s['data_inicio'])
            d_fim_str = str(s['data_fim'])
            try:
                d_inicio_br = datetime.strptime(d_inicio_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                d_fim_br = datetime.strptime(d_fim_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                d_inicio_br, d_fim_br = d_inicio_str, d_fim_str

            in_time = s['checkin'].strftime("%H:%M (%d/%m)") if s['checkin'] else "Pendente"
            out_time = s['checkout'].strftime("%H:%M (%d/%m)") if s['checkout'] else "Pendente"
            local_evento = s.get('evento_local') or "Local a definir"

            btn_maps = ft.ElevatedButton(
                "Como Chegar (Maps)", icon=ft.Icons.MAP,
                style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"),
                height=38,
                on_click=lambda _, loc=local_evento: open_google_maps(loc)
            )

            card = ft.Container(
                bgcolor=COLOR_SURFACE, padding=12, border_radius=10,
                content=ft.Column(spacing=6, controls=[
                    ft.Text(f"⭐ {s['funcao']} — {s['evento_nome']}", weight=ft.FontWeight.BOLD, size=15, color=COLOR_PRIMARY),
                    ft.Text(f"🏢 Produtora: {s['empresa_nome']}", size=12, color=COLOR_TEXT_PRIMARY),
                    ft.Text(f"📍 Local: {local_evento}", size=12, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD),
                    btn_maps,
                    ft.Text(f"📅 Período: {d_inicio_br} até {d_fim_br}", size=11, color=COLOR_TEXT_SECONDARY),
                    ft.Text(f"💰 Diária: R$ {s['valor_diaria']}", size=12, color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD),
                    ft.Divider(color="#334155"),
                    ft.Column(controls=[
                        ft.Text(f"Entrada: {in_time}", size=11, color=COLOR_TEXT_SECONDARY),
                        ft.Text(f"Saída: {out_time}", size=11, color=COLOR_TEXT_SECONDARY)
                    ], spacing=2)
                ])
            )
            list_escalas.controls.append(card)

    def handle_apply(vaga_id):
        if apply_for_job(vaga_id, usuario_id):
            show_snack("Candidatura enviada com sucesso!", is_error=False)
            reload_available_jobs()
            render_tab()
        else:
            show_snack("Erro ao processar candidatura.")

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=COLOR_ERROR if is_error else COLOR_SUCCESS)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def set_tab(tname):
        nonlocal active_tab
        active_tab = tname
        render_tab()

    def render_tab():
        if active_tab == "vagas":
            btn_tab_vagas.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000")
            btn_tab_escalas.style = ft.ButtonStyle(bgcolor=COLOR_SURFACE, color=COLOR_TEXT_PRIMARY)
            reload_available_jobs()
            main_content_area.content = list_vagas
        else:
            btn_tab_vagas.style = ft.ButtonStyle(bgcolor=COLOR_SURFACE, color=COLOR_TEXT_PRIMARY)
            btn_tab_escalas.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000")
            reload_schedules()
            main_content_area.content = list_escalas
        page.update()

    btn_tab_vagas = ft.ElevatedButton("Oportunidades", on_click=lambda _: set_tab("vagas"), height=36)
    btn_tab_escalas = ft.ElevatedButton("Minhas Escalas", on_click=lambda _: set_tab("escalas"), height=36)

    render_tab()

    return ft.Container(
        expand=True, padding=12, bgcolor="#0B132B",
        content=ft.Column(
            expand=True, spacing=12, scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(controls=[
                            user_avatar,
                            ft.Column(controls=[
                                ft.Text(f"{nome_user}", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                                ft.Text("Staff Verificado", size=11, color=COLOR_SUCCESS)
                            ], spacing=0)
                        ], spacing=8),
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.SETTINGS, icon_size=20, tooltip="Editar Perfil", icon_color=COLOR_PRIMARY, on_click=lambda _: on_navigate("PROFILE") if on_navigate else None),
                            ft.IconButton(ft.Icons.REFRESH, icon_size=20, tooltip="Atualizar", icon_color=COLOR_PRIMARY, on_click=lambda _: render_tab()),
                            ft.IconButton(ft.Icons.LOGOUT, icon_size=20, tooltip="Sair", icon_color=COLOR_ERROR, on_click=lambda _: on_logout() if on_logout else None)
                        ], spacing=2)
                    ]
                ),
                ft.Row(controls=[btn_tab_vagas, btn_tab_escalas], spacing=8, alignment=ft.MainAxisAlignment.START),
                ft.Divider(color="#334155", height=1),
                main_content_area
            ]
        )
    )