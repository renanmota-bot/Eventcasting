from datetime import datetime
import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO
)
from services.event_service import get_company_events, create_event
from services.job_service import get_event_jobs, create_job
from services.admin_candidacy_service import get_event_candidacies, update_candidacy_status
from services.checkin_service import get_approved_staff_for_event, register_checkin, register_checkout
from services.financial_service import get_financial_summary_by_event, get_event_payroll
from services.export_service import export_payroll_pdf
from services.cep_service import fetch_address_by_cep

def AdminDashboardView(page: ft.Page, user: dict, on_navigate, on_logout):
    empresa_id = user.get('empresa_id')
    selected_event = None
    selected_financial_event = None
    active_tab = "eventos"

    # Campos do Evento
    txt_nome = ft.TextField(
        label="Nome do Evento", border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )

    def format_cep(e):
        val = "".join(filter(str.isdigit, e.control.value or ""))[:8]
        if len(val) > 5:
            e.control.value = val[:5] + "-" + val[5:]
        else:
            e.control.value = val
        page.update()
        if len(val) == 8:
            addr = fetch_address_by_cep(val)
            if addr:
                txt_endereco.value = addr["logradouro"]
                txt_bairro.value = addr["bairro"]
                txt_cidade.value = addr["cidade"]
                txt_estado.value = addr["uf"]
                show_snack("Endereço do evento localizado via CEP!", is_error=False)
                page.update()

    txt_cep = ft.TextField(
        label="CEP do Local", max_length=9, border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY),
        on_change=format_cep
    )

    txt_endereco = ft.TextField(
        label="Endereço / Logradouro", border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_numero = ft.TextField(
        label="Número", border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_bairro = ft.TextField(
        label="Bairro", border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_cidade = ft.TextField(
        label="Cidade", border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )
    txt_estado = ft.TextField(
        label="UF", max_length=2, border_color=COLOR_TEXT_SECONDARY, 
        text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY)
    )

    def format_date_input(e):
        value = "".join(filter(str.isdigit, e.control.value or ""))[:8]
        formatted = ""
        if len(value) > 0: formatted = value[:2]
        if len(value) >= 3: formatted += "/" + value[2:4]
        if len(value) >= 5: formatted += "/" + value[4:8]
        e.control.value = formatted
        page.update()

    txt_data_inicio = ft.TextField(
        label="Data Início (DD/MM/AAAA)", hint_text="DD/MM/AAAA", max_length=10,
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY),
        on_change=format_date_input
    )
    txt_data_fim = ft.TextField(
        label="Data Fim (DD/MM/AAAA)", hint_text="DD/MM/AAAA", max_length=10,
        border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY,
        text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY),
        label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY),
        on_change=format_date_input
    )

    # Campos de Vaga
    txt_funcao = ft.TextField(label="Função (Ex: Recepcionista)", border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY))
    txt_diaria = ft.TextField(label="Valor Diária (R$)", border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY))
    txt_qtd = ft.TextField(label="Qtd. Vagas", border_color=COLOR_TEXT_SECONDARY, text_size=14, color=COLOR_TEXT_PRIMARY, text_style=ft.TextStyle(color=COLOR_TEXT_PRIMARY), label_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY))

    list_eventos = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    list_jobs = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
    list_candidaturas = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    list_presenca = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    list_financial = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    payroll_details = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
    
    main_content_area = ft.Container(expand=True)
    jobs_area = ft.Container(visible=False)
    payroll_area = ft.Container(visible=False)

    def open_jobs_management(ev):
        nonlocal selected_event
        selected_event = ev
        reload_jobs()
        jobs_area.visible = True
        page.update()

    def close_jobs_management(_):
        nonlocal selected_event
        selected_event = None
        jobs_area.visible = False
        page.update()

    def open_payroll_details(ev_id, ev_nome):
        nonlocal selected_financial_event
        selected_financial_event = {"id": ev_id, "nome": ev_nome}
        reload_payroll()
        payroll_area.visible = True
        page.update()

    def close_payroll_details(_):
        nonlocal selected_financial_event
        selected_financial_event = None
        payroll_area.visible = False
        page.update()

    def reload_events():
        list_eventos.controls.clear()
        eventos = get_company_events(empresa_id)
        for ev in eventos:
            d_inicio_str = str(ev['data_inicio'])
            d_fim_str = str(ev['data_fim'])
            try:
                d_inicio_br = datetime.strptime(d_inicio_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                d_fim_br = datetime.strptime(d_fim_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                d_inicio_br, d_fim_br = d_inicio_str, d_fim_str

            loc_formatada = f"{ev.get('endereco') or ev.get('local') or ''}, {ev.get('numero') or ''} - {ev.get('bairro') or ''} ({ev.get('cidade') or ''}/{ev.get('estado') or ''})"

            card = ft.Container(
                bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=4, controls=[
                            ft.Text(ev['nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                            ft.Text(f"📍 {loc_formatada}", size=13, color=COLOR_TEXT_SECONDARY),
                            ft.Text(f"📅 {d_inicio_br} até {d_fim_br}", size=12, color=COLOR_PRIMARY)
                        ]),
                        ft.ElevatedButton("Vagas", icon=ft.Icons.WORK, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=lambda _, e=ev: open_jobs_management(e))
                    ]
                )
            )
            list_eventos.controls.append(card)

    def reload_jobs():
        if not selected_event: return
        list_jobs.controls.clear()
        jobs = get_event_jobs(selected_event['id'])
        for j in jobs:
            c = ft.Container(
                bgcolor="#0F172A", padding=10, border_radius=6,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"• {j['funcao']} ({j['quantidade']} vagas) — R$ {j['valor_diaria']}", color=COLOR_TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                        ft.Text(j['status'], size=11, color=COLOR_PRIMARY)
                    ]
                )
            )
            list_jobs.controls.append(c)

    def reload_candidacies():
        list_candidaturas.controls.clear()
        cands = get_event_candidacies(empresa_id)
        if not cands:
            list_candidaturas.controls.append(ft.Text("Nenhuma candidatura recebida.", color=COLOR_TEXT_SECONDARY))
            return

        for c in cands:
            status = str(c['status_candidatura']).upper()
            cid = c['candidatura_id']
            foto_b64 = c.get('foto_base64')

            if foto_b64:
                avatar = ft.CircleAvatar(foreground_image_src=f"data:image/jpeg;base64,{foto_b64}", radius=28)
            else:
                avatar = ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON, color=COLOR_TEXT_PRIMARY), bgcolor="#0F172A", radius=28)

            actions = ft.Row(controls=[
                ft.ElevatedButton("Aprovar", style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"), on_click=lambda e, cand_id=cid: handle_update_cand(cand_id, 'APROVADO')),
                ft.ElevatedButton("Recusar", style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color="#FFFFFF"), on_click=lambda e, cand_id=cid: handle_update_cand(cand_id, 'RECUSADO'))
            ], spacing=8) if status == 'PENDENTE' else ft.Text(status, color=COLOR_SUCCESS if status == 'APROVADO' else COLOR_ERROR, weight=ft.FontWeight.BOLD)

            card = ft.Container(
                bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(spacing=15, controls=[
                            avatar,
                            ft.Column(spacing=4, controls=[
                                ft.Text(f"{c['staff_nome']} — {c['funcao']}", weight=ft.FontWeight.BOLD, size=15, color=COLOR_TEXT_PRIMARY),
                                ft.Text(f"🎪 Evento: {c['evento_nome']} | Diária: R$ {c['valor_diaria']}", size=12, color=COLOR_PRIMARY),
                                ft.Text(f"📱 Whats: {c['staff_whatsapp']} | Pix: {c['chave_pix'] or 'N/A'}", size=12, color=COLOR_TEXT_SECONDARY)
                            ])
                        ]),
                        actions
                    ]
                )
            )
            list_candidaturas.controls.append(card)

    def reload_presence():
        list_presenca.controls.clear()
        staff_approved = get_approved_staff_for_event(empresa_id)
        if not staff_approved:
            list_presenca.controls.append(ft.Text("Nenhum colaborador aprovado na equipe.", color=COLOR_TEXT_SECONDARY))
            return
        for s in staff_approved:
            cid = s['candidatura_id']
            in_time = s['checkin'].strftime("%H:%M") if s['checkin'] else "—"
            out_time = s['checkout'].strftime("%H:%M") if s['checkout'] else "—"

            btn_in = ft.ElevatedButton("Check-in", style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS if not s['checkin'] else COLOR_SURFACE, color="#FFFFFF"), disabled=bool(s['checkin']), on_click=lambda e, cand_id=cid: handle_checkin(cand_id))
            btn_out = ft.ElevatedButton("Check-out", style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY if s['checkin'] and not s['checkout'] else COLOR_SURFACE, color="#FFFFFF"), disabled=not bool(s['checkin']) or bool(s['checkout']), on_click=lambda e, cand_id=cid: handle_checkout(cand_id))

            card = ft.Container(
                bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=4, controls=[
                            ft.Text(f"{s['staff_nome']} ({s['funcao']})", weight=ft.FontWeight.BOLD, size=15, color=COLOR_TEXT_PRIMARY),
                            ft.Text(f"🎪 Evento: {s['evento_nome']}", size=12, color=COLOR_PRIMARY),
                            ft.Text(f"⏱️ Entrada: {in_time} | Saída: {out_time}", size=12, color=COLOR_TEXT_SECONDARY)
                        ]),
                        ft.Row(controls=[btn_in, btn_out], spacing=8)
                    ]
                )
            )
            list_presenca.controls.append(card)

    def reload_financial():
        list_financial.controls.clear()
        summary = get_financial_summary_by_event(empresa_id)
        if not summary:
            list_financial.controls.append(ft.Text("Nenhum registro financeiro disponível.", color=COLOR_TEXT_SECONDARY))
            return
        for s in summary:
            card = ft.Container(
                bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=4, controls=[
                            ft.Text(s['evento_nome'], weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                            ft.Text(f"👥 Equipe Confirmada: {s['total_aprovados']} colaboradores", size=13, color=COLOR_TEXT_SECONDARY),
                            ft.Text(f"💰 Custo Total de Diárias: R$ {s['total_investido']:.2f}", size=13, color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD)
                        ]),
                        ft.ElevatedButton("Ver Folha Pix", icon=ft.Icons.ATTACH_MONEY, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=lambda _, eid=s['evento_id'], enome=s['evento_nome']: open_payroll_details(eid, enome))
                    ]
                )
            )
            list_financial.controls.append(card)

    def reload_payroll():
        if not selected_financial_event: return
        payroll_details.controls.clear()
        p_list = get_event_payroll(selected_financial_event['id'])
        for p in p_list:
            c = ft.Container(
                bgcolor="#0F172A", padding=12, border_radius=6,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=2, controls=[
                            ft.Text(f"{p['staff_nome']} ({p['funcao']})", color=COLOR_TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                            ft.Text(f"🔑 Pix: {p['chave_pix'] or 'Não informado'}", color=COLOR_PRIMARY, size=12)
                        ]),
                        ft.Text(f"R$ {p['valor_diaria']:.2f}", color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD, size=15)
                    ]
                )
            )
            payroll_details.controls.append(c)

    def handle_export_pdf(_):
        if not selected_financial_event: return
        try:
            filepath = export_payroll_pdf(selected_financial_event['id'], selected_financial_event['nome'])
            show_snack("PDF salvo com sucesso na sua pasta Downloads!", is_error=False)
        except Exception as ex:
            show_snack(f"Erro ao gerar PDF: {ex}")

    def handle_checkin(cid):
        if register_checkin(cid):
            show_snack("Check-in registrado!", is_error=False)
            reload_presence()
            page.update()

    def handle_checkout(cid):
        if register_checkout(cid):
            show_snack("Check-out registrado!", is_error=False)
            reload_presence()
            page.update()

    def handle_update_cand(cid, novo_status):
        if update_candidacy_status(cid, novo_status):
            msg_status = "aprovada" if novo_status == "APROVADO" else "recusada"
            show_snack(f"Candidatura {msg_status} com sucesso!", is_error=False)
        else:
            show_snack("Erro ao atualizar status.")
        reload_candidacies()
        page.update()

    def handle_create_job(_):
        if not selected_event: return
        funcao = txt_funcao.value.strip() if txt_funcao.value else ""
        diaria = txt_diaria.value.strip() if txt_diaria.value else ""
        qtd = txt_qtd.value.strip() if txt_qtd.value else ""
        if not all([funcao, diaria, qtd]):
            show_snack("Preencha todos os campos da vaga.")
            return
        try:
            val_diaria = float(diaria.replace(",", "."))
            val_qtd = int(qtd)
        except ValueError:
            show_snack("Valores inválidos.")
            return
        if create_job(selected_event['id'], funcao, val_diaria, val_qtd):
            show_snack("Vaga cadastrada com sucesso!", is_error=False)
            txt_funcao.value = ""
            txt_diaria.value = ""
            txt_qtd.value = ""
            reload_jobs()
            page.update()

    def handle_create_event(_):
        d_inicio_br = txt_data_inicio.value.strip() if txt_data_inicio.value else ""
        d_fim_br = txt_data_fim.value.strip() if txt_data_fim.value else ""
        nome_ev = txt_nome.value.strip() if txt_nome.value else ""
        
        if not all([nome_ev, d_inicio_br, d_fim_br, txt_cidade.value]):
            show_snack("Preencha o nome, datas e endereço/cidade do evento.")
            return
        try:
            d_inicio_iso = datetime.strptime(d_inicio_br, "%d/%m/%Y").strftime("%Y-%m-%d")
            d_fim_iso = datetime.strptime(d_fim_br, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            show_snack("Data inválida. Use DD/MM/AAAA.")
            return

        loc_completa = f"{txt_endereco.value or ''}, {txt_numero.value or 'S/N'} - {txt_bairro.value or ''} ({txt_cidade.value or ''}/{txt_estado.value or ''})"

        if create_event(
            empresa_id=empresa_id, 
            nome=nome_ev, 
            local=loc_completa, 
            data_inicio=d_inicio_iso, 
            data_fim=d_fim_iso,
            cep=txt_cep.value.strip() if txt_cep.value else "",
            endereco=txt_endereco.value.strip() if txt_endereco.value else "",
            numero=txt_numero.value.strip() if txt_numero.value else "",
            bairro=txt_bairro.value.strip() if txt_bairro.value else "",
            cidade=txt_cidade.value.strip() if txt_cidade.value else "",
            estado=txt_estado.value.strip().upper() if txt_estado.value else ""
        ):
            show_snack("Evento cadastrado com sucesso!", is_error=False)
            txt_nome.value = ""
            txt_cep.value = ""
            txt_endereco.value = ""
            txt_numero.value = ""
            txt_bairro.value = ""
            txt_cidade.value = ""
            txt_estado.value = ""
            txt_data_inicio.value = ""
            txt_data_fim.value = ""
            reload_events()
            render_tab()

    def handle_copy_staff_link(_):
        staff_link = f"https://eventcasting.app/register_staff?empresa_id={empresa_id}"
        page.set_clipboard(staff_link)
        show_snack(f"Link de cadastro para Staff copiado! (Produtora ID: {empresa_id})", is_error=False)

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
        btn_tab_eventos.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY if active_tab == "eventos" else COLOR_SURFACE, color="#000000" if active_tab == "eventos" else COLOR_TEXT_PRIMARY)
        btn_tab_candidaturas.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY if active_tab == "candidaturas" else COLOR_SURFACE, color="#000000" if active_tab == "candidaturas" else COLOR_TEXT_PRIMARY)
        btn_tab_presenca.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY if active_tab == "presenca" else COLOR_SURFACE, color="#000000" if active_tab == "presenca" else COLOR_TEXT_PRIMARY)
        btn_tab_financeiro.style = ft.ButtonStyle(bgcolor=COLOR_PRIMARY if active_tab == "financeiro" else COLOR_SURFACE, color="#000000" if active_tab == "financeiro" else COLOR_TEXT_PRIMARY)

        if active_tab == "eventos":
            main_content_area.content = ft.Column(
                expand=True, spacing=15,
                controls=[
                    ft.Container(
                        bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                        content=ft.Column(controls=[
                            ft.Text("Cadastrar Novo Evento com CEP", weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                            txt_nome,
                            ft.Row(controls=[txt_cep, txt_endereco, txt_numero], expand=True),
                            ft.Row(controls=[txt_bairro, txt_cidade, txt_estado], expand=True),
                            ft.Row(controls=[txt_data_inicio, txt_data_fim], expand=True),
                            ft.ElevatedButton("Salvar Evento", icon=ft.Icons.ADD, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=handle_create_event)
                        ])
                    ),
                    jobs_area,
                    ft.Text("Eventos Cadastrados", weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                    list_eventos
                ]
            )
        elif active_tab == "candidaturas":
            reload_candidacies()
            main_content_area.content = list_candidaturas
        elif active_tab == "presenca":
            reload_presence()
            main_content_area.content = list_presenca
        else:
            reload_financial()
            main_content_area.content = ft.Column(expand=True, spacing=10, controls=[payroll_area, list_financial])
        page.update()

    btn_tab_eventos = ft.ElevatedButton("Eventos", on_click=lambda _: set_tab("eventos"))
    btn_tab_candidaturas = ft.ElevatedButton("Candidaturas", on_click=lambda _: set_tab("candidaturas"))
    btn_tab_presenca = ft.ElevatedButton("Presença", on_click=lambda _: set_tab("presenca"))
    btn_tab_financeiro = ft.ElevatedButton("Financeiro", on_click=lambda _: set_tab("financeiro"))

    jobs_area.content = ft.Container(
        bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
        content=ft.Column(controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text("Gerenciar Vagas do Evento", size=16, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                ft.IconButton(ft.Icons.CLOSE, on_click=close_jobs_management)
            ]),
            ft.Row(controls=[txt_funcao, txt_diaria, txt_qtd], expand=True),
            ft.ElevatedButton("Adicionar Vaga", icon=ft.Icons.ADD_TASK, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="#000000"), on_click=handle_create_job),
            ft.Divider(color="#334155"),
            list_jobs
        ])
    )

    payroll_area.content = ft.Container(
        bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
        content=ft.Column(controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text("Folha de Pagamento (Chaves Pix)", size=16, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                ft.Row(controls=[
                    ft.ElevatedButton("Exportar PDF", icon=ft.Icons.PICTURE_AS_PDF, style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"), on_click=handle_export_pdf),
                    ft.IconButton(ft.Icons.CLOSE, on_click=close_payroll_details)
                ])
            ]),
            payroll_details
        ])
    )

    reload_events()
    render_tab()

    return ft.Container(
        expand=True, padding=20,
        content=ft.Column(
            expand=True, spacing=15,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(controls=[
                            ft.Text("Event Casting — Painel de Gestão", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                            ft.Text(f"Bem-vindo, {user.get('nome')}", size=13, color=COLOR_TEXT_SECONDARY)
                        ]),
                        ft.Row(controls=[
                            ft.ElevatedButton(
                                "Copiar Link de Staff", 
                                icon=ft.Icons.LINK,
                                style=ft.ButtonStyle(bgcolor=COLOR_SURFACE, color=COLOR_TEXT_PRIMARY),
                                on_click=handle_copy_staff_link
                            ),
                            ft.IconButton(ft.Icons.LOGOUT, tooltip="Sair", icon_color=COLOR_ERROR, on_click=lambda _: on_logout())
                        ])
                    ]
                ),
                ft.Row(controls=[btn_tab_eventos, btn_tab_candidaturas, btn_tab_presenca, btn_tab_financeiro], spacing=10),
                ft.Divider(color="#334155"),
                main_content_area
            ]
        )
    )