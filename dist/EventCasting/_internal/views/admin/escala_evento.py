import os
import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_INFO
)
from services.schedule_service import get_confirmed_team_by_event
from services.financial_service import update_attendance_status, get_event_financial_report, export_event_csv
from utils.formatters import date_to_br

def AdminEscalaEventoView(page: ft.Page, event: dict, on_back):
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def reload_team_list():
        list_container.controls.clear()
        team = get_confirmed_team_by_event(event['id'])
        report = get_event_financial_report(event['id'])

        summary_card = ft.Container(
            bgcolor=COLOR_SURFACE,
            padding=15,
            border_radius=8,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"Equipe: {report.get('total_escalados', 0)} pessoas", weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                    ft.Text(f"Previsto: R$ {report.get('total_previsto', 0):.2f}", weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY),
                    ft.Text(f"A Pagar: R$ {report.get('total_devido', 0) - report.get('total_pago', 0):.2f}", weight=ft.FontWeight.BOLD, color=COLOR_WARNING),
                    ft.Text(f"Pago: R$ {report.get('total_pago', 0):.2f}", weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS, size=16),
                ]
            )
        )
        list_container.controls.append(summary_card)

        if not team:
            list_container.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhum colaborador na escala deste evento.", color=COLOR_TEXT_SECONDARY)
                )
            )
        else:
            for member in team:
                c_id = member['candidatura_id']
                status = member['status_candidatura']

                actions = []
                if status == "APROVADA":
                    actions.extend([
                        ft.Button("Presença", style=ft.ButtonStyle(bgcolor=COLOR_INFO, color="#FFFFFF"), on_click=lambda _, cid=c_id: change_status(cid, "PRESENTE")),
                        ft.Button("Falta", style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color="#FFFFFF"), on_click=lambda _, cid=c_id: change_status(cid, "FALTOU"))
                    ])
                elif status == "PRESENTE":
                    actions.extend([
                        ft.Button("Dar Baixa (Pagar)", style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"), on_click=lambda _, cid=c_id: change_status(cid, "PAGO")),
                        ft.Button("Falta", style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color="#FFFFFF"), on_click=lambda _, cid=c_id: change_status(cid, "FALTOU"))
                    ])
                elif status == "PAGO":
                    actions.append(
                        ft.Container(
                            content=ft.Text("PAGO / CONCLUÍDO", size=11, color="#000000", weight=ft.FontWeight.BOLD),
                            bgcolor=COLOR_SUCCESS, padding=8, border_radius=8
                        )
                    )
                elif status == "FALTOU":
                    actions.extend([
                        ft.Container(
                            content=ft.Text("FALTOU", size=11, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                            bgcolor=COLOR_ERROR, padding=8, border_radius=8
                        ),
                        ft.TextButton("Reativar", on_click=lambda _, cid=c_id: change_status(cid, "PRESENTE"))
                    ])

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
                                    ft.Row(controls=[
                                        ft.Text(member['nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                                        ft.Container(
                                            content=ft.Text(member['funcao'].upper(), size=11, color="#000000", weight=ft.FontWeight.BOLD),
                                            bgcolor=COLOR_PRIMARY, padding=6, border_radius=10
                                        )
                                    ]),
                                    ft.Text(f"CPF: {member['cpf']} | WhatsApp: {member['whatsapp']}", size=13, color=COLOR_TEXT_SECONDARY),
                                    ft.Text(f"Chave Pix: {member['chave_pix'] or 'Não informada'} | Valor: R$ {member['valor_diaria']:.2f}", size=12, color=COLOR_TEXT_SECONDARY),
                                ]
                            ),
                            ft.Row(controls=actions, spacing=8)
                        ]
                    )
                )
                list_container.controls.append(card)
        page.update()

    def change_status(candidatura_id, new_status):
        if update_attendance_status(candidatura_id, new_status):
            reload_team_list()

    def handle_export_click(_):
        file_name_clean = "".join(c for c in event['nome'] if c.isalnum() or c in (' ', '_', '-')).strip()
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        save_path = os.path.join(downloads_folder, f"fechamento_{file_name_clean}.csv")
        
        success, msg = export_event_csv(event['id'], save_path)
        
        display_msg = f"Relatório salvo em Downloads: fechamento_{file_name_clean}.csv" if success else msg

        snack = ft.SnackBar(
            content=ft.Text(display_msg),
            bgcolor=COLOR_SUCCESS if success else COLOR_ERROR
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    reload_team_list()
    dt_ini = date_to_br(event.get('data_inicio'))

    return ft.Container(
        expand=True,
        padding=25,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                            ft.Column(spacing=2, controls=[
                                ft.Text(f"Gestão de Presença & Pagamentos: {event['nome']}", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                                ft.Text(f"Local: {event['local']} ({dt_ini})", size=13, color=COLOR_TEXT_SECONDARY)
                            ])
                        ]),
                        ft.Button(
                            "Exportar Relatório CSV",
                            icon=ft.Icons.DOWNLOAD,
                            style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"),
                            on_click=handle_export_click
                        )
                    ]
                ),
                list_container
            ]
        )
    )