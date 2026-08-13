import flet as ft

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query


def SuperAdminDashboardView(page: ft.Page, user=None, on_logout=None, on_ghost_login=None):
    nome_super = user.get('nome', 'Super Admin') if user else 'Super Admin'

    # --- INICIALIZAÇÃO DE TABELAS ---
    def init_super_db():
        q_schema = """
            ALTER TABLE empresas ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'ATIVO';
            ALTER TABLE empresas ADD COLUMN IF NOT EXISTS plano VARCHAR(50) DEFAULT 'MENSAL';
            ALTER TABLE empresas ADD COLUMN IF NOT EXISTS valor_plano NUMERIC(10,2) DEFAULT 100.00;
            
            CREATE TABLE IF NOT EXISTS chamados_suporte (
                id SERIAL PRIMARY KEY,
                empresa_id INT,
                assunto VARCHAR(200) NOT NULL,
                categoria VARCHAR(100) DEFAULT 'Geral',
                prioridade VARCHAR(20) DEFAULT 'MÉDIA',
                status VARCHAR(30) DEFAULT 'ABERTO',
                data_criacao TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS chamados_interacoes (
                id SERIAL PRIMARY KEY,
                chamado_id INT NOT NULL,
                remetente_tipo VARCHAR(20) NOT NULL,
                mensagem TEXT NOT NULL,
                data_envio TIMESTAMP DEFAULT NOW()
            );
        """
        try:
            execute_query(q_schema, commit=True)
        except Exception as ex:
            print(f"Notice schema: {ex}")

    init_super_db()

    # --- CONTROLES DE INTERFACE ---
    txt_total_empresas = ft.Text("0", size=20, weight="bold", color="#4CC9F0")
    txt_total_usuarios = ft.Text("0", size=20, weight="bold", color="#2A9D8F")
    txt_faturamento_saas = ft.Text("R$ 0,00", size=20, weight="bold", color="#E76F51")

    list_empresas = ft.Column(spacing=10)
    list_usuarios = ft.Column(spacing=10)
    list_chamados = ft.Column(spacing=10)

    txt_busca_empresa = ft.TextField(label="Buscar Produtora por Nome ou CNPJ", text_size=12, border_radius=8, expand=True)

    txt_novo_nome_emp = ft.TextField(label="Nome da Produtora *", text_size=12, border_radius=8)
    txt_novo_cnpj_emp = ft.TextField(label="CNPJ / CPF *", text_size=12, border_radius=8)
    txt_novo_email_admin = ft.TextField(label="E-mail do Admin *", text_size=12, border_radius=8)
    txt_nova_senha_admin = ft.TextField(label="Senha Inicial *", password=True, can_reveal_password=True, text_size=12, border_radius=8)

    txt_busca_usuario = ft.TextField(label="Buscar Usuário por Nome ou E-mail", text_size=12, border_radius=8, expand=True)
    dd_filtro_perfil_usr = ft.Dropdown(
        label="Perfil", value="TODOS", text_size=12, border_radius=8, width=150,
        options=[
            ft.dropdown.Option("TODOS", "Todos"),
            ft.dropdown.Option("ADMIN", "Admin"),
            ft.dropdown.Option("STAFF", "Staff"),
            ft.dropdown.Option("SUPER_ADMIN", "Super Admin")
        ]
    )

    txt_usr_nome = ft.TextField(label="Nome Completo *", text_size=12, border_radius=8)
    txt_usr_email = ft.TextField(label="E-mail *", text_size=12, border_radius=8)
    txt_usr_senha = ft.TextField(label="Senha *", password=True, can_reveal_password=True, text_size=12, border_radius=8)
    dd_usr_perfil = ft.Dropdown(
        label="Perfil *", value="STAFF", text_size=12, border_radius=8,
        options=[
            ft.dropdown.Option("STAFF", "Staff"),
            ft.dropdown.Option("ADMIN", "Admin"),
            ft.dropdown.Option("SUPER_ADMIN", "Super Admin")
        ]
    )
    txt_usr_empresa_id = ft.TextField(label="ID Empresa (Opcional)", value="1", text_size=12, border_radius=8)

    dd_filtro_status_chamado = ft.Dropdown(
        label="Filtrar por Status", text_size=12, border_radius=8, width=160, value="TODOS",
        options=[
            ft.dropdown.Option("TODOS", "TODOS"),
            ft.dropdown.Option("ABERTO", "ABERTO"),
            ft.dropdown.Option("EM ANDAMENTO", "EM ANDAMENTO"),
            ft.dropdown.Option("RESOLVIDO", "RESOLVIDO")
        ]
    )

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg, color="white", weight="bold"), bgcolor="#E76F51" if is_error else "#2A9D8F")
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def carregar_empresas():
        list_empresas.controls.clear()
        try:
            busca = txt_busca_empresa.value.strip() if txt_busca_empresa.value else ""
            if busca:
                query = "SELECT id, COALESCE(nome, 'Sem Nome') as nome, COALESCE(cnpj, 'N/A') as cnpj, COALESCE(status, 'ATIVO') as status, COALESCE(plano, 'MENSAL') as plano, COALESCE(valor_plano, 100.00) as valor_plano FROM empresas WHERE LOWER(nome) LIKE LOWER(%s) OR cnpj LIKE %s ORDER BY id DESC;"
                empresas = execute_query(query, (f"%{busca}%", f"%{busca}%"), fetch_all=True) or []
            else:
                query = "SELECT id, COALESCE(nome, 'Sem Nome') as nome, COALESCE(cnpj, 'N/A') as cnpj, COALESCE(status, 'ATIVO') as status, COALESCE(plano, 'MENSAL') as plano, COALESCE(valor_plano, 100.00) as valor_plano FROM empresas ORDER BY id DESC;"
                empresas = execute_query(query, fetch_all=True) or []

            txt_total_empresas.value = str(len(empresas))
            res_usr = execute_query("SELECT COUNT(*) as qtd FROM usuarios;", fetch_all=True)
            if res_usr: txt_total_usuarios.value = str(res_usr[0].get('qtd', 0))

            mrr_total = sum([float(e.get('valor_plano') or 100.00) for e in empresas if str(e.get('status') or 'ATIVO').upper() == 'ATIVO'])
            txt_faturamento_saas.value = f"R$ {mrr_total:.2f}"

            if not empresas:
                list_empresas.controls.append(ft.Text("Nenhuma empresa cadastrada.", color="#94A3B8"))
            else:
                for emp in empresas:
                    emp_id = emp['id']
                    emp_nome = emp['nome']
                    emp_cnpj = emp['cnpj']
                    st = str(emp.get('status') or 'ATIVO').upper()
                    plano_atual = str(emp.get('plano') or 'MENSAL').upper()
                    valor_atual = float(emp.get('valor_plano') or 100.00)

                    dd_status = ft.Dropdown(
                        value=st, width=130, text_size=12,
                        options=[
                            ft.dropdown.Option("ATIVO", "ATIVO"),
                            ft.dropdown.Option("INADIMPLENTE", "INADIMPLENTE"),
                            ft.dropdown.Option("DEGUSTAÇÃO", "DEGUSTAÇÃO"),
                            ft.dropdown.Option("BLOQUEADO", "BLOQUEADO")
                        ]
                    )

                    dd_plano = ft.Dropdown(
                        value=plano_atual, width=130, text_size=12,
                        options=[
                            ft.dropdown.Option("MENSAL", "MENSAL"),
                            ft.dropdown.Option("ANUAL", "ANUAL"),
                            ft.dropdown.Option("GRATUITO", "GRATUITO")
                        ]
                    )

                    txt_val_plano = ft.TextField(value=f"{valor_atual:.2f}", width=100, text_size=12, label="Valor R$")

                    def salvar_assinatura(e_id, in_st, in_pl, in_vl):
                        try:
                            nv_v = float(in_vl.value.replace(',', '.'))
                            execute_query("UPDATE empresas SET status = %s, plano = %s, valor_plano = %s WHERE id = %s;", (in_st.value, in_pl.value, nv_v, e_id), commit=True)
                            show_snack("Assinatura atualizada!", is_error=False)
                            carregar_empresas()
                        except Exception as ex:
                            show_snack(f"Erro ao salvar: {ex}")

                    def fazer_ghost_login(e_id):
                        u_admin = execute_query("SELECT id, nome, email, perfil, empresa_id FROM usuarios WHERE empresa_id = %s AND perfil = 'ADMIN' LIMIT 1;", (e_id,), fetch_all=True)
                        if u_admin and on_ghost_login:
                            on_ghost_login(u_admin[0])
                        else:
                            show_snack("Empresa não possui Admin cadastrado.")

                    list_empresas.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=14, border_radius=10,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"🏢 {emp_nome} (ID: #{emp_id})", weight="bold", color="white", size=15),
                                    ft.Text(f"Status: {st}", color="#2A9D8F" if st in ["ATIVO", "DEGUSTAÇÃO"] else "#E76F51", weight="bold", size=12)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"CNPJ/CPF: {emp_cnpj}", size=12, color="#94A3B8"),
                                ft.Divider(color="#334155"),
                                ft.Text("Gerenciar Assinatura SaaS:", size=12, weight="bold", color="#4CC9F0"),
                                ft.Row([
                                    dd_status, dd_plano, txt_val_plano,
                                    ft.ElevatedButton("Salvar Alterações", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), height=38, on_click=lambda _, eid=emp_id, st_i=dd_status, pl_i=dd_plano, vl_i=txt_val_plano: salvar_assinatura(eid, st_i, pl_i, vl_i))
                                ], spacing=8, scroll=ft.ScrollMode.AUTO),
                                ft.Row([
                                    ft.ElevatedButton("Entrar no Painel (Ghost Login) 👁️", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"), height=36, on_click=lambda _, eid=emp_id: fazer_ghost_login(eid))
                                ])
                            ], spacing=8)
                        )
                    )
        except Exception as ex:
            list_empresas.controls.append(ft.Text(f"Erro ao carregar empresas: {ex}", color="#E76F51"))
        page.update()

    def handle_criar_empresa_manual(e):
        if not all([txt_novo_nome_emp.value, txt_novo_cnpj_emp.value, txt_novo_email_admin.value, txt_nova_senha_admin.value]):
            show_snack("Preencha todos os campos!")
            return
        try:
            q_emp = "INSERT INTO empresas (nome, cnpj, status, plano, valor_plano) VALUES (%s, %s, 'ATIVO', 'MENSAL', 100.00) RETURNING id;"
            res_emp = execute_query(q_emp, (txt_novo_nome_emp.value.strip(), txt_novo_cnpj_emp.value.strip()), fetch_all=True, commit=True)
            if res_emp:
                new_id = res_emp[0]['id']
                execute_query("INSERT INTO usuarios (empresa_id, nome, email, senha, perfil, status) VALUES (%s, %s, %s, %s, 'ADMIN', 'ATIVO');", (new_id, f"Admin {txt_novo_nome_emp.value.strip()}", txt_novo_email_admin.value.strip(), txt_nova_senha_admin.value.strip()), commit=True)
                show_snack("Produtora e Admin criados com sucesso!", is_error=False)
                txt_novo_nome_emp.value = ""
                txt_novo_cnpj_emp.value = ""
                txt_novo_email_admin.value = ""
                txt_nova_senha_admin.value = ""
                carregar_empresas()
        except Exception as ex:
            show_snack(f"Erro ao criar empresa: {ex}")

    def carregar_usuarios():
        list_usuarios.controls.clear()
        try:
            busca = txt_busca_usuario.value.strip() if txt_busca_usuario.value else ""
            p_filtro = dd_filtro_perfil_usr.value

            params = []
            where_clauses = []

            if busca:
                where_clauses.append("(LOWER(nome) LIKE LOWER(%s) OR LOWER(email) LIKE LOWER(%s))")
                params.extend([f"%{busca}%", f"%{busca}%"])

            if p_filtro and p_filtro != "TODOS":
                where_clauses.append("perfil = %s")
                params.append(p_filtro)

            where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            query = f"SELECT id, nome, email, perfil, empresa_id FROM usuarios{where_str} ORDER BY id DESC LIMIT 100;"

            usrs = execute_query(query, tuple(params) if params else None, fetch_all=True) or []

            if not usrs:
                list_usuarios.controls.append(ft.Text("Nenhum usuário encontrado.", color="#94A3B8"))
            else:
                for u in usrs:
                    u_id = u['id']
                    u_nome = u['nome']
                    u_email = u['email']
                    u_perf = str(u.get('perfil', 'STAFF')).upper()
                    emp_str = f"Empresa ID: {u['empresa_id']}" if u.get('empresa_id') else "Master SaaS"

                    txt_ed_nome = ft.TextField(value=u_nome, text_size=12, label="Nome")
                    txt_ed_email = ft.TextField(value=u_email, text_size=12, label="E-mail")
                    dd_ed_perfil = ft.Dropdown(
                        value=u_perf, text_size=12, width=130,
                        options=[
                            ft.dropdown.Option("STAFF", "STAFF"),
                            ft.dropdown.Option("ADMIN", "ADMIN"),
                            ft.dropdown.Option("SUPER_ADMIN", "SUPER_ADMIN")
                        ]
                    )

                    def salvar_edicao_usuario(uid, in_n, in_e, in_p):
                        try:
                            execute_query("UPDATE usuarios SET nome = %s, email = %s, perfil = %s WHERE id = %s;", (in_n.value.strip(), in_e.value.strip(), in_p.value, uid), commit=True)
                            show_snack("Usuário atualizado com sucesso!", is_error=False)
                            carregar_usuarios()
                        except Exception as ex:
                            show_snack(f"Erro ao salvar usuário: {ex}")

                    def deletar_usuario(uid):
                        try:
                            execute_query("DELETE FROM usuarios WHERE id = %s;", (uid,), commit=True)
                            show_snack("Usuário removido!", is_error=False)
                            carregar_usuarios()
                        except Exception as ex:
                            show_snack(f"Erro ao excluir usuário: {ex}")

                    list_usuarios.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=12, border_radius=8,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"👤 #{u_id} — {u_nome}", weight="bold", color="white", size=14),
                                    ft.Text(f"Perfil: {u_perf}", color="#4CC9F0", weight="bold", size=12)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"E-mail: {u_email} | {emp_str}", size=11, color="#94A3B8"),
                                ft.Row([txt_ed_nome, txt_ed_email, dd_ed_perfil], spacing=8, scroll=ft.ScrollMode.AUTO),
                                ft.Row([
                                    ft.ElevatedButton("Salvar Alterações", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), height=34, on_click=lambda _, uid=u_id, n_i=txt_ed_nome, e_i=txt_ed_email, p_i=dd_ed_perfil: salvar_edicao_usuario(uid, n_i, e_i, p_i)),
                                    ft.ElevatedButton("Acessar (Ghost) 👁️", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"), height=34, on_click=lambda _, usr=u: on_ghost_login(usr) if on_ghost_login else None),
                                    ft.ElevatedButton("Excluir 🗑️", style=ft.ButtonStyle(bgcolor="#E76F51", color="white"), height=34, on_click=lambda _, uid=u_id: deletar_usuario(uid))
                                ], spacing=8)
                            ], spacing=6)
                        )
                    )
        except Exception as ex:
            list_usuarios.controls.append(ft.Text(f"Erro ao carregar usuários: {ex}", color="#E76F51"))
        page.update()

    def handle_adicionar_usuario(e):
        if not all([txt_usr_nome.value, txt_usr_email.value, txt_usr_senha.value]):
            show_snack("Preencha Nome, E-mail e Senha!")
            return
        try:
            emp_id_val = int(txt_usr_empresa_id.value) if txt_usr_empresa_id.value and txt_usr_empresa_id.value.isdigit() else 1
            query = "INSERT INTO usuarios (empresa_id, nome, email, senha, perfil, status) VALUES (%s, %s, %s, %s, %s, 'ATIVO');"
            execute_query(query, (emp_id_val, txt_usr_nome.value.strip(), txt_usr_email.value.strip(), txt_usr_senha.value.strip(), dd_usr_perfil.value), commit=True)
            show_snack("Novo usuário cadastrado!", is_error=False)
            txt_usr_nome.value = ""
            txt_usr_email.value = ""
            txt_usr_senha.value = ""
            carregar_usuarios()
        except Exception as ex:
            show_snack(f"Erro ao cadastrar usuário: {ex}")

    txt_busca_usuario.on_change = lambda _: carregar_usuarios()
    dd_filtro_perfil_usr.on_change = lambda _: carregar_usuarios()

    # --- QUERY TOTALMENTE INDEPENDENTE PARA TRAZER ABSOLUTAMENTE TODOS OS CHAMADOS ---
    def carregar_chamados():
        list_chamados.controls.clear()
        try:
            st_filtro = dd_filtro_status_chamado.value
            
            if st_filtro and st_filtro != "TODOS":
                query = "SELECT id, empresa_id, assunto, categoria, prioridade, status, data_criacao FROM chamados_suporte WHERE status = %s ORDER BY id DESC;"
                chams = execute_query(query, (st_filtro,), fetch_all=True) or []
            else:
                query = "SELECT id, empresa_id, assunto, categoria, prioridade, status, data_criacao FROM chamados_suporte ORDER BY id DESC;"
                chams = execute_query(query, fetch_all=True) or []

            if not chams:
                list_chamados.controls.append(ft.Text("Nenhum chamado pendente ou registrado.", color="#94A3B8"))
            else:
                for ch in chams:
                    ch_id = ch['id']
                    assunto = ch['assunto']
                    e_id = ch.get('empresa_id')
                    
                    # Busca nome da empresa se existir
                    emp_nome = f"Empresa ID #{e_id}" if e_id else "Produtora Geral"
                    if e_id:
                        e_res = execute_query("SELECT nome FROM empresas WHERE id = %s;", (e_id,), fetch_all=True)
                        if e_res and e_res[0].get('nome'):
                            emp_nome = e_res[0]['nome']

                    st = str(ch['status']).upper()
                    prio = str(ch.get('prioridade', 'MÉDIA')).upper()

                    dd_st_chamado = ft.Dropdown(
                        value=st, width=150, text_size=12,
                        options=[
                            ft.dropdown.Option("ABERTO", "ABERTO"),
                            ft.dropdown.Option("EM ANDAMENTO", "EM ANDAMENTO"),
                            ft.dropdown.Option("RESOLVIDO", "RESOLVIDO"),
                            ft.dropdown.Option("FECHADO", "FECHADO")
                        ]
                    )

                    txt_resp_chamado = ft.TextField(label="Escrever Resposta...", multiline=True, min_lines=1, max_lines=3, text_size=12, border_radius=8, expand=True)
                    col_interacoes = ft.Column(spacing=6)

                    def carregar_interacoes(cid, container_col):
                        container_col.controls.clear()
                        inters = execute_query("SELECT remetente_tipo, mensagem, data_envio FROM chamados_interacoes WHERE chamado_id = %s ORDER BY id ASC;", (cid,), fetch_all=True) or []
                        for i in inters:
                            rem = "Sua Resposta (Super Admin)" if i['remetente_tipo'] == 'SUPER_ADMIN' else "Produtora"
                            bg_c = "#2A9D8F" if i['remetente_tipo'] == 'SUPER_ADMIN' else "#0F172A"
                            container_col.controls.append(
                                ft.Container(
                                    bgcolor=bg_c, padding=8, border_radius=6,
                                    content=ft.Column([
                                        ft.Text(rem, weight="bold", size=10, color="#94A3B8"),
                                        ft.Text(i['mensagem'], color="white", size=12)
                                    ], spacing=2)
                                )
                            )
                        page.update()

                    def responder_e_atualizar(cid, txt_in, dd_st, col_int):
                        if not txt_in.value.strip():
                            show_snack("Digite uma resposta para enviar!")
                            return
                        try:
                            execute_query("INSERT INTO chamados_interacoes (chamado_id, remetente_tipo, mensagem) VALUES (%s, 'SUPER_ADMIN', %s);", (cid, txt_in.value.strip()), commit=True)
                            execute_query("UPDATE chamados_suporte SET status = %s WHERE id = %s;", (dd_st.value, cid), commit=True)
                            show_snack("Resposta enviada!", is_error=False)
                            txt_in.value = ""
                            carregar_interacoes(cid, col_int)
                        except Exception as ex:
                            show_snack(f"Erro ao responder chamado: {ex}")

                    carregar_interacoes(ch_id, col_interacoes)

                    list_chamados.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=14, border_radius=10,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"🎫 Chamado #{ch_id} — {assunto}", weight="bold", color="white", size=15),
                                    ft.Text(f"Prioridade: {prio}", color="#E76F51" if prio in ["ALTA", "URGENTE"] else "#2A9D8F", weight="bold", size=12)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Produtora: {emp_nome} | Categoria: {ch.get('categoria', 'Geral')}", size=12, color="#94A3B8"),
                                ft.Divider(color="#334155"),
                                col_interacoes,
                                ft.Divider(color="#334155"),
                                ft.Row([
                                    dd_st_chamado,
                                    txt_resp_chamado,
                                    ft.ElevatedButton("Enviar Resposta 📩", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"), height=42, on_click=lambda _, cid=ch_id, tin=txt_resp_chamado, stin=dd_st_chamado, colin=col_interacoes: responder_e_atualizar(cid, tin, stin, colin))
                                ], spacing=8)
                            ], spacing=8)
                        )
                    )
        except Exception as ex:
            list_chamados.controls.append(ft.Text(f"Erro ao carregar chamados: {ex}", color="#E76F51"))
        page.update()

    dd_filtro_status_chamado.on_change = lambda _: carregar_chamados()

    area_conteudo = ft.Container(expand=True)

    def set_aba(aba_nome):
        if aba_nome == "EMPRESAS":
            carregar_empresas()
            area_conteudo.content = ft.Column([
                ft.Row([
                    ft.Text("Produtoras / Assinantes SaaS", weight="bold", size=15, color="#4CC9F0"),
                    txt_busca_empresa,
                    ft.ElevatedButton("Buscar", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=lambda _: carregar_empresas())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color="#334155"),
                list_empresas
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "CRIAR_EMPRESA":
            area_conteudo.content = ft.Column([
                ft.Text("Cadastrar Nova Produtora Manualmente", weight="bold", size=15, color="#4CC9F0"),
                txt_novo_nome_emp, txt_novo_cnpj_emp, txt_novo_email_admin, txt_nova_senha_admin,
                ft.ElevatedButton("Cadastrar Produtora & Admin", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_criar_empresa_manual, width=380)
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "USUARIOS":
            carregar_usuarios()
            area_conteudo.content = ft.Column([
                ft.Text("Gestão de Usuários Globais", weight="bold", size=15, color="#4CC9F0"),
                ft.Row([txt_busca_usuario, dd_filtro_perfil_usr], spacing=8),
                ft.Divider(color="#334155"),
                ft.Text("Cadastrar Novo Usuário:", weight="bold", size=13, color="white"),
                ft.Row([txt_usr_nome, txt_usr_email, txt_usr_senha], spacing=8),
                ft.Row([dd_usr_perfil, txt_usr_empresa_id], spacing=8),
                ft.ElevatedButton("Adicionar Usuário", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_adicionar_usuario, width=320),
                ft.Divider(color="#334155"),
                list_usuarios
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "CHAMADOS":
            carregar_chamados()
            area_conteudo.content = ft.Column([
                ft.Row([
                    ft.Text("Central de Chamados & Tickets de Suporte", weight="bold", size=15, color="#4CC9F0"),
                    dd_filtro_status_chamado
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color="#334155"),
                list_chamados
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        page.update()

    btn_aba_emp = ft.ElevatedButton("Empresas & Assinaturas", on_click=lambda _: set_aba("EMPRESAS"), height=36)
    btn_aba_add = ft.ElevatedButton("+ Nova Empresa", on_click=lambda _: set_aba("CRIAR_EMPRESA"), height=36)
    btn_aba_usr = ft.ElevatedButton("Usuários Globais", on_click=lambda _: set_aba("USUARIOS"), height=36)
    btn_aba_chamados = ft.ElevatedButton("Chamados 🎫", on_click=lambda _: set_aba("CHAMADOS"), height=36)

    carregar_empresas()
    set_aba("EMPRESAS")

    cards_metricas = ft.ResponsiveRow([
        ft.Container(content=ft.Column([ft.Text("Total de Produtoras", color="#94A3B8", size=11), txt_total_empresas]), bgcolor="#1E293B", padding=12, border_radius=8, col={"xs": 4, "sm": 4}),
        ft.Container(content=ft.Column([ft.Text("Total de Usuários", color="#94A3B8", size=11), txt_total_usuarios]), bgcolor="#1E293B", padding=12, border_radius=8, col={"xs": 4, "sm": 4}),
        ft.Container(content=ft.Column([ft.Text("MRR Ativo (SaaS)", color="#94A3B8", size=11), txt_faturamento_saas]), bgcolor="#1E293B", padding=12, border_radius=8, col={"xs": 4, "sm": 4}),
    ], spacing=10)

    return ft.Container(
        expand=True, bgcolor="#0B132B", padding=12,
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(f"Painel Máster SaaS — {nome_super}", size=18, weight="bold", color="white"),
                    ft.Text("Coração da Plataforma: Assinaturas, Chamados e Gestão Global", size=11, color="#94A3B8")
                ], expand=True),
                ft.IconButton(ft.Icons.LOGOUT, icon_color="#E76F51", tooltip="Sair", on_click=lambda e: on_logout() if on_logout else None)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            cards_metricas,
            ft.Row([btn_aba_emp, btn_aba_add, btn_aba_usr, btn_aba_chamados], spacing=8, scroll=ft.ScrollMode.AUTO),
            ft.Divider(color="#334155", height=1),
            area_conteudo
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
    )