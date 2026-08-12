import flet as ft
from config.settings import (
    COLOR_SURFACE, COLOR_PRIMARY, COLOR_TEXT_PRIMARY, 
    COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO
)
from services.saas_metrics_service import (
    get_saas_metrics_summary, get_companies_list_for_saas, 
    create_company_by_dev, update_company_status, delete_company_completely
)

def SuperAdminDashboardView(page: ft.Page, user: dict, on_logout):
    metrics_container = ft.Row(wrap=True, spacing=15, alignment=ft.MainAxisAlignment.START)
    list_companies = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    # Campos de formulário
    txt_nome = ft.TextField(label="Nome Fantasia", border_color=COLOR_TEXT_SECONDARY, expand=True)
    txt_cnpj = ft.TextField(label="CNPJ / Documento", border_color=COLOR_TEXT_SECONDARY, expand=True)
    txt_email = ft.TextField(label="E-mail do Admin", border_color=COLOR_TEXT_SECONDARY, expand=True)
    txt_senha = ft.TextField(label="Senha do Admin", password=True, border_color=COLOR_TEXT_SECONDARY, expand=True)

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=COLOR_ERROR if is_error else COLOR_SUCCESS)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def handle_quick_register(_):
        if not txt_nome.value or not txt_email.value or not txt_senha.value:
            show_snack("Preencha Nome, E-mail e Senha para prosseguir!")
            return
        
        success, msg = create_company_by_dev(
            txt_nome.value.strip(),
            txt_cnpj.value.strip(),
            txt_email.value.strip(),
            txt_senha.value.strip()
        )
        show_snack(msg, is_error=not success)
        if success:
            txt_nome.value = ""
            txt_cnpj.value = ""
            txt_email.value = ""
            txt_senha.value = ""
            reload_data()

    def handle_change_status(empresa_id, status):
        update_company_status(empresa_id, status)
        show_snack(f"Status alterado para {status}!", is_error=False)
        reload_data()

    def handle_delete_company(empresa_id, nome_fantasia):
        def confirm_delete(_):
            delete_company_completely(empresa_id)
            dlg.open = False
            show_snack(f"Empresa '{nome_fantasia}' e seus dados foram excluídos com sucesso!", is_error=False)
            page.update()
            reload_data()

        dlg = ft.AlertDialog(
            title=ft.Text("⚠️ Confirmar Exclusão Definitiva"),
            content=ft.Text(f"Tem certeza que deseja apagar a empresa '{nome_fantasia}' (ID: {empresa_id})?\nEsta ação removerá todos os eventos, usuários e registros vinculados a ela!"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, 'open', False) or page.update()),
                ft.ElevatedButton("Excluir Definitivamente", style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color="#FFFFFF"), on_click=confirm_delete)
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def reload_data():
        metrics_container.controls.clear()
        list_companies.controls.clear()
        
        m = get_saas_metrics_summary()

        card_mrr = build_metric_card("Faturamento Mês", f"R$ {m['faturamento_mes_atual']:.2f}", ft.Icons.ATTACH_MONEY, COLOR_SUCCESS)
        card_total_rev = build_metric_card("Faturamento Total", f"R$ {m['faturamento_total']:.2f}", ft.Icons.ACCOUNT_BALANCE_WALLET, COLOR_PRIMARY)
        card_active_comp = build_metric_card("Empresas Ativas", f"{m['empresas_ativas']} / {m['total_empresas']}", ft.Icons.BUSINESS, COLOR_INFO)
        card_susp_comp = build_metric_card("Empresas Suspensas", f"{m['empresas_suspensas']}", ft.Icons.WARNING_AMBER, COLOR_ERROR)
        card_staffs = build_metric_card("Staffs Cadastrados", f"{m['total_staffs']}", ft.Icons.PEOPLE, COLOR_TEXT_PRIMARY)

        metrics_container.controls.extend([card_mrr, card_total_rev, card_active_comp, card_susp_comp, card_staffs])

        companies = get_companies_list_for_saas()
        if not companies:
            list_companies.controls.append(ft.Text("Nenhuma empresa cadastrada no sistema.", color=COLOR_TEXT_SECONDARY))
        else:
            for comp in companies:
                st = str(comp.get("status", "PENDENTE")).upper()
                
                # Badge de Status
                if st == "ATIVO":
                    bg_st = COLOR_SUCCESS
                elif st == "SUSPENSO":
                    bg_st = "#D97706" # Laranja
                else:
                    bg_st = COLOR_ERROR

                # Botões de Ação por Empresa
                btn_ativar = ft.TextButton("Ativar 🟢", on_click=lambda _, eid=comp['id']: handle_change_status(eid, "ATIVO"))
                btn_suspender = ft.TextButton("Suspender 🟡", on_click=lambda _, eid=comp['id']: handle_change_status(eid, "SUSPENSO"))
                btn_excluir = ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color=COLOR_ERROR, tooltip="Excluir Empresa", on_click=lambda _, eid=comp['id'], nm=comp['nome_fantasia']: handle_delete_company(eid, nm))

                card_c = ft.Container(
                    bgcolor=COLOR_SURFACE, padding=15, border_radius=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(spacing=4, controls=[
                                ft.Text(f"🏢 {comp['nome_fantasia']} (ID: {comp['id']})", weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT_PRIMARY),
                                ft.Text(f"📄 CNPJ: {comp.get('cnpj') or 'N/I'} | Users: {comp['total_usuarios']}", size=12, color=COLOR_TEXT_SECONDARY),
                                ft.Text(f"🎪 Eventos Criados: {comp['total_eventos']}", size=12, color=COLOR_PRIMARY)
                            ]),
                            ft.Row(controls=[
                                ft.Container(
                                    content=ft.Text(f"Status: {st}", size=12, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                    bgcolor=bg_st, padding=8, border_radius=6
                                ),
                                btn_ativar,
                                btn_suspender,
                                btn_excluir
                            ], spacing=5)
                        ]
                    )
                )
                list_companies.controls.append(card_c)
        page.update()

    def build_metric_card(title, value, icon_data, color_accent):
        return ft.Container(
            bgcolor=COLOR_SURFACE, padding=20, border_radius=10, width=210,
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Row(controls=[
                        ft.Icon(icon_data, color=color_accent, size=22),
                        ft.Text(title, size=11, color=COLOR_TEXT_SECONDARY, weight=ft.FontWeight.BOLD)
                    ]),
                    ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
                ]
            )
        )

    reload_data()

    return ft.Container(
        expand=True, padding=20,
        content=ft.Column(
            expand=True, spacing=15, scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(controls=[
                            ft.Text("Painel do Desenvolvedor — Gestão Total SaaS", size=22, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                            ft.Text("Controle Absoluto: Adicionar, Ativar, Suspender e Excluir Produtoras", size=13, color=COLOR_TEXT_SECONDARY)
                        ]),
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.REFRESH, tooltip="Atualizar Dados", icon_color=COLOR_PRIMARY, on_click=lambda _: reload_data()),
                            ft.IconButton(ft.Icons.LOGOUT, tooltip="Sair", icon_color=COLOR_ERROR, on_click=lambda _: on_logout())
                        ])
                    ]
                ),
                metrics_container,
                ft.Divider(color="#334155"),
                
                # Formulário de Cadastro Direto
                ft.Container(
                    bgcolor=COLOR_SURFACE, padding=15, border_radius=10,
                    content=ft.Column(spacing=10, controls=[
                        ft.Text("⚡ Criar Nova Empresa (Acesso Direto Sem Cobrança)", size=15, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                        ft.Row(controls=[txt_nome, txt_cnpj]),
                        ft.Row(controls=[txt_email, txt_senha]),
                        ft.ElevatedButton(
                            "Cadastrar Empresa Agora", icon=ft.Icons.ADD_BUSINESS,
                            style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color="#FFFFFF"),
                            on_click=handle_quick_register
                        )
                    ])
                ),

                ft.Divider(color="#334155"),
                ft.Text("Gerenciamento de Produtoras Cadastradas", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                list_companies
            ]
        )
    )