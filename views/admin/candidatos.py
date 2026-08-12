import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
)
from services.application_service import get_candidates_by_job, update_application_status
from utils.formatters import date_to_br

def AdminCandidatosView(page: ft.Page, job: dict, event: dict, on_back):
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def reload_candidates_list():
        list_container.controls.clear()
        candidates = get_candidates_by_job(job['id'])

        if not candidates:
            list_container.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhum colaborador se candidatou a esta vaga ainda.", color=COLOR_TEXT_SECONDARY)
                )
            )
        else:
            for cand in candidates:
                c_id = cand['candidatura_id']
                c_status = cand['candidatura_status']

                actions = []
                if c_status == "PENDENTE":
                    btn_approve = ft.Button(
                        "Aprovar",
                        style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"),
                        on_click=lambda _, cid=c_id: change_status(cid, "APROVADA")
                    )
                    btn_reject = ft.Button(
                        "Recusar",
                        style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color="#FFFFFF"),
                        on_click=lambda _, cid=c_id: change_status(cid, "RECUSADA")
                    )
                    actions.append(btn_approve)
                    actions.append(btn_reject)
                else:
                    status_color = COLOR_SUCCESS if c_status == "APROVADA" else COLOR_ERROR
                    actions.append(
                        ft.Container(
                            content=ft.Text(c_status, size=11, color="#000000", weight=ft.FontWeight.BOLD),
                            bgcolor=status_color,
                            padding=6,
                            border_radius=8
                        )
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
                                    ft.Text(cand['nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                                    ft.Text(f"Função Principal: {cand['funcao_principal']} | Contato: {cand['whatsapp']}", size=13, color=COLOR_TEXT_SECONDARY),
                                    ft.Text(f"Cidade: {cand['cidade']}/{cand['estado']} | Experiência: {cand['experiencia'] or 'Não informada'}", size=12, color=COLOR_TEXT_SECONDARY),
                                ]
                            ),
                            ft.Row(controls=actions, spacing=8)
                        ]
                    )
                )
                list_container.controls.append(card)
        page.update()

    def change_status(candidatura_id, new_status):
        if update_application_status(candidatura_id, new_status):
            reload_candidates_list()

    reload_candidates_list()

    dt_ini = date_to_br(event.get('data_inicio'))

    return ft.Container(
        expand=True,
        padding=25,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                ft.Row(controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                    ft.Column(spacing=2, controls=[
                        ft.Text(f"Candidatos: {job['funcao'].upper()}", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                        ft.Text(f"Evento: {event['nome']} ({dt_ini})", size=13, color=COLOR_TEXT_SECONDARY)
                    ])
                ]),
                list_container
            ]
        )
    )
