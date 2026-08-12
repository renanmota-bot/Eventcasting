import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_INFO
)
from services.event_service import create_event, get_all_events, update_event_status
from views.admin.vagas import AdminVagasView
from views.admin.escala_evento import AdminEscalaEventoView
from utils.formatters import date_to_iso, date_to_br

def AdminEventosView(page: ft.Page, on_back):
    selected_status = "TODOS"
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    txt_nome = ft.TextField(label="Nome do Evento", border_color=COLOR_PRIMARY, text_size=13)
    txt_data_inicio = ft.TextField(label="Data Início (DD/MM/AAAA)", border_color=COLOR_PRIMARY, text_size=13)
    txt_data_fim = ft.TextField(label="Data Fim (DD/MM/AAAA)", border_color=COLOR_PRIMARY, text_size=13)
    txt_hora_inicio = ft.TextField(label="Hora Início (Ex: 08:00)", border_color=COLOR_PRIMARY, text_size=13)
    txt_hora_fim = ft.TextField(label="Hora Fim (Ex: 18:00)", border_color=COLOR_PRIMARY, text_size=13)
    txt_local = ft.TextField(label="Local (Ex: Allianz Parque)", border_color=COLOR_PRIMARY, text_size=13)
    txt_endereco = ft.TextField(label="Endereço Completo", border_color=COLOR_PRIMARY, text_size=13)
    txt_cidade = ft.TextField(label="Cidade", border_color=COLOR_PRIMARY, text_size=13)
    txt_estado = ft.TextField(label="Estado (Ex: SP)", border_color=COLOR_PRIMARY, text_size=13)
    txt_obs = ft.TextField(label="Observações", border_color=COLOR_PRIMARY, text_size=13)

    lbl_form_msg = ft.Text("", size=13, weight=ft.FontWeight.W_500)

    def get_status_color(status):
        if status == "PUBLICADO": return COLOR_INFO
        if status == "CONCLUIDO": return COLOR_SUCCESS
        if status == "CANCELADO": return COLOR_ERROR
        return COLOR_WARNING

    def reload_events_list():
        list_container.controls.clear()
        events = get_all_events(selected_status)

        if not events:
            list_container.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhum evento encontrado nesta categoria.", color=COLOR_TEXT_SECONDARY)
                )
            )
        else:
            for ev in events:
                e_id = ev['id']
                e_status = ev['status']
                ev_data = ev

                dt_ini = date_to_br(ev['data_inicio'])
                dt_fim = date_to_br(ev['data_fim'])

                actions = [
                    ft.Button(
                        "Vagas",
                        style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"),
                        on_click=lambda _, event_obj=ev_data: open_vagas_view(event_obj)
                    ),
                    ft.Button(
                        "Ver Equipe Escalada",
                        style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"),
                        on_click=lambda _, event_obj=ev_data: open_escala_view(event_obj)
                    )
                ]

                if e_status == "PUBLICADO":
                    actions.extend([
                        ft.Button(
                            "Concluir",
                            style=ft.ButtonStyle(bgcolor=COLOR_WARNING, color="#000000"),
                            on_click=lambda _, eid=e_id: change_status(eid, "CONCLUIDO")
                        ),
                        ft.Button(
                            "Cancelar",
                            style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color="#FFFFFF"),
                            on_click=lambda _, eid=e_id: change_status(eid, "CANCELADO")
                        )
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
                                        ft.Text(ev['nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                                        ft.Container(
                                            content=ft.Text(e_status, size=11, color="#000000", weight=ft.FontWeight.BOLD),
                                            bgcolor=get_status_color(e_status),
                                            padding=6,
                                            border_radius=10
                                        )
                                    ]),
                                    ft.Text(f"Data: {dt_ini} até {dt_fim} | Horário: {ev['hora_inicio']} às {ev['hora_fim']}", size=13, color=COLOR_PRIMARY),
                                    ft.Text(f"Local: {ev['local']} — {ev['endereco']} ({ev['cidade']}/{ev['estado']})", size=12, color=COLOR_TEXT_SECONDARY),
                                ]
                            ),
                            ft.Row(controls=actions, spacing=8)
                        ]
                    )
                )
                list_container.controls.append(card)
        page.update()

    def open_vagas_view(event):
        page.clean()
        page.add(AdminVagasView(page, event, on_back=lambda: (page.clean(), page.add(AdminEventosView(page, on_back)), page.update())))
        page.update()

    def open_escala_view(event):
        page.clean()
        page.add(AdminEscalaEventoView(page, event, on_back=lambda: (page.clean(), page.add(AdminEventosView(page, on_back)), page.update())))
        page.update()

    def change_status(event_id, new_status):
        if update_event_status(event_id, new_status):
            reload_events_list()

    def close_dialog(e=None):
        dialog_form.open = False
        page.update()

    def handle_create_event(e):
        lbl_form_msg.value = ""
        fields = [txt_nome, txt_data_inicio, txt_data_fim, txt_hora_inicio, txt_hora_fim, txt_local, txt_endereco, txt_cidade, txt_estado]
        if any(not f.value for f in fields):
            lbl_form_msg.value = "Preencha todos os campos obrigatórios."
            lbl_form_msg.color = COLOR_ERROR
            page.update()
            return

        data = {
            "nome": txt_nome.value, 
            "data_inicio": date_to_iso(txt_data_inicio.value), 
            "data_fim": date_to_iso(txt_data_fim.value),
            "hora_inicio": txt_hora_inicio.value, 
            "hora_fim": txt_hora_fim.value,
            "local": txt_local.value, 
            "endereco": txt_endereco.value,
            "cidade": txt_cidade.value, 
            "estado": txt_estado.value, 
            "observacoes": txt_obs.value
        }

        success, msg = create_event(data)
        if success:
            for f in fields: f.value = ""
            txt_obs.value = ""
            close_dialog()
            reload_events_list()
        else:
            lbl_form_msg.value = msg
            lbl_form_msg.color = COLOR_ERROR
            page.update()

    dialog_form = ft.AlertDialog(
        title=ft.Text("Cadastrar Novo Evento", color=COLOR_TEXT_PRIMARY, size=18, weight=ft.FontWeight.BOLD),
        content=ft.Container(
            width=450,
            padding=10,
            content=ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                tight=True,
                controls=[
                    txt_nome, txt_data_inicio, txt_data_fim,
                    txt_hora_inicio, txt_hora_fim, txt_local,
                    txt_endereco, txt_cidade, txt_estado, txt_obs,
                    lbl_form_msg
                ]
            )
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=close_dialog),
            ft.Button("Salvar Evento", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=handle_create_event)
        ]
    )

    def open_new_event_dialog(e):
        page.overlay.append(dialog_form)
        dialog_form.open = True
        page.update()

    def filter_changed(e):
        nonlocal selected_status
        selected_status = filter_dropdown.value
        reload_events_list()

    filter_dropdown = ft.Dropdown(
        value="TODOS",
        width=180,
        options=[
            ft.dropdown.Option("TODOS"),
            ft.dropdown.Option("PUBLICADO"),
            ft.dropdown.Option("CONCLUIDO"),
            ft.dropdown.Option("CANCELADO"),
        ]
    )
    filter_dropdown.on_change = filter_changed

    reload_events_list()

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
                            ft.Text("Gestão de Eventos", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                        ]),
                        ft.Row(controls=[
                            filter_dropdown,
                            ft.Button("+ Novo Evento", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=open_new_event_dialog)
                        ])
                    ]
                ),
                list_container
            ]
        )
    )
