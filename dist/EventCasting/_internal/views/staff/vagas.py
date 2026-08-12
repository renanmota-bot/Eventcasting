import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING
)
from services.application_service import get_open_jobs_for_staff, apply_to_job
from utils.formatters import date_to_br

def StaffVagasView(page: ft.Page, user: dict, on_back):
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def reload_vagas_list():
        list_container.controls.clear()
        jobs = get_open_jobs_for_staff(user['id'])

        if not jobs:
            list_container.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhuma vaga aberta disponível no momento.", color=COLOR_TEXT_SECONDARY)
                )
            )
        else:
            for job in jobs:
                j_id = job['id']
                cand_status = job['candidatura_status']
                dt_ini = date_to_br(job['data_inicio'])

                if cand_status is None:
                    action_control = ft.Button(
                        "Candidatar-se",
                        style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"),
                        on_click=lambda _, jid=j_id: handle_apply(jid)
                    )
                else:
                    status_color = COLOR_WARNING if cand_status == "PENDENTE" else (COLOR_SUCCESS if cand_status == "APROVADA" else COLOR_ERROR)
                    action_control = ft.Container(
                        content=ft.Text(f"Candidatura {cand_status}", size=12, color="#000000", weight=ft.FontWeight.BOLD),
                        bgcolor=status_color,
                        padding=8,
                        border_radius=8
                    )

                card = ft.Container(
                    bgcolor=COLOR_SURFACE,
                    padding=15,
                    border_radius=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(job['evento_nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                                    ft.Text(f"Função: {job['funcao'].upper()} — R$ {job['valor_diaria']:.2f}/dia", size=14, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Data: {dt_ini} | Horário: {job['horario_inicio']} às {job['horario_fim']}", size=12, color=COLOR_TEXT_SECONDARY),
                                    ft.Text(f"Local: {job['local']} ({job['cidade']}/{job['estado']})", size=12, color=COLOR_TEXT_SECONDARY),
                                ]
                            ),
                            action_control
                        ]
                    )
                )
                list_container.controls.append(card)
        page.update()

    def handle_apply(job_id):
        if user['status'] != "APROVADO":
            snack = ft.SnackBar(content=ft.Text("Seu cadastro ainda precisa ser APROVADO pela administração para se candidatar."), bgcolor=COLOR_ERROR)
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return

        success, msg = apply_to_job(job_id, user['id'])
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=COLOR_SUCCESS if success else COLOR_ERROR)
        page.overlay.append(snack)
        snack.open = True
        reload_vagas_list()

    reload_vagas_list()

    return ft.Container(
        expand=True,
        padding=25,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                ft.Row(controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                    ft.Text("Vagas Abertas", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                ]),
                list_container
            ]
        )
    )