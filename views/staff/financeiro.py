import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_WARNING
)
from services.financial_service import get_staff_financial_summary
from utils.formatters import date_to_br

def StaffFinanceiroView(page: ft.Page, user: dict, on_back):
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    records = get_staff_financial_summary(user['id'])
    total_recebido = sum(r['valor_diaria'] for r in records if r['status_pagamento'] == 'PAGO')
    total_pendente = sum(r['valor_diaria'] for r in records if r['status_pagamento'] == 'PRESENTE')

    # Card de resumo dos ganhos
    summary_card = ft.Container(
        bgcolor=COLOR_SURFACE,
        padding=15,
        border_radius=8,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(f"A Receber: R$ {total_pendente:.2f}", weight=ft.FontWeight.BOLD, color=COLOR_WARNING, size=15),
                ft.Text(f"Total Recebido: R$ {total_recebido:.2f}", weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS, size=15),
            ]
        )
    )
    list_container.controls.append(summary_card)

    if not records:
        list_container.controls.append(
            ft.Container(
                padding=20,
                content=ft.Text("Nenhum histórico financeiro encontrado.", color=COLOR_TEXT_SECONDARY)
            )
        )
    else:
        for r in records:
            is_pago = r['status_pagamento'] == 'PAGO'
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
                                ft.Text(r['evento_nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                                ft.Text(f"Função: {r['funcao'].upper()} | Data: {date_to_br(r['data_inicio'])}", size=13, color=COLOR_TEXT_SECONDARY),
                            ]
                        ),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=4,
                            controls=[
                                ft.Text(f"R$ {r['valor_diaria']:.2f}", size=16, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                                ft.Container(
                                    content=ft.Text("RECEBIDO" if is_pago else "A RECEBER", size=10, color="#000000", weight=ft.FontWeight.BOLD),
                                    bgcolor=COLOR_SUCCESS if is_pago else COLOR_WARNING,
                                    padding=5,
                                    border_radius=6
                                )
                            ]
                        )
                    ]
                )
            )
            list_container.controls.append(card)

    return ft.Container(
        expand=True,
        padding=25,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                ft.Row(controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                    ft.Text("Meu Extrato / Extrato Financeiro", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                ]),
                list_container
            ]
        )
    )
