import flet as ft
import bcrypt
import io
import csv
import base64
import asyncio

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query

# Função auxiliar de log de auditoria
def registrar_log(ator, acao):
    try:
        execute_query("INSERT INTO auditoria (ator, acao) VALUES (%s, %s);", (ator, acao), commit=True)
    except Exception:
        pass

def SuperAdminDashboardView(page: ft.Page, user=None, on_logout=None, on_ghost_login=None):
    nome_admin = user.get('nome', 'Super Admin') if user else 'Super Admin'
    
    # --- Componentes Visuais de Estatísticas ---
    txt_total_empresas = ft.Text("0", size=24, weight="bold", color="#4CC9F0")
    txt_total_usuarios = ft.Text("0", size=24, weight="bold", color="#4CC9F0")
    txt_receita_total = ft.Text("R$ 0,00", size=24, weight="bold", color="#2A9D8F")

    def atualizar_estatisticas():
        try:
            res_emp = execute_query("SELECT COUNT(*) as qtd FROM empresas;", fetch_all=True)
            res_usr = execute_query("SELECT COUNT(*) as qtd FROM usuarios;", fetch_all=True)
            res_fin = execute_query("SELECT SUM(valor) as total FROM pagamentos WHERE status = 'PAGO';", fetch_all=True)
            
            if res_emp: txt_total_empresas.value = str(res_emp[0].get('qtd', 0))
            if res_usr: txt_total_usuarios.value = str(res_usr[0].get('qtd', 0))
            if res_fin and res_fin[0].get('total'):
                txt_receita_total.value = f"R$ {float(res_fin[0]['total']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            pass

    # --- Broadcast (Aviso Global) ---
    txt_aviso_global = ft.TextField(label="Disparar Aviso Global para todos os clientes...", expand=True, text_size=14)
    
    def salvar_aviso(e):
        mensagem = txt_aviso_global.value.strip()
        try:
            execute_query("UPDATE avisos SET ativo = false;", commit=True)
            if mensagem:
                execute_query("INSERT INTO avisos (mensagem) VALUES (%s);", (mensagem,), commit=True)
                registrar_log(nome_admin, f"Disparou aviso global: {mensagem[:30]}...")
                page.snack_bar = ft.SnackBar(ft.Text("Aviso global emitido!"), bgcolor="#2A9D8F")
            else:
                registrar_log(nome_admin, "Limpou o aviso global.")
                page.snack_bar = ft.SnackBar(ft.Text("Aviso global removido!"), bgcolor="#F4A261")
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            print(ex)

    linha_broadcast = ft.Row([
        txt_aviso_global, 
        ft.ElevatedButton("Emitir / Limpar", on_click=salvar_aviso, style=ft.ButtonStyle(bgcolor="#E76F51", color="white"))
    ])

    # --- Lógica de Empresas ---
    def carregar_empresas(filtro=""):
        tabela_empresas.rows.clear()
        query = "SELECT id, nome_fantasia, razao_social, cnpj, COALESCE(ativa, true) as ativa FROM empresas WHERE nome_fantasia ILIKE %s ORDER BY id DESC;"
        try:
            empresas = execute_query(query, (f"%{filtro}%",), fetch_all=True) or []
            for emp in empresas:
                is_ativa = emp.get('ativa', True)
                tabela_empresas.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(emp.get('id', '')))),
                        ft.DataCell(ft.Text(emp.get('nome_fantasia') or emp.get('razao_social') or "Sem Nome", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(emp.get('cnpj') or "N/A")),
                        ft.DataCell(ft.Text("Ativa" if is_ativa else "Bloqueada", color="#2A9D8F" if is_ativa else "#E76F51")),
                        ft.DataCell(
                            ft.Row([
                                ft.ElevatedButton("Bloquear" if is_ativa else "Ativar", style=ft.ButtonStyle(color="white", bgcolor="#E76F51" if is_ativa else "#2A9D8F"), on_click=lambda e, eid=emp['id'], st=is_ativa: alternar_status_empresa(eid, st))
                            ])
                        )
                    ])
                )
        except Exception: pass
        page.update()

    def alternar_status_empresa(emp_id, status_atual):
        try:
            execute_query("UPDATE empresas SET ativa = %s WHERE id = %s;", (not status_atual, emp_id), commit=True)
            registrar_log(nome_admin, f"Alterou status da empresa ID {emp_id} para {not status_atual}")
        except Exception: pass
        carregar_empresas()

    # --- Modal Nova Empresa ---
    txt_nome_fantasia = ft.TextField(label="Nome Fantasia", text_size=14)
    txt_razao_social = ft.TextField(label="Razão Social", text_size=14)
    txt_cnpj = ft.TextField(label="CNPJ", text_size=14)
    txt_nome_responsavel = ft.TextField(label="Nome do Dono/Admin", text_size=14)
    txt_email = ft.TextField(label="E-mail de Login", text_size=14)
    txt_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, text_size=14)

    def salvar_nova_empresa(e):
        nome, razao, cnpj = txt_nome_fantasia.value.strip(), txt_razao_social.value.strip(), txt_cnpj.value.strip()
        nome_resp, email, senha_pura = txt_nome_responsavel.value.strip(), txt_email.value.strip(), txt_senha.value.strip()

        if not nome and not razao: return
        if not email or not senha_pura: return

        senha_hash = bcrypt.hashpw(senha_pura.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        query = """
            WITH nova_empresa AS (
                INSERT INTO empresas (nome_fantasia, razao_social, cnpj, ativa, plano_id) 
                VALUES (%s, %s, %s, true, 1) RETURNING id
            )
            INSERT INTO usuarios (nome, email, senha, perfil, empresa_id)
            SELECT %s, %s, %s, 'ADMIN', id FROM nova_empresa;
        """
        try:
            execute_query(query, (nome or razao, razao or nome, cnpj, nome_resp or "Admin", email, senha_hash), commit=True)
            registrar_log(nome_admin, f"Cadastrou nova empresa: {nome or razao}")
        except Exception as ex:
            print(f"Erro ao salvar: {ex}")

        txt_nome_fantasia.value = txt_razao_social.value = txt_cnpj.value = ""
        txt_nome_responsavel.value = txt_email.value = txt_senha.value = ""
        
        dialog_nova_empresa.open = False
        carregar_empresas()
        carregar_usuarios()
        atualizar_estatisticas()
        page.update()

    def fechar_dialog_nova_empresa(e):
        dialog_nova_empresa.open = False
        page.update()

    dialog_nova_empresa = ft.AlertDialog(
        title=ft.Text("Cadastrar Tenant e Login"),
        content=ft.Column([
            ft.Text("Dados da Empresa", weight="bold", color="#4CC9F0"),
            txt_nome_fantasia, txt_razao_social, txt_cnpj, ft.Divider(),
            ft.Text("Dados de Acesso (Admin)", weight="bold", color="#4CC9F0"),
            txt_nome_responsavel, txt_email, txt_senha
        ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),
        actions=[ft.TextButton("Cancelar", on_click=fechar_dialog_nova_empresa), ft.ElevatedButton("Salvar", on_click=salvar_nova_empresa)]
    )

    def abrir_modal_empresa(e):
        page.overlay.append(dialog_nova_empresa)
        dialog_nova_empresa.open = True
        page.update()

    # --- Modal Gerenciar Usuário (Editar Senha e Dados) ---
    usuario_em_edicao = [None]
    txt_edit_nome = ft.TextField(label="Nome", text_size=14)
    txt_edit_email = ft.TextField(label="E-mail", text_size=14)
    dd_edit_perfil = ft.Dropdown(
        label="Perfil",
        options=[ft.dropdown.Option("SUPER_ADMIN"), ft.dropdown.Option("ADMIN"), ft.dropdown.Option("STAFF")],
        text_size=14
    )
    txt_edit_senha = ft.TextField(label="Nova Senha (deixe em branco para manter)", password=True, can_reveal_password=True, text_size=14)

    def salvar_edicao_usuario(e):
        uid = usuario_em_edicao[0]
        if not uid: return
        nome, email, perfil, senha = txt_edit_nome.value.strip(), txt_edit_email.value.strip(), dd_edit_perfil.value, txt_edit_senha.value.strip()

        try:
            if senha:
                senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                execute_query("UPDATE usuarios SET nome=%s, email=%s, perfil=%s, senha=%s WHERE id=%s;", (nome, email, perfil, senha_hash, uid), commit=True)
            else:
                execute_query("UPDATE usuarios SET nome=%s, email=%s, perfil=%s WHERE id=%s;", (nome, email, perfil, uid), commit=True)
            registrar_log(nome_admin, f"Editou dados/senha do usuário ID {uid}")
        except Exception as ex:
            print(f"Erro ao editar usuário: {ex}")

        dialog_editar_usuario.open = False
        carregar_usuarios()
        page.update()

    def fechar_modal_edicao(e):
        dialog_editar_usuario.open = False
        page.update()

    dialog_editar_usuario = ft.AlertDialog(
        title=ft.Text("Gerenciar Usuário"),
        content=ft.Column([
            txt_edit_nome, txt_edit_email, dd_edit_perfil, ft.Divider(), txt_edit_senha
        ], tight=True, spacing=10),
        actions=[ft.TextButton("Cancelar", on_click=fechar_modal_edicao), ft.ElevatedButton("Salvar", on_click=salvar_edicao_usuario)]
    )

    def abrir_modal_edicao_usuario(usr):
        usuario_em_edicao[0] = usr['id']
        txt_edit_nome.value = usr.get('nome', '')
        txt_edit_email.value = usr.get('email', '')
        dd_edit_perfil.value = usr.get('perfil', 'STAFF')
        txt_edit_senha.value = ""
        
        page.overlay.append(dialog_editar_usuario)
        dialog_editar_usuario.open = True
        page.update()

    # --- Lógica de Usuários ---
    def carregar_usuarios(filtro=""):
        tabela_usuarios.rows.clear()
        query = "SELECT id, nome, email, perfil, empresa_id FROM usuarios WHERE nome ILIKE %s OR email ILIKE %s ORDER BY id DESC;"
        try:
            usuarios = execute_query(query, (f"%{filtro}%", f"%{filtro}%"), fetch_all=True) or []
            for usr in usuarios:
                tabela_usuarios.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(usr.get('id', '')))),
                        ft.DataCell(ft.Text(usr.get('nome') or "Sem Nome", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(usr.get('email') or "N/A")),
                        ft.DataCell(ft.Chip(label=ft.Text(usr.get('perfil') or "STAFF"))),
                        ft.DataCell(
                            ft.Row([
                                ft.ElevatedButton("Gerenciar", style=ft.ButtonStyle(color="white", bgcolor="#F4A261"), on_click=lambda e, u=usr: abrir_modal_edicao_usuario(u)),
                                ft.ElevatedButton("Acessar", style=ft.ButtonStyle(color="white", bgcolor="#4CC9F0"), on_click=lambda e, u=usr: disparar_ghost_login(u)),
                                ft.ElevatedButton("Excluir", style=ft.ButtonStyle(color="white", bgcolor="#D62828"), on_click=lambda e, uid=usr['id']: deletar_usr(uid))
                            ])
                        )
                    ])
                )
        except Exception: pass
        page.update()

    def disparar_ghost_login(usr):
        registrar_log(nome_admin, f"Tentou Ghost Login no usuário ID {usr['id']} ({usr['email']})")
        if on_ghost_login:
            on_ghost_login(usr)
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"Sessão ativada para {usr['email']}. Configure on_ghost_login no main.py para trocar a tela."), bgcolor="#F4A261")
            page.snack_bar.open = True
            page.update()

    def deletar_usr(uid):
        try:
            execute_query("DELETE FROM usuarios WHERE id = %s;", (uid,), commit=True)
            registrar_log(nome_admin, f"Deletou usuário ID {uid}")
            carregar_usuarios()
            atualizar_estatisticas()
        except Exception: pass

    # --- Lógica Financeira (Recebimentos) ---
    def carregar_financeiro():
        tabela_financeiro.rows.clear()
        try:
            query = """
                SELECT p.id, e.nome_fantasia, p.valor, p.data_vencimento, p.status 
                FROM pagamentos p
                LEFT JOIN empresas e ON p.empresa_id = e.id
                ORDER BY p.id DESC LIMIT 100;
            """
            faturas = execute_query(query, fetch_all=True) or []
            for fat in faturas:
                tabela_financeiro.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(fat.get('id', '')))),
                        ft.DataCell(ft.Text(fat.get('nome_fantasia') or "N/A")),
                        ft.DataCell(ft.Text(f"R$ {float(fat.get('valor', 0)):.2f}")),
                        ft.DataCell(ft.Text(str(fat.get('data_vencimento', '')))),
                        ft.DataCell(ft.Text(fat.get('status', 'PENDENTE'), color="#2A9D8F" if fat.get('status') == 'PAGO' else "#E76F51", weight=ft.FontWeight.BOLD))
                    ])
                )
        except Exception:
            tabela_financeiro.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("Tabela 'pagamentos' vazia ou inexistente.", color="#F4A261")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-"))]))
        page.update()

    def exportar_para_excel(e):
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(["ID", "Referência/Empresa", "Valor", "Data", "Status"])
        for row in tabela_financeiro.rows:
            linha = [cell.content.value for cell in row.cells]
            writer.writerow(linha)
        csv_string = output.getvalue()
        b64 = base64.b64encode(csv_string.encode('utf-8-sig')).decode('utf-8')
        
        url_data = f"data:text/csv;base64,{b64}"
        try:
            asyncio.create_task(page.launch_url(url_data))
        except Exception:
            try:
                page.launch_url(url_data)
            except Exception as ex:
                print(f"Erro ao disparar download: {ex}")

    # --- Lógica de Planos ---
    def carregar_planos():
        tabela_planos.rows.clear()
        try:
            planos = execute_query("SELECT id, nome, limite_usuarios, preco FROM planos ORDER BY id ASC;", fetch_all=True) or []
            for p in planos:
                tabela_planos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(p.get('id', '')))),
                        ft.DataCell(ft.Text(p.get('nome', ''), weight="bold")),
                        ft.DataCell(ft.Text("Ilimitado" if p.get('limite_usuarios', 0) >= 99999 else str(p.get('limite_usuarios', '0')))),
                        ft.DataCell(ft.Text(f"R$ {float(p.get('preco', 0)):.2f}"))
                    ])
                )
        except Exception:
            tabela_planos.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("Execute o SQL de planos.")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-"))]))
        page.update()

    # --- Lógica de Auditoria ---
    def carregar_auditoria():
        tabela_auditoria.rows.clear()
        try:
            logs = execute_query("SELECT id, ator, acao, data_hora FROM auditoria ORDER BY id DESC LIMIT 50;", fetch_all=True) or []
            for l in logs:
                tabela_auditoria.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(l.get('id', '')))),
                        ft.DataCell(ft.Text(str(l.get('data_hora', ''))[:16])),
                        ft.DataCell(ft.Text(l.get('ator', ''), color="#F4A261")),
                        ft.DataCell(ft.Text(l.get('acao', '')))
                    ])
                )
        except Exception:
            tabela_auditoria.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("Execute o SQL de auditoria.")), ft.DataCell(ft.Text("-"))]))
        page.update()

    # --- Criação das Tabelas ---
    tabela_empresas = ft.DataTable(columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Empresa")), ft.DataColumn(ft.Text("CNPJ")), ft.DataColumn(ft.Text("Status")), ft.DataColumn(ft.Text("Ações"))], rows=[])
    tabela_usuarios = ft.DataTable(columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Nome")), ft.DataColumn(ft.Text("E-mail")), ft.DataColumn(ft.Text("Perfil")), ft.DataColumn(ft.Text("Ações"))], rows=[])
    tabela_financeiro = ft.DataTable(columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Referência / Empresa")), ft.DataColumn(ft.Text("Valor")), ft.DataColumn(ft.Text("Vencimento")), ft.DataColumn(ft.Text("Status"))], rows=[])
    tabela_planos = ft.DataTable(columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Nome do Plano")), ft.DataColumn(ft.Text("Limite de Usuários")), ft.DataColumn(ft.Text("Preço Base"))], rows=[])
    tabela_auditoria = ft.DataTable(columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Data/Hora")), ft.DataColumn(ft.Text("Usuário (Ator)")), ft.DataColumn(ft.Text("Ação Realizada"))], rows=[])

    btn_add_empresa = ft.ElevatedButton("+ Nova Empresa", on_click=abrir_modal_empresa, style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"))

    carregar_empresas()
    carregar_usuarios()
    atualizar_estatisticas()

    # --- Conteúdo das Abas ---
    tab_empresas_content = ft.Column([
        ft.Row([
            ft.TextField(hint_text="Buscar empresas...", on_change=lambda e: carregar_empresas(e.control.value), expand=True),
            btn_add_empresa
        ]), 
        ft.Column([tabela_empresas], scroll=ft.ScrollMode.AUTO)
    ])
    
    tab_usuarios_content = ft.Column([ft.Row([ft.TextField(hint_text="Buscar usuários...", on_change=lambda e: carregar_usuarios(e.control.value), expand=True)]), ft.Column([tabela_usuarios], scroll=ft.ScrollMode.AUTO)])
    tab_financeiro_content = ft.Column([ft.Row([ft.Text("Gestão de Recebimentos e Faturas", size=18, weight="bold", expand=True), ft.ElevatedButton("Exportar Excel (CSV)", on_click=exportar_para_excel, style=ft.ButtonStyle(bgcolor="#1E293B", color="#4CC9F0"))]), ft.Column([tabela_financeiro], scroll=ft.ScrollMode.AUTO)])
    tab_planos_content = ft.Column([ft.Text("Gestão de Limites e Tiers do SaaS", size=18, weight="bold"), ft.Column([tabela_planos], scroll=ft.ScrollMode.AUTO)])
    tab_auditoria_content = ft.Column([ft.Text("Visão Raio-X (50 últimos registros)", size=18, weight="bold"), ft.Column([tabela_auditoria], scroll=ft.ScrollMode.AUTO)])

    content_area = ft.Container(content=tab_empresas_content, expand=True)

    def set_tab(index):
        for btn in [btn_tab1, btn_tab2, btn_tab3, btn_tab4, btn_tab5]:
            btn.style = ft.ButtonStyle(color="#94A3B8", bgcolor="transparent")
        
        if index == 0:
            btn_tab1.style = ft.ButtonStyle(color="#4CC9F0", bgcolor="#1E293B")
            content_area.content = tab_empresas_content
        elif index == 1:
            btn_tab2.style = ft.ButtonStyle(color="#4CC9F0", bgcolor="#1E293B")
            content_area.content = tab_usuarios_content
        elif index == 2:
            btn_tab3.style = ft.ButtonStyle(color="#4CC9F0", bgcolor="#1E293B")
            carregar_financeiro()
            content_area.content = tab_financeiro_content
        elif index == 3:
            btn_tab4.style = ft.ButtonStyle(color="#4CC9F0", bgcolor="#1E293B")
            carregar_planos()
            content_area.content = tab_planos_content
        elif index == 4:
            btn_tab5.style = ft.ButtonStyle(color="#4CC9F0", bgcolor="#1E293B")
            carregar_auditoria()
            content_area.content = tab_auditoria_content
        page.update()

    btn_tab1 = ft.ElevatedButton("Empresas", on_click=lambda _: set_tab(0), style=ft.ButtonStyle(color="#4CC9F0", bgcolor="#1E293B"))
    btn_tab2 = ft.ElevatedButton("Usuários", on_click=lambda _: set_tab(1), style=ft.ButtonStyle(color="#94A3B8", bgcolor="transparent"))
    btn_tab3 = ft.ElevatedButton("Financeiro", on_click=lambda _: set_tab(2), style=ft.ButtonStyle(color="#94A3B8", bgcolor="transparent"))
    btn_tab4 = ft.ElevatedButton("Planos", on_click=lambda _: set_tab(3), style=ft.ButtonStyle(color="#94A3B8", bgcolor="transparent"))
    btn_tab5 = ft.ElevatedButton("Auditoria", on_click=lambda _: set_tab(4), style=ft.ButtonStyle(color="#94A3B8", bgcolor="transparent"))

    tab_header = ft.Row([btn_tab1, btn_tab2, btn_tab3, btn_tab4, btn_tab5], spacing=10)

    # Dashboard Cards
    dev_stats_row = ft.Row([
        ft.Container(content=ft.Column([ft.Text("Total Empresas", color="#94A3B8"), txt_total_empresas]), bgcolor="#1E293B", padding=15, border_radius=8, expand=True),
        ft.Container(content=ft.Column([ft.Text("Total Usuários", color="#94A3B8"), txt_total_usuarios]), bgcolor="#1E293B", padding=15, border_radius=8, expand=True),
        ft.Container(content=ft.Column([ft.Text("Receita (Pagos)", color="#94A3B8"), txt_receita_total]), bgcolor="#1E293B", padding=15, border_radius=8, expand=True)
    ], spacing=20)

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Painel Master — Controle Total do SaaS", size=22, weight="bold", color="white"),
                ft.ElevatedButton("Sair", on_click=lambda e: on_logout() if on_logout else None)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            dev_stats_row,
            linha_broadcast,
            tab_header,
            content_area
        ], spacing=15, scroll=ft.ScrollMode.AUTO),
        padding=20, 
        expand=True, 
        bgcolor="#0B132B"
    )