import flet as ft
from datetime import datetime

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query


def StaffDashboardView(page: ft.Page, user=None, on_logout=None, on_navigate=None):
    usuario_id = user.get('id') if user else None
    nome_staff = user.get('nome', 'Colaborador') if user else 'Colaborador'
    empresa_id = user.get('empresa_id') if user else None

    def init_staff_schema():
        try:
            execute_query("""
                ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS chave_pix VARCHAR(100);
                ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nota_media NUMERIC(3,2) DEFAULT 5.00;
            """, commit=True)
        except Exception:
            pass

    init_staff_schema()

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg, color="white", weight="bold"), bgcolor="#E76F51" if is_error else "#2A9D8F")
        page.overlay.append(snack)
        snack.open = True
        page.update()

    list_vagas_disponiveis = ft.Column(spacing=10)
    list_meus_eventos = ft.Column(spacing=10)
    list_caches_pendentes = ft.Column(spacing=8)
    list_caches_pagos = ft.Column(spacing=8)

    txt_chave_pix = ft.TextField(label="Sua Chave Pix (CPF, E-mail, Celular)", text_size=13, border_radius=8, expand=True)
    lbl_nota_staff = ft.Text("⭐ 5.0 / 5.0", size=16, weight="bold", color="#4CC9F0")

    txt_total_a_receber = ft.Text("R$ 0,00", size=18, weight="bold", color="#E76F51")
    txt_total_recebido = ft.Text("R$ 0,00", size=18, weight="bold", color="#2A9D8F")

    def carregar_perfil():
        if not usuario_id: return
        try:
            res = execute_query("SELECT chave_pix, COALESCE(nota_media, 5.00) as nota FROM usuarios WHERE id = %s;", (usuario_id,), fetch_all=True)
            if res:
                usr = res[0]
                if usr.get('chave_pix'):
                    txt_chave_pix.value = usr['chave_pix']
                lbl_nota_staff.value = f"⭐ {float(usr['nota']):.1f} / 5.0"
                page.update()
        except Exception:
            pass

    def handle_salvar_pix(e):
        if not txt_chave_pix.value.strip():
            show_snack("Digite uma chave Pix válida!")
            return
        try:
            execute_query("UPDATE usuarios SET chave_pix = %s WHERE id = %s;", (txt_chave_pix.value.strip(), usuario_id), commit=True)
            show_snack("Chave Pix salva com sucesso!", is_error=False)
        except Exception as ex:
            show_snack(f"Erro ao salvar Pix: {ex}")

    # --- CARREGAR VAGAS COM STATUS DINÂMICO E CANCELAMENTO ---
    def carregar_vagas_disponiveis():
        list_vagas_disponiveis.controls.clear()
        try:
            query = """
                SELECT v.id as vaga_id, v.funcao, v.valor_diaria, v.quantidade,
                       e.id as evento_id, e.nome as evento_nome, e.local, e.data_inicio, e.data_fim,
                       c.id as candidatura_id, c.status as candidatura_status
                FROM vagas v
                JOIN eventos e ON v.evento_id = e.id
                LEFT JOIN candidaturas c ON c.vaga_id = v.id AND c.usuario_id = %s
                WHERE e.empresa_id = %s AND v.status = 'ABERTA'
                ORDER BY v.id DESC;
            """
            vagas = execute_query(query, (usuario_id, empresa_id), fetch_all=True) or []

            if not vagas:
                list_vagas_disponiveis.controls.append(ft.Text("Nenhuma vaga aberta no momento.", color="#94A3B8"))
            else:
                for vg in vagas:
                    v_id = vg['vaga_id']
                    cand_id = vg.get('candidatura_id')
                    cand_st = str(vg.get('candidatura_status') or '').upper()
                    dt_in = vg['data_inicio']
                    dt_fim = vg['data_fim']

                    def candidatar(vaga_id_target, dt_inicio_alvo, dt_fim_alvo):
                        try:
                            # Valida choque de datas com outros eventos inscritos/aprovados
                            query_conflito = """
                                SELECT e.nome as evento_conflito
                                FROM candidaturas c
                                JOIN vagas v ON c.vaga_id = v.id
                                JOIN eventos e ON v.evento_id = e.id
                                WHERE c.usuario_id = %s 
                                  AND c.status IN ('APROVADO', 'PENDENTE')
                                  AND (e.data_inicio <= %s AND e.data_fim >= %s);
                            """
                            conflitos = execute_query(query_conflito, (usuario_id, dt_fim_alvo, dt_inicio_alvo), fetch_all=True)

                            if conflitos:
                                nome_ev = conflitos[0].get('evento_conflito', 'outro evento')
                                show_snack(f"⚠️ Você já tem job cadastrado/agendado neste mesmo dia ({nome_ev})!", is_error=True)
                                return

                            execute_query("INSERT INTO candidaturas (vaga_id, usuario_id, status) VALUES (%s, %s, 'PENDENTE');", (vaga_id_target, usuario_id), commit=True)
                            show_snack("Inscrição realizada!", is_error=False)
                            carregar_vagas_disponiveis()
                            carregar_meus_eventos()

                        except Exception as ex:
                            show_snack(f"Erro ao candidatar: {ex}")

                    def cancelar_inscricao(c_id):
                        try:
                            execute_query("DELETE FROM candidaturas WHERE id = %s;", (c_id,), commit=True)
                            show_snack("Inscrição cancelada com sucesso!", is_error=False)
                            carregar_vagas_disponiveis()
                            carregar_meus_eventos()
                        except Exception as ex:
                            show_snack(f"Erro ao cancelar inscrição: {ex}")

                    # Lógica do Botão de Inscrição / Cancelamento / Confirmação
                    if cand_st == 'APROVADO':
                        btn_acao = ft.ElevatedButton(
                            "Inscrição Confirmada ✅ (Não pode ser cancelada)",
                            style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"),
                            disabled=True, height=36
                        )
                    elif cand_st == 'PENDENTE':
                        btn_acao = ft.ElevatedButton(
                            "Cancelar Inscrição 🚫",
                            style=ft.ButtonStyle(bgcolor="#334155", color="#E76F51"),
                            height=36,
                            on_click=lambda _, cid=cand_id: cancelar_inscricao(cid)
                        )
                    else:
                        btn_acao = ft.ElevatedButton(
                            "Quero me Candidatar ✋",
                            style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"),
                            height=36,
                            on_click=lambda _, vid=v_id, d_in=dt_in, d_fim=dt_fim: candidatar(vid, d_in, d_fim)
                        )

                    list_vagas_disponiveis.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=12, border_radius=8,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"🎪 {vg['evento_nome']}", weight="bold", color="white", size=14),
                                    ft.Text(f"R$ {float(vg['valor_diaria']):.2f} / dia", color="#2A9D8F", weight="bold", size=13)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Função: {vg['funcao']} | Vagas: {vg['quantidade']}", size=12, color="#4CC9F0"),
                                ft.Text(f"📍 {vg.get('local', 'N/A')}", size=11, color="#94A3B8"),
                                ft.Text(f"📅 Data: {vg.get('data_inicio')} até {vg.get('data_fim')}", size=11, color="#94A3B8"),
                                btn_acao
                            ], spacing=6)
                        )
                    )
        except Exception as ex:
            list_vagas_disponiveis.controls.append(ft.Text(f"Erro ao carregar vagas: {ex}", color="#E76F51"))
        page.update()

    def carregar_meus_eventos():
        list_meus_eventos.controls.clear()
        try:
            query = """
                SELECT c.id as cand_id, c.status as cand_status, v.funcao, v.valor_diaria,
                       e.nome as evento_nome, e.local, e.data_inicio, e.data_fim,
                       COALESCE(p.dias_presentes, 0) as dias_presentes,
                       COALESCE(p.status_pagamento, 'PENDENTE') as status_pag
                FROM candidaturas c
                JOIN vagas v ON c.vaga_id = v.id
                JOIN eventos e ON v.evento_id = e.id
                LEFT JOIN presencas_pagamentos p ON c.id = p.candidatura_id
                WHERE c.usuario_id = %s ORDER BY c.id DESC;
            """
            meus = execute_query(query, (usuario_id,), fetch_all=True) or []

            if not meus:
                list_meus_eventos.controls.append(ft.Text("Você ainda não possui candidaturas ou eventos.", color="#94A3B8"))
            else:
                for m in meus:
                    cand_id = m['cand_id']
                    st = str(m['cand_status']).upper()
                    st_col = "#2A9D8F" if st == 'APROVADO' else ("#4CC9F0" if st == 'PENDENTE' else "#E76F51")
                    local_str = str(m.get('local') or '')

                    maps_url = f"https://www.google.com/maps/search/?api=1&query={local_str.replace(' ', '+')}"

                    def realizar_checkin(c_id, pres_atual):
                        try:
                            nv_pres = pres_atual + 1
                            execute_query("""
                                INSERT INTO presencas_pagamentos (candidatura_id, dias_presentes)
                                VALUES (%s, %s)
                                ON CONFLICT (candidatura_id)
                                DO UPDATE SET dias_presentes = EXCLUDED.dias_presentes;
                            """, (c_id, nv_pres), commit=True)
                            show_snack("Check-in realizado com sucesso! Presença confirmada.", is_error=False)
                            carregar_meus_eventos()
                            carregar_extrato()
                        except Exception as ex:
                            show_snack(f"Erro no Check-in: {ex}")

                    card_content = [
                        ft.Row([
                            ft.Text(f"🎪 {m['evento_nome']}", weight="bold", color="white", size=14),
                            ft.Text(f"Status: {st}", color=st_col, weight="bold", size=12)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"Função: {m['funcao']} | Diária: R$ {float(m['valor_diaria']):.2f}", size=12, color="#4CC9F0"),
                        ft.Text(f"📅 Período: {m.get('data_inicio')} até {m.get('data_fim')}", size=11, color="#94A3B8"),
                    ]

                    if st == 'APROVADO':
                        card_content.extend([
                            ft.Divider(color="#334155"),
                            ft.Text("📍 Guia do Evento / Briefing:", weight="bold", size=12, color="white"),
                            ft.Text(f"Endereço: {local_str}", size=11, color="#94A3B8"),
                            ft.Text("👔 Dress Code: Camiseta/Camisa preta lisa, calça escura e tênis confortável.", size=11, color="#2A9D8F"),
                            ft.ResponsiveRow([
                                ft.ElevatedButton("Abrir no Google Maps 🗺️", style=ft.ButtonStyle(bgcolor="#1E293B", color="#4CC9F0"), height=34, on_click=lambda _, url=maps_url: page.launch_url(url), col={"xs": 12, "sm": 6}),
                                ft.ElevatedButton("Fazer Check-in 📍", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), height=34, on_click=lambda _, cid=cand_id, pr=m['dias_presentes']: realizar_checkin(cid, pr), col={"xs": 12, "sm": 6})
                            ], spacing=8)
                        ])

                    list_meus_eventos.controls.append(
                        ft.Container(bgcolor="#1E293B", padding=12, border_radius=8, content=ft.Column(card_content, spacing=6))
                    )
        except Exception as ex:
            list_meus_eventos.controls.append(ft.Text(f"Erro ao carregar minha agenda: {ex}", color="#E76F51"))
        page.update()

    # --- CARREGAR EXTRATO DE CACHÊS SEPARADO (PENDENTES VS EFETIVADOS) ---
    def carregar_extrato():
        list_caches_pendentes.controls.clear()
        list_caches_pagos.controls.clear()
        try:
            query = """
                SELECT e.nome as evento_nome, v.funcao, v.valor_diaria,
                       COALESCE(p.dias_presentes, 0) as dias_presentes,
                       COALESCE(p.status_pagamento, 'PENDENTE') as status_pag,
                       COALESCE(p.valor_pago, 0.00) as valor_pago
                FROM candidaturas c
                JOIN vagas v ON c.vaga_id = v.id
                JOIN eventos e ON v.evento_id = e.id
                LEFT JOIN presencas_pagamentos p ON c.id = p.candidatura_id
                WHERE c.usuario_id = %s AND c.status = 'APROVADO';
            """
            caches = execute_query(query, (usuario_id,), fetch_all=True) or []

            tot_a_receber = 0.0
            tot_recebido = 0.0

            if not caches:
                list_caches_pendentes.controls.append(ft.Text("Nenhum cachê pendente.", color="#94A3B8"))
                list_caches_pagos.controls.append(ft.Text("Nenhum pagamento efetuado ainda.", color="#94A3B8"))
            else:
                for c in caches:
                    v_diaria = float(c['valor_diaria'])
                    dias = int(c['dias_presentes'])
                    st_p = str(c['status_pag']).upper()
                    v_calculado = v_diaria * dias

                    card_item = ft.Container(
                        bgcolor="#1E293B", padding=10, border_radius=6,
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{c['evento_nome']} ({c['funcao']})", weight="bold", color="white", size=13),
                                ft.Text(f"Presenças: {dias} dia(s) | Status: {st_p}", size=11, color="#94A3B8")
                            ], expand=True),
                            ft.Text(f"R$ {v_calculado if st_p != 'PAGO' else float(c['valor_pago']):.2f}", weight="bold", color="#2A9D8F" if st_p == 'PAGO' else "#E76F51", size=13)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )

                    if st_p == 'PAGO':
                        tot_recebido += float(c['valor_pago'])
                        list_caches_pagos.controls.append(card_item)
                    else:
                        tot_a_receber += v_calculado
                        list_caches_pendentes.controls.append(card_item)

            txt_total_a_receber.value = f"R$ {tot_a_receber:.2f}"
            txt_total_recebido.value = f"R$ {tot_recebido:.2f}"
        except Exception as ex:
            list_caches_pendentes.controls.append(ft.Text(f"Erro ao carregar extrato: {ex}", color="#E76F51"))
        page.update()

    area_conteudo = ft.Container(expand=True)

    def set_aba(aba_nome):
        if aba_nome == "AGENDA":
            carregar_meus_eventos()
            area_conteudo.content = ft.Column([
                ft.Text("Minha Agenda & Eventos Confirmados", weight="bold", size=15, color="#4CC9F0"),
                list_meus_eventos
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "VAGAS":
            carregar_vagas_disponiveis()
            area_conteudo.content = ft.Column([
                ft.Text("Vagas Abertas na Empresa", weight="bold", size=15, color="#4CC9F0"),
                list_vagas_disponiveis
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "CACHES":
            carregar_extrato()
            area_conteudo.content = ft.Column([
                ft.Text("Extrato de Cachês", weight="bold", size=15, color="#4CC9F0"),
                ft.ResponsiveRow([
                    ft.Container(content=ft.Column([ft.Text("A Receber (Pendente)", size=10, color="#94A3B8"), txt_total_a_receber]), bgcolor="#1E293B", padding=10, border_radius=6, col={"xs": 6, "sm": 6}),
                    ft.Container(content=ft.Column([ft.Text("Total Pago (Efetivado)", size=10, color="#94A3B8"), txt_total_recebido]), bgcolor="#1E293B", padding=10, border_radius=6, col={"xs": 6, "sm": 6}),
                ], spacing=8),
                ft.Divider(color="#334155"),
                ft.Text("Cadastrar / Atualizar Chave Pix", weight="bold", size=13, color="white"),
                ft.ResponsiveRow([
                    txt_chave_pix,
                    ft.ElevatedButton("Salvar Pix", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), height=42, on_click=handle_salvar_pix)
                ], spacing=8),
                ft.Divider(color="#334155"),
                ft.Text("⏳ Cachês Pendentes a Receber:", weight="bold", size=13, color="#E76F51"),
                list_caches_pendentes,
                ft.Divider(color="#334155"),
                ft.Text("✅ Cachês Efetivados / Pagos:", weight="bold", size=13, color="#2A9D8F"),
                list_caches_pagos
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        page.update()

    btn_aba_ag = ft.ElevatedButton("Minha Agenda 📅", on_click=lambda _: set_aba("AGENDA"), height=36)
    btn_aba_vg = ft.ElevatedButton("Vagas Abertas 🔍", on_click=lambda _: set_aba("VAGAS"), height=36)
    btn_aba_cx = ft.ElevatedButton("Meus Cachês 💵", on_click=lambda _: set_aba("CACHES"), height=36)

    carregar_perfil()
    set_aba("AGENDA")

    card_perfil_header = ft.Container(
        bgcolor="#1E293B", padding=12, border_radius=10,
        content=ft.Row([
            ft.Column([
                ft.Text(f"Bem-vindo(a), {nome_staff}", size=16, weight="bold", color="white"),
                ft.Text("Sua avaliação com as produtoras:", size=11, color="#94A3B8")
            ], expand=True),
            lbl_nota_staff
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    )

    return ft.Container(
        expand=True, bgcolor="#0B132B", padding=12,
        content=ft.Column([
            ft.Row([
                ft.Text("Painel do Colaborador (Staff)", size=18, weight="bold", color="white"),
                ft.IconButton(ft.Icons.LOGOUT, icon_color="#E76F51", tooltip="Sair", on_click=lambda e: on_logout() if on_logout else None)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            card_perfil_header,
            ft.Row([btn_aba_ag, btn_aba_vg, btn_aba_cx], spacing=8, scroll=ft.ScrollMode.AUTO),
            ft.Divider(color="#334155", height=1),
            area_conteudo
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
    )