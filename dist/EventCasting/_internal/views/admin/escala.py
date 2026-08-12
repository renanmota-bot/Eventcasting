import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS
)
from services.schedule_service import get_staff_schedule
from utils.formatters import date_to_br

def StaffEscalaView(page: ft.Page, user: dict, on_back):
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def reload_schedule():
        list_container.controls.clear()
        items = get_staff_schedule(user['id'])

        if not items:
            list_container.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Você ainda não está escalado em nenhum evento futuro.", color=COLOR_TEXT_SECONDARY)
                )
            )
        else:
            for item in items:
                dt_ini = date_to_br(item['data_inicio'])
                dt_fim = date_to_br(item['data_fim'])

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
                                    ft.Text(item['evento_nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                                    ft.Text(f"Função Escala: {item['funcao'].upper()} — R$ {item['valor_diaria']:.2f}/dia", size=14, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Data: {dt_ini} até {dt_fim} | Horário: {item['horario_inicio']} às {item['horario_fim']}", size=12, color=COLOR_TEXT_SECONDARY),
                                    ft.Text(f"Local: {item['local']} ({item['cidade']}/{item['estado']})", size=12, color=COLOR_TEXT_SECONDARY),
                                ]
                            ),
                            ft.Container(
                                content=ft.Text("CONFIRMADO", size=11, color="#000000", weight=ft.FontWeight.BOLD),
                                bgcolor=COLOR_SUCCESS,
                                padding=8,
                                border_radius=8
                            )
                        ]
                    )
                )
                list_container.controls.append(card)
        page.update()

    reload_schedule()

    return ft.Container(
        expand=True,
        padding=25,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                ft.Row(controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                    ft.Text("Minhas Escalas / Trabalhos", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                ]),
                list_container
            ]
        )
    )
