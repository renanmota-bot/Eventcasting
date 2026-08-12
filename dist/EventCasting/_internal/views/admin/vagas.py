import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
)
from services.job_service import create_job, get_jobs_by_event, update_job, delete_job
from views.admin.candidatos import AdminCandidatosView
from utils.formatters import date_to_br

def AdminVagasView(page: ft.Page, event: dict, on_back):
    editing_job_id = None
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    txt_funcao = ft.TextField(label="Função (Ex: Carregador)", border_color=COLOR_PRIMARY, text_size=13)
    txt_quantidade = ft.TextField(label="Quantidade de Vagas", border_color=COLOR_PRIMARY, text_size=13)
    txt_valor = ft.TextField(label="Valor Diária (R$)", border_color=COLOR_PRIMARY, text_size=13)
    txt_hora_inicio = ft.TextField(label="Horário Início (Ex: 08:00)", border_color=COLOR_PRIMARY, text_size=13)
    txt_hora_fim = ft.TextField(label="Horário Fim (Ex: 18:00)", border_color=COLOR_PRIMARY, text_size=13)
    txt_dias = ft.TextField(label="Quantidade de Dias", value="1", border_color=COLOR_PRIMARY, text_size=13)
    txt_descricao = ft.TextField(label="Descrição das Atividades", border_color=COLOR_PRIMARY, text_size=13)

    lbl_form_msg = ft.Text("", size=13, weight=ft.FontWeight.W_500)

    def reload_jobs_list():
        list_container.controls.clear()
        jobs = get_jobs_by_event(event['id'])

        if not jobs:
            list_container.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhuma vaga cadastrada para este evento ainda.", color=COLOR_TEXT_SECONDARY)
                )
            )
        else:
            for job in jobs:
                job_obj = job
                j_id = job['id']

                actions = [
                    ft.IconButton(ft.Icons.EDIT, icon_color=COLOR_PRIMARY, tooltip="Editar Vaga", on_click=lambda _, j=job_obj: open_edit_dialog(j)),
                    ft.IconButton(ft.Icons.DELETE, icon_color=COLOR_ERROR, tooltip="Excluir Vaga", on_click=lambda _, jid=j_id: confirm_delete(jid)),
                    ft.Button("Ver Candidatos", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=lambda _, j=job_obj: open_candidatos_view(j))
                ]

                card = ft.Container(
                    bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(job['funcao'].upper(), weight=ft.FontWeight.BOLD, size=16, color=COLOR_PRIMARY),
                                    ft.Text(f"Vagas: {job['quantidade']} profissionais | Valor: R$ {job['valor_diaria']:.2f}/dia", size=13, color=COLOR_TEXT_PRIMARY),
                                    ft.Text(f"Horário: {job['horario_inicio']} às {job['horario_fim']}", size=12, color=COLOR_TEXT_SECONDARY),
                                ]
                            ),
                            ft.Row(controls=actions, spacing=4)
                        ]
                    )
                )
                list_container.controls.append(card)
        page.update()

    def open_candidatos_view(job):
        page.clean()
        page.add(AdminCandidatosView(page, job, event, on_back=lambda: (page.clean(), page.add(AdminVagasView(page, event, on_back)), page.update())))
        page.update()

    def confirm_delete(job_id):
        def do_delete(_):
            delete_job(job_id)
            dialog_confirm.open = False
            reload_jobs_list()

        dialog_confirm = ft.AlertDialog(
            title=ft.Text("Excluir Vaga"),
            content=ft.Text("Tem certeza que deseja excluir esta vaga? As candidaturas vinculadas serão removidas."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dialog_confirm, 'open', False) or page.update()),
                ft.Button("Excluir", style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color="#FFFFFF"), on_click=do_delete)
            ]
        )
        page.overlay.append(dialog_confirm)
        dialog_confirm.open = True
        page.update()

    def open_edit_dialog(job):
        nonlocal editing_job_id
        editing_job_id = job['id']
        txt_funcao.value = job['funcao']
        txt_quantidade.value = str(job['quantidade'])
        txt_valor.value = str(job['valor_diaria'])
        txt_hora_inicio.value = job['horario_inicio']
        txt_hora_fim.value = job['horario_fim']
        txt_dias.value = str(job.get('quantidade_dias', 1))
        txt_descricao.value = job.get('descricao', '')

        dialog_form.title.value = "Editar Vaga"
        page.overlay.append(dialog_form)
        dialog_form.open = True
        page.update()

    def open_new_job_dialog(_=None):
        nonlocal editing_job_id
        editing_job_id = None
        fields = [txt_funcao, txt_quantidade, txt_valor, txt_hora_inicio, txt_hora_fim, txt_descricao]
        for f in fields: f.value = ""
        txt_dias.value = "1"
        dialog_form.title.value = "Nova Vaga"
        page.overlay.append(dialog_form)
        dialog_form.open = True
        page.update()

    def handle_save_job(e):
        lbl_form_msg.value = ""
        fields = [txt_funcao, txt_quantidade, txt_valor, txt_hora_inicio, txt_hora_fim]
        if any(not f.value for f in fields):
            lbl_form_msg.value = "Preencha todos os campos obrigatórios."
            lbl_form_msg.color = COLOR_ERROR
            page.update()
            return

        try:
            qty = int(txt_quantidade.value)
            val = float(txt_valor.value.replace(",", "."))
            dias = int(txt_dias.value or "1")
        except ValueError:
            lbl_form_msg.value = "Quantidade e Valor devem ser números válidos."
            lbl_form_msg.color = COLOR_ERROR
            page.update()
            return

        data = {
            "evento_id": event['id'], "funcao": txt_funcao.value,
            "quantidade": qty, "valor_diaria": val, "quantidade_dias": dias,
            "horario_inicio": txt_hora_inicio.value, "horario_fim": txt_hora_fim.value,
            "descricao": txt_descricao.value
        }

        if editing_job_id:
            success, msg = update_job(editing_job_id, data)
        else:
            success, msg = create_job(data)

        if success:
            dialog_form.open = False
            reload_jobs_list()
        else:
            lbl_form_msg.value = msg
            lbl_form_msg.color = COLOR_ERROR
            page.update()

    dialog_form = ft.AlertDialog(
        title=ft.Text(f"Vaga: {event['nome']}", color=COLOR_TEXT_PRIMARY, size=18, weight=ft.FontWeight.BOLD),
        content=ft.Container(
            width=450, padding=10,
            content=ft.Column(
                spacing=10, scroll=ft.ScrollMode.AUTO, tight=True,
                controls=[
                    txt_funcao, txt_quantidade, txt_valor,
                    txt_hora_inicio, txt_hora_fim, txt_dias,
                    txt_descricao, lbl_form_msg
                ]
            )
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: setattr(dialog_form, 'open', False) or page.update()),
            ft.Button("Salvar Vaga", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=handle_save_job)
        ]
    )

    reload_jobs_list()
    dt_ini = date_to_br(event.get('data_inicio'))

    return ft.Container(
        expand=True, padding=25,
        content=ft.Column(
            expand=True, spacing=20,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: on_back()),
                            ft.Column(spacing=2, controls=[
                                ft.Text(f"Vagas do Evento: {event['nome']}", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                                ft.Text(f"{event['local']} ({dt_ini})", size=13, color=COLOR_TEXT_SECONDARY)
                            ])
                        ]),
                        ft.Button("+ Adicionar Vaga", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=open_new_job_dialog)
                    ]
                ),
                list_container
            ]
        )
    )