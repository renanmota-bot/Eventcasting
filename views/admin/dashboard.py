import flet as ft

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query

def AdminDashboardView(page: ft.Page, user=None, on_logout=None, on_navigate=None):
    nome_admin = user.get('nome', 'Administrador') if user else 'Administrador'
    empresa_id = user.get('empresa_id') if user else None

    # Link oficial de convite do Staff
    staff_link = f"https://eventcasting.onrender.com/?register&empresa={empresa_id}" if empresa_id else "https://eventcasting.onrender.com/?register"

    # --- CONTROLES DE INTERFACE ---
    txt_total_staff = ft.Text("0", size=20, weight="bold", color="#4CC9F0")
    txt_eventos_ativos = ft.Text("0", size=20, weight="bold", color="#2A9D8F")

    # Inputs para Criar Evento
    txt_nome_evento = ft.TextField(label="Nome do Evento", text_size=13, border_radius=8)
    txt_local_evento = ft.TextField(label="Localização / Endereço Completo", text_size=13, border_radius=8)
    txt_data_inicio = ft.TextField(label="Data Início (AAAA-MM-DD)", hint_text="2026-08-20", text_size=13, border_radius=8)
    txt_data_fim = ft.TextField(label="Data Fim (AAAA-MM-DD)", hint_text="2026-08-22", text_size=13, border_radius=8)

    # Inputs para Criar Vaga
    dd_eventos = ft.Dropdown(label="Selecione o Evento", text_size=13, border_radius=8)
    txt_funcao = ft.TextField(label="Função (Ex: Recepcionista, Seguranca)", text_size=13, border_radius=8)
    txt_valor_diaria = ft.TextField(label="Valor Diária (R$)", text_size=13, border_radius=8)
    txt_qtd_vagas = ft.TextField(label="Quantidade de Vagas", text_size=13, border_radius=8)

    # Listas
    list_eventos = ft.Column(spacing=10)
    list_candidatos = ft.Column(spacing=10)

    # --- LÓGICA DE NAVEGAÇÃO E DADOS ---
    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor="#E76F51" if is_error else "#2A9D8F")
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def handle_copy_staff_link(e):
        try:
            page.clipboard = staff_link
        except Exception:
            try:
                page.set_clipboard_async(staff_link)
            except Exception as ex:
                print(f"Erro ao copiar clipboard: {ex}")
        show_snack("Link do Staff copiado para a área de transferência!", is_error=False)

    def carregar_dados():
        if not empresa_id:
            return

        # 1. Carrega Métricas
        try:
            res_staff = execute_query("SELECT COUNT(*) as qtd FROM usuarios WHERE empresa_id = %s AND perfil = 'STAFF';", (empresa_id,), fetch_all=True)
            if res_staff: txt_total_staff.value = str(res_staff[0].get('qtd', 0))

            res_ev = execute_query("SELECT COUNT(*) as qtd FROM eventos WHERE empresa_id = %s;", (empresa_id,), fetch_all=True)
            if res_ev: txt_eventos_ativos.value = str(res_ev[0].get('qtd', 0))
        except Exception:
            pass

        # 2. Carrega Dropdown e Lista de Eventos
        try:
            eventos = execute_query("SELECT id, nome, local, data_inicio, data_fim FROM eventos WHERE empresa_id = %s ORDER BY id DESC;", (empresa_id,), fetch_all=True)
            dd_eventos.options.clear()
            list_eventos.controls.clear()

            if eventos:
                for ev in eventos:
                    dd_eventos.options.append(ft.dropdown.Option(str(ev['id']), ev['nome']))
                    list_eventos.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=12, border_radius=8,
                            content=ft.Column([
                                ft.Text(f"🎪 {ev['nome']}", weight="bold", size=14, color="white"),
                                ft.Text(f"📍 {ev.get('local', 'N/A')}", size=12, color="#94A3B8"),
                                ft.Text(f"📅 {ev.get('data_inicio')} até {ev.get('data_fim')}", size=11, color="#2A9D8F")
                            ], spacing=4)
                        )
                    )
            else:
                list_eventos.controls.append(ft.Text("Nenhum evento cadastrado ainda.", size=12, color="#94A3B8"))
        except Exception:
            pass

        page.update()

    def handle_criar_evento(e):
        if not all([txt_nome_evento.value, txt_local_evento.value, txt_data_inicio.value, txt_data_fim.value]):
            show_snack("Preencha todos os campos do evento!")
            return

        try:
            query = "INSERT INTO eventos (empresa_id, nome, local, data_inicio, data_fim) VALUES (%s, %s, %s, %s, %s);"
            execute_query(query, (empresa_id, txt_nome_evento.value.strip(), txt_local_evento.value.strip(), txt_data_inicio.value.strip(), txt_data_fim.value.strip()))
            
            show_snack("Evento criado com sucesso!", is_error=False)
            txt_nome_evento.value = ""
            txt_local_evento.value = ""
            txt_data_inicio.value = ""
            txt_data_fim.value = ""
            carregar_dados()
        except Exception as ex:
            show_snack(f"Erro ao criar evento: {ex}")

    def handle_criar_vaga(e):
        if not all([dd_eventos.value, txt_funcao.value, txt_valor_diaria.value, txt_qtd_vagas.value]):
            show_snack("Preencha todos os campos da vaga!")
            return

        try:
            query = "INSERT INTO vagas (evento_id, funcao, valor_diaria, quantidade, status) VALUES (%s, %s, %s, %s, 'ABERTA');"
            execute_query(query, (int(dd_eventos.value), txt_funcao.value.strip(), float(txt_valor_diaria.value.replace(',', '.')), int(txt_qtd_vagas.value)))
            
            show_snack("Vaga publicada com sucesso!", is_error=False)
            txt_funcao.value = ""
            txt_valor_diaria.value = ""
            txt_qtd_vagas.value = ""
            carregar_dados()
        except Exception as ex:
            show_snack(f"Erro ao criar vaga: {ex}")

    # --- COMPONENTES VISUAIS ---
    btn_copiar_link = ft.ElevatedButton(
        "Copiar Link do Staff",
        style=ft.ButtonStyle(bgcolor="#4CC9F0", color="white", shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=handle_copy_staff_link, height=42
    )

    card_link_staff = ft.Container(
        content=ft.Column([
            ft.Text("Link de Convite para Equipe (Staff)", weight="bold", size=14, color="white"),
            ft.Text("Compartilhe com colaboradores para cadastrarem-se na sua empresa:", size=11, color="#94A3B8"),
            ft.TextField(value=staff_link, read_only=True, text_size=12, border_radius=8),
            btn_copiar_link
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        bgcolor="#1E293B", padding=12, border_radius=10
    )

    cards_metricas = ft.ResponsiveRow([
        ft.Container(
            content=ft.Column([ft.Text("Membros Staff", color="#94A3B8", size=11), txt_total_staff]),
            bgcolor="#1E293B", padding=12, border_radius=8, col={"xs": 6, "sm": 6}
        ),
        ft.Container(
            content=ft.Column([ft.Text("Eventos Ativos", color="#94A3B8", size=11), txt_eventos_ativos]),
            bgcolor="#1E293B", padding=12, border_radius=8, col={"xs": 6, "sm": 6}
        )
    ], spacing=10)

    # Abas com Organização do Painel da Empresa
    tabs_painel = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Eventos & Vagas",
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text("1. Cadastrar Novo Evento", weight="bold", size=15, color="#4CC9F0"),
                        txt_nome_evento,
                        txt_local_evento,
                        ft.Row([txt_data_inicio, txt_data_fim], spacing=10),
                        ft.ElevatedButton("Criar Evento", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_criar_evento, width=380),
                        ft.Divider(color="#334155"),
                        ft.Text("2. Publicar Vaga no Evento", weight="bold", size=15, color="#4CC9F0"),
                        dd_eventos,
                        txt_funcao,
                        ft.Row([txt_valor_diaria, txt_qtd_vagas], spacing=10),
                        ft.ElevatedButton("Publicar Vaga", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="white"), on_click=handle_criar_vaga, width=380),
                    ], spacing=10, scroll=ft.ScrollMode.AUTO)
                )
            ),
            ft.Tab(
                text="Meus Eventos",
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text("Eventos Cadastrados", weight="bold", size=15, color="white"),
                        list_eventos
                    ], spacing=10, scroll=ft.ScrollMode.AUTO)
                )
            )
        ],
        expand=True
    )

    carregar_dados()

    return ft.Container(
        expand=True, bgcolor="#0B132B", padding=12,
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(f"Painel — {nome_admin}", size=18, weight="bold", color="white"),
                    ft.Text("Gestão da empresa e convites", size=11, color="#94A3B8")
                ], expand=True),
                ft.IconButton(ft.Icons.LOGOUT, icon_color="#E76F51", tooltip="Sair", on_click=lambda e: on_logout() if on_logout else None)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            cards_metricas,
            card_link_staff,
            ft.Divider(color="#334155", height=1),
            tabs_painel
        ], spacing=12, scroll=ft.ScrollMode.AUTO)
    )