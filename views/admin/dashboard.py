import flet as ft
from datetime import datetime
import io
import csv
import base64

try:
    from database import execute_query
except ImportError:
    try:
        from database.connection import execute_query
    except ImportError:
        from database.db import execute_query

try:
    from services.export_service import generate_financial_csv
except ImportError:
    def generate_financial_csv(l): return ""

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def AdminDashboardView(page: ft.Page, user=None, on_logout=None, on_navigate=None):
    nome_admin = user.get('nome', 'Administrador') if user else 'Administrador'
    email_admin = user.get('email', '') if user else ''
    empresa_id = user.get('empresa_id') if user else 1

    staff_link = f"https://eventcasting.onrender.com/?register&empresa={empresa_id}"

    # --- INICIALIZAÇÃO DE TABELAS ---
    def init_tables():
        query_tables = """
            ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rg VARCHAR(30);
            ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS cpf VARCHAR(30);
            ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS whatsapp VARCHAR(30);

            CREATE TABLE IF NOT EXISTS financeiro (
                id SERIAL PRIMARY KEY,
                empresa_id INT NOT NULL,
                evento_id INT,
                tipo VARCHAR(20) NOT NULL,
                descricao VARCHAR(255) NOT NULL,
                categoria VARCHAR(100),
                valor NUMERIC(10,2) NOT NULL,
                imposto_percentual NUMERIC(5,2) DEFAULT 0,
                data_lancamento DATE DEFAULT CURRENT_DATE
            );
            CREATE TABLE IF NOT EXISTS notas_fiscais (
                id SERIAL PRIMARY KEY,
                empresa_id INT NOT NULL,
                tomador_nome VARCHAR(200) NOT NULL,
                tomador_cnpj VARCHAR(20) NOT NULL,
                descricao_servico TEXT NOT NULL,
                valor_total NUMERIC(10,2) NOT NULL,
                aliquota_iss NUMERIC(5,2) DEFAULT 0,
                status VARCHAR(30) DEFAULT 'RASCUNHO',
                data_emissao TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS presencas_pagamentos (
                id SERIAL PRIMARY KEY,
                candidatura_id INT NOT NULL UNIQUE,
                dias_presentes INT DEFAULT 0,
                status_pagamento VARCHAR(20) DEFAULT 'PENDENTE',
                valor_pago NUMERIC(10,2) DEFAULT 0.00,
                data_pagamento TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS chamados_suporte (
                id SERIAL PRIMARY KEY,
                empresa_id INT NOT NULL,
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
            execute_query(query_tables, commit=True)
        except Exception as ex:
            print(f"Erro init tables: {ex}")

    init_tables()

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(content=ft.Text(msg, color="white", weight="bold"), bgcolor="#E76F51" if is_error else "#2A9D8F")
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def parse_data_br_to_iso(data_br):
        try:
            return datetime.strptime(data_br.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception:
            return None

    def parse_data_iso_to_br(data_iso):
        try:
            return datetime.strptime(str(data_iso), "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return str(data_iso)

    # --- EDICAO DE PERFIL ---
    txt_prof_nome = ft.TextField(label="Seu Nome Completo *", value=nome_admin, text_size=13, border_radius=8)
    txt_prof_email = ft.TextField(label="Seu E-mail *", value=email_admin, text_size=13, border_radius=8)
    txt_prof_senha = ft.TextField(label="Nova Senha (Deixe em branco para não alterar)", password=True, can_reveal_password=True, text_size=13, border_radius=8)
    txt_prof_razao = ft.TextField(label="Razão Social (Bloqueado)", value="Empresa Licenciada SaaS", read_only=True, text_size=13, border_radius=8, bgcolor="#0F172A")
    txt_prof_cnpj = ft.TextField(label="CNPJ (Bloqueado)", value="00.000.000/0001-00", read_only=True, text_size=13, border_radius=8, bgcolor="#0F172A")

    def carregar_dados_empresa_perfil():
        try:
            emp = execute_query("SELECT COALESCE(nome, 'Empresa') as nome, COALESCE(cnpj, '00.000.000/0001-00') as cnpj FROM empresas WHERE id = %s;", (empresa_id,), fetch_all=True)
            if emp:
                txt_prof_razao.value = emp[0].get('nome', 'Empresa')
                txt_prof_cnpj.value = emp[0].get('cnpj', '00.000.000/0001-00')
                page.update()
        except Exception:
            pass

    def handle_salvar_perfil(e):
        if not txt_prof_nome.value.strip() or not txt_prof_email.value.strip():
            show_snack("Nome e E-mail são obrigatórios!")
            return
        try:
            usr_id = user.get('id') if user else None
            if txt_prof_senha.value.strip():
                execute_query("UPDATE usuarios SET nome = %s, email = %s, senha = %s WHERE id = %s;", (txt_prof_nome.value.strip(), txt_prof_email.value.strip(), txt_prof_senha.value.strip(), usr_id), commit=True)
            else:
                execute_query("UPDATE usuarios SET nome = %s, email = %s WHERE id = %s;", (txt_prof_nome.value.strip(), txt_prof_email.value.strip(), usr_id), commit=True)
            show_snack("Perfil atualizado com sucesso!", is_error=False)
        except Exception as ex:
            show_snack(f"Erro ao atualizar perfil: {ex}")

    # --- CONTROLES DE EVENTO & VAGA ---
    txt_nome_evento = ft.TextField(label="Nome do Evento *", text_size=13, border_radius=8)
    txt_local_evento = ft.TextField(label="Localização / Endereço *", text_size=13, border_radius=8)
    txt_data_inicio = ft.TextField(label="Data Início (DD/MM/AAAA) *", hint_text="20/08/2026", text_size=13, border_radius=8, expand=True)
    txt_data_fim = ft.TextField(label="Data Fim (DD/MM/AAAA) *", hint_text="22/08/2026", text_size=13, border_radius=8, expand=True)
    txt_hora_inicio = ft.TextField(label="Hora Início (HH:MM) *", hint_text="08:00", text_size=13, border_radius=8, expand=True)
    txt_hora_fim = ft.TextField(label="Hora Fim (HH:MM) *", hint_text="18:00", text_size=13, border_radius=8, expand=True)

    dd_eventos_vagas = ft.Dropdown(label="Selecione o Evento *", text_size=13, border_radius=8)
    txt_funcao_vaga = ft.TextField(label="Função (Ex: Recepcionista) *", text_size=13, border_radius=8)
    txt_diaria_vaga = ft.TextField(label="Valor Diária (R$) *", text_size=13, border_radius=8, expand=True)
    txt_qtd_vagas = ft.TextField(label="Quantidade de Vagas *", text_size=13, border_radius=8, expand=True)

    dd_eventos_cand = ft.Dropdown(label="Filtrar por Evento", value="TODOS", text_size=13, border_radius=8)
    list_candidatos = ft.Column(spacing=10)

    list_pagamentos_pendentes = ft.Column(spacing=10)
    list_pagamentos_finalizados = ft.Column(spacing=10)

    # PROCESSAMENTO MANUAL/LOTE DE PIX
    txt_pix_lote_input = ft.TextField(label="Cole os dados do Pix (CPF;VALOR) para dar baixa em lote:", multiline=True, min_lines=2, text_size=11, border_radius=8)

    def handle_processar_pix_lote(e):
        if not txt_pix_lote_input.value or not txt_pix_lote_input.value.strip():
            show_snack("Cole o conteúdo do CSV ou texto no campo!")
            return
        try:
            linhas = txt_pix_lote_input.value.strip().split('\n')
            count = 0
            for row in linhas:
                parts = row.split(';') if ';' in row else row.split(',')
                if len(parts) >= 2:
                    cpf_pix = parts[0].strip()
                    v_pago = float(parts[1].replace(',', '.').strip())
                    execute_query("""
                        UPDATE presencas_pagamentos SET status_pagamento = 'PAGO', valor_pago = %s, data_pagamento = NOW()
                        WHERE candidatura_id IN (
                            SELECT c.id FROM candidaturas c JOIN usuarios u ON c.usuario_id = u.id WHERE u.cpf = %s
                        );
                    """, (v_pago, cpf_pix), commit=True)
                    count += 1
            show_snack(f"Processado em lote! {count} pagamentos atualizados.", is_error=False)
            txt_pix_lote_input.value = ""
            carregar_pagamentos_pendentes()
            carregar_pagamentos_finalizados()
        except Exception as ex:
            show_snack(f"Erro ao processar lote: {ex}")

    # --- FINANCEIRO & DRE ---
    dd_fin_tipo = ft.Dropdown(label="Tipo *", options=[ft.dropdown.Option("RECEITA", "Receita (Entrada)"), ft.dropdown.Option("DESPESA", "Despesa (Saída)")], text_size=13)
    txt_fin_desc = ft.TextField(label="Descrição *", text_size=13, border_radius=8)
    txt_fin_cat = ft.TextField(label="Categoria (Ex: Staff, Cachê, Aluguel)", text_size=13, border_radius=8)
    txt_fin_valor = ft.TextField(label="Valor (R$) *", text_size=13, border_radius=8)
    txt_fin_imposto = ft.TextField(label="% Imposto (Ex: 6.0)", value="0", text_size=13, border_radius=8)
    list_financeiro = ft.Column(spacing=8)
    
    txt_fin_resumo_bruto = ft.Text("R$ 0,00", size=15, weight="bold", color="#2A9D8F")
    txt_fin_resumo_imposto = ft.Text("R$ 0,00", size=15, weight="bold", color="#E76F51")
    txt_fin_resumo_despesa = ft.Text("R$ 0,00", size=15, weight="bold", color="#E63946")
    txt_fin_resumo_liquido = ft.Text("R$ 0,00", size=15, weight="bold", color="#4CC9F0")
    
    pb_lucratividade = ft.ProgressBar(value=0.0, color="#4CC9F0", bgcolor="#1E293B", height=10)
    lbl_margem_lucro = ft.Text("Margem de Lucro: 0%", size=12, color="#94A3B8")

    # PROPOSTA PDF
    txt_prop_cliente = ft.TextField(label="Nome / Razão Social do Cliente *", text_size=13, border_radius=8)
    txt_prop_cnpj = ft.TextField(label="CNPJ / CPF do Cliente *", text_size=13, border_radius=8)
    txt_prop_evento = ft.TextField(label="Nome do Evento / Projeto *", text_size=13, border_radius=8)
    txt_prop_descricao = ft.TextField(label="Descrição dos Serviços *", multiline=True, min_lines=2, text_size=13, border_radius=8)
    txt_prop_qtd_staff = ft.TextField(label="Qtd. de Profissionais *", value="1", text_size=13, border_radius=8)
    txt_prop_diaria_unit = ft.TextField(label="Valor Unitário p/ Diária (R$) *", text_size=13, border_radius=8)
    txt_prop_dias = ft.TextField(label="Qtd. de Dias de Evento *", value="1", text_size=13, border_radius=8)
    txt_prop_condicoes = ft.TextField(label="Condições de Pagamento", value="50% no aceite e 50% em até 5 dias pós evento.", text_size=13, border_radius=8)

    # NF
    txt_nf_tomador = ft.TextField(label="Razão Social / Nome do Cliente *", text_size=13, border_radius=8)
    txt_nf_cnpj = ft.TextField(label="CNPJ / CPF do Cliente *", text_size=13, border_radius=8)
    txt_nf_desc = ft.TextField(label="Descrição dos Serviços *", multiline=True, min_lines=2, text_size=13, border_radius=8)
    txt_nf_valor = ft.TextField(label="Valor Total da Nota (R$) *", text_size=13, border_radius=8)
    txt_nf_aliquota = ft.TextField(label="Alíquota ISS (%)", value="5.0", text_size=13, border_radius=8)
    list_notas_fiscais = ft.Column(spacing=10)

    # CHAMADOS
    txt_chamado_assunto = ft.TextField(label="Assunto do Chamado *", text_size=13, border_radius=8)
    dd_chamado_cat = ft.Dropdown(
        label="Categoria *", value="Dúvida", text_size=13, border_radius=8,
        options=[
            ft.dropdown.Option("Dúvida", "Dúvida / Ajuda"),
            ft.dropdown.Option("Financeiro", "Financeiro / Faturamento"),
            ft.dropdown.Option("Bug", "Problema no Sistema"),
            ft.dropdown.Option("Sugestão", "Sugestão de Funcionalidade")
        ]
    )
    dd_chamado_prio = ft.Dropdown(
        label="Prioridade *", value="MÉDIA", text_size=13, border_radius=8,
        options=[
            ft.dropdown.Option("BAIXA", "Baixa"),
            ft.dropdown.Option("MÉDIA", "Média"),
            ft.dropdown.Option("ALTA", "Alta"),
            ft.dropdown.Option("URGENTE", "Urgente")
        ]
    )
    txt_chamado_msg = ft.TextField(label="Descrição Detalhada do Problema *", multiline=True, min_lines=3, text_size=13, border_radius=8)
    list_meus_chamados = ft.Column(spacing=10)

    # --- LÓGICA DE DADOS ---
    def carregar_eventos_dropdowns():
        if not empresa_id: return
        try:
            evs = execute_query("SELECT id, nome FROM eventos WHERE empresa_id = %s ORDER BY id DESC;", (empresa_id,), fetch_all=True)
            dd_eventos_vagas.options.clear()
            dd_eventos_cand.options.clear()
            dd_eventos_cand.options.append(ft.dropdown.Option("TODOS", "Todos os Eventos"))
            if evs:
                for ev in evs:
                    dd_eventos_vagas.options.append(ft.dropdown.Option(str(ev['id']), ev['nome']))
                    dd_eventos_cand.options.append(ft.dropdown.Option(str(ev['id']), ev['nome']))
            page.update()
        except Exception:
            pass

    def handle_criar_evento(e):
        dt_in_iso = parse_data_br_to_iso(txt_data_inicio.value or "")
        dt_fim_iso = parse_data_br_to_iso(txt_data_fim.value or "")

        if not all([txt_nome_evento.value, txt_local_evento.value, dt_in_iso, dt_fim_iso, txt_hora_inicio.value, txt_hora_fim.value]):
            show_snack("Preencha todos os campos do evento com data válida (DD/MM/AAAA)!")
            return

        try:
            local_com_horario = f"{txt_local_evento.value.strip()} | Horário: {txt_hora_inicio.value.strip()} às {txt_hora_fim.value.strip()}"
            query = "INSERT INTO eventos (empresa_id, nome, local, data_inicio, data_fim) VALUES (%s, %s, %s, %s, %s);"
            execute_query(query, (empresa_id, txt_nome_evento.value.strip(), local_com_horario, dt_in_iso, dt_fim_iso), commit=True)
            show_snack("Evento cadastrado com sucesso!", is_error=False)
            txt_nome_evento.value = ""
            txt_local_evento.value = ""
            txt_data_inicio.value = ""
            txt_data_fim.value = ""
            txt_hora_inicio.value = ""
            txt_hora_fim.value = ""
            carregar_eventos_dropdowns()
        except Exception as ex:
            show_snack(f"Erro ao cadastrar evento: {ex}")

    def handle_criar_vaga(e):
        if not all([dd_eventos_vagas.value, txt_funcao_vaga.value, txt_diaria_vaga.value, txt_qtd_vagas.value]):
            show_snack("Preencha todos os campos da vaga!")
            return
        try:
            query = "INSERT INTO vagas (evento_id, funcao, valor_diaria, quantidade, status) VALUES (%s, %s, %s, %s, 'ABERTA');"
            execute_query(query, (int(dd_eventos_vagas.value), txt_funcao_vaga.value.strip(), float(txt_diaria_vaga.value.replace(',', '.')), int(txt_qtd_vagas.value)), commit=True)
            show_snack("Vaga publicada com sucesso!", is_error=False)
            txt_funcao_vaga.value = ""
            txt_diaria_vaga.value = ""
            txt_qtd_vagas.value = ""
        except Exception as ex:
            show_snack(f"Erro ao publicar vaga: {ex}")

    def carregar_candidatos(e=None):
        list_candidatos.controls.clear()
        try:
            filtro_ev = dd_eventos_cand.value

            if filtro_ev and filtro_ev != "TODOS":
                query = """
                    SELECT c.id as cand_id, u.nome, u.email, COALESCE(u.whatsapp, 'N/A') as whatsapp, COALESCE(u.cpf, 'N/A') as cpf, COALESCE(u.rg, 'N/A') as rg,
                           v.funcao, c.status, e.nome as evento_nome
                    FROM candidaturas c
                    JOIN vagas v ON c.vaga_id = v.id
                    JOIN eventos e ON v.evento_id = e.id
                    JOIN usuarios u ON c.usuario_id = u.id
                    WHERE e.empresa_id = %s AND v.evento_id = %s ORDER BY c.id DESC;
                """
                cands = execute_query(query, (empresa_id, int(filtro_ev)), fetch_all=True) or []
            else:
                query = """
                    SELECT c.id as cand_id, u.nome, u.email, COALESCE(u.whatsapp, 'N/A') as whatsapp, COALESCE(u.cpf, 'N/A') as cpf, COALESCE(u.rg, 'N/A') as rg,
                           v.funcao, c.status, e.nome as evento_nome
                    FROM candidaturas c
                    JOIN vagas v ON c.vaga_id = v.id
                    JOIN eventos e ON v.evento_id = e.id
                    JOIN usuarios u ON c.usuario_id = u.id
                    WHERE e.empresa_id = %s ORDER BY c.id DESC;
                """
                cands = execute_query(query, (empresa_id,), fetch_all=True) or []

            if not cands:
                list_candidatos.controls.append(ft.Text("Nenhuma candidatura encontrada.", color="#94A3B8"))
            else:
                for c in cands:
                    cand_id = c['cand_id']
                    st = str(c['status']).upper()

                    def responder(cid, status_novo):
                        execute_query("UPDATE candidaturas SET status = %s WHERE id = %s;", (status_novo, cid), commit=True)
                        show_snack(f"Candidatura {status_novo.lower()}!", is_error=False)
                        carregar_candidatos()

                    list_candidatos.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=12, border_radius=8,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"👤 {c['nome']}", weight="bold", color="white", size=14),
                                    ft.Text(f"Status: {st}", color="#4CC9F0" if st == 'PENDENTE' else ("#2A9D8F" if st == 'APROVADO' else "#E76F51"), weight="bold", size=12)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Evento: {c.get('evento_nome', 'N/A')} | Função: {c['funcao']}", size=12, color="#4CC9F0"),
                                ft.Text(f"CPF: {c['cpf']} | RG: {c['rg']}", size=11, color="#94A3B8"),
                                ft.Text(f"WhatsApp: {c['whatsapp']} | E-mail: {c['email']}", size=11, color="#94A3B8"),
                                ft.Row([
                                    ft.ElevatedButton("Aprovar", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), height=35, on_click=lambda _, cid=cand_id: responder(cid, "APROVADO")),
                                    ft.ElevatedButton("Recusar", style=ft.ButtonStyle(bgcolor="#E76F51", color="white"), height=35, on_click=lambda _, cid=cand_id: responder(cid, "RECUSADO")),
                                ], spacing=10)
                            ], spacing=6)
                        )
                    )
        except Exception as ex:
            list_candidatos.controls.append(ft.Text(f"Erro ao buscar candidatos: {ex}", color="#E76F51"))
        page.update()

    dd_eventos_cand.on_change = carregar_candidatos

    def carregar_pagamentos_pendentes():
        list_pagamentos_pendentes.controls.clear()
        try:
            query = """
                SELECT c.id as cand_id, u.nome, COALESCE(u.cpf, 'N/A') as cpf, COALESCE(u.whatsapp, 'N/A') as whatsapp,
                       v.funcao, v.valor_diaria, e.nome as evento_nome,
                       COALESCE(p.dias_presentes, 0) as dias_presentes,
                       COALESCE(p.status_pagamento, 'PENDENTE') as status_pagamento
                FROM candidaturas c
                JOIN vagas v ON c.vaga_id = v.id
                JOIN eventos e ON v.evento_id = e.id
                JOIN usuarios u ON c.usuario_id = u.id
                LEFT JOIN presencas_pagamentos p ON c.id = p.candidatura_id
                WHERE e.empresa_id = %s AND c.status = 'APROVADO' AND COALESCE(p.status_pagamento, 'PENDENTE') != 'PAGO';
            """
            pags = execute_query(query, (empresa_id,), fetch_all=True) or []

            if not pags:
                list_pagamentos_pendentes.controls.append(ft.Text("Nenhum pagamento pendente no momento.", color="#2A9D8F"))
            else:
                for p in pags:
                    cid = p['cand_id']
                    st_pag = str(p['status_pagamento']).upper()
                    dias_pres = p['dias_presentes']
                    val_diaria = float(p['valor_diaria'])

                    txt_dias_in = ft.TextField(value=str(dias_pres), width=60, text_size=12, label="Dias")
                    dd_st_pag = ft.Dropdown(
                        value=st_pag, width=130, text_size=12,
                        options=[
                            ft.dropdown.Option("PENDENTE", "PENDENTE"),
                            ft.dropdown.Option("PARCIAL", "PARCIAL"),
                            ft.dropdown.Option("PAGO", "PAGO (Dar Baixa)")
                        ]
                    )

                    def dar_baixa_pagamento(c_id, d_input, st_input, v_diaria):
                        try:
                            dias = int(d_input.value or 0)
                            novo_st = st_input.value
                            v_pago = dias * v_diaria if novo_st == 'PAGO' else (v_diaria * dias * 0.5 if novo_st == 'PARCIAL' else 0.0)

                            query_upsert = """
                                INSERT INTO presencas_pagamentos (candidatura_id, dias_presentes, status_pagamento, valor_pago, data_pagamento)
                                VALUES (%s, %s, %s, %s, NOW())
                                ON CONFLICT (candidatura_id) 
                                DO UPDATE SET dias_presentes = EXCLUDED.dias_presentes,
                                              status_pagamento = EXCLUDED.status_pagamento,
                                              valor_pago = EXCLUDED.valor_pago,
                                              data_pagamento = NOW();
                            """
                            execute_query(query_upsert, (c_id, dias, novo_st, v_pago), commit=True)
                            
                            if novo_st == 'PAGO':
                                show_snack("Baixa efetuada! Movido para a aba de Finalizados.", is_error=False)
                            else:
                                show_snack("Status atualizado!", is_error=False)

                            carregar_pagamentos_pendentes()
                            carregar_pagamentos_finalizados()

                        except Exception as ex:
                            show_snack(f"Erro ao salvar: {ex}")

                    list_pagamentos_pendentes.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=12, border_radius=8,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"👤 {p['nome']} ({p['funcao']})", weight="bold", color="white", size=14),
                                    ft.Text(f"Diária: R$ {val_diaria:.2f}", color="#2A9D8F", weight="bold", size=13)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Evento: {p['evento_nome']} | Pix (CPF): {p['cpf']}", size=11, color="#94A3B8"),
                                ft.Row([
                                    txt_dias_in,
                                    dd_st_pag,
                                    ft.ElevatedButton("Salvar / Baixa", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"), height=38, on_click=lambda _, c_id=cid, din=txt_dias_in, stin=dd_st_pag, vd=val_diaria: dar_baixa_pagamento(c_id, din, stin, vd)),
                                    ft.ElevatedButton("Copiar Pix", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), height=38, on_click=lambda _, pix=p['cpf']: (setattr(page, 'clipboard', pix), show_snack("Chave Pix Copiada!", is_error=False)))
                                ], spacing=8, scroll=ft.ScrollMode.AUTO)
                            ], spacing=6)
                        )
                    )
        except Exception as ex:
            list_pagamentos_pendentes.controls.append(ft.Text(f"Erro ao carregar pagamentos: {ex}", color="#E76F51"))
        page.update()

    def carregar_pagamentos_finalizados():
        list_pagamentos_finalizados.controls.clear()
        try:
            query = """
                SELECT c.id as cand_id, u.nome, COALESCE(u.cpf, 'N/A') as cpf, COALESCE(u.whatsapp, 'N/A') as whatsapp,
                       v.funcao, v.valor_diaria, e.nome as evento_nome,
                       p.dias_presentes, p.valor_pago, p.data_pagamento
                FROM candidaturas c
                JOIN vagas v ON c.vaga_id = v.id
                JOIN eventos e ON v.evento_id = e.id
                JOIN usuarios u ON c.usuario_id = u.id
                JOIN presencas_pagamentos p ON c.id = p.candidatura_id
                WHERE e.empresa_id = %s AND p.status_pagamento = 'PAGO'
                ORDER BY p.data_pagamento DESC;
            """
            fin = execute_query(query, (empresa_id,), fetch_all=True) or []

            if not fin:
                list_pagamentos_finalizados.controls.append(ft.Text("Nenhum pagamento finalizado ainda.", color="#94A3B8"))
            else:
                for f in fin:
                    v_pago = float(f.get('valor_pago') or 0.0)
                    dt_pag = str(f.get('data_pagamento') or 'N/A')

                    list_pagamentos_finalizados.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=12, border_radius=8,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"✅ {f['nome']} — {f['funcao']}", weight="bold", color="white", size=14),
                                    ft.Text(f"Total Pago: R$ {v_pago:.2f}", color="#2A9D8F", weight="bold", size=14)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Evento: {f['evento_nome']} | Dias Trabalhados: {f['dias_presentes']}", size=12, color="#4CC9F0"),
                                ft.Text(f"CPF: {f['cpf']} | WhatsApp: {f['whatsapp']}", size=11, color="#94A3B8"),
                                ft.Text(f"Data da Baixa: {dt_pag}", size=10, color="#94A3B8")
                            ], spacing=4)
                        )
                    )
        except Exception as ex:
            list_pagamentos_finalizados.controls.append(ft.Text(f"Erro ao carregar finalizados: {ex}", color="#E76F51"))
        page.update()

    def carregar_financeiro():
        list_financeiro.controls.clear()
        try:
            query = "SELECT id, tipo, descricao, categoria, valor, imposto_percentual, data_lancamento FROM financeiro WHERE empresa_id = %s ORDER BY id DESC;"
            lancs = execute_query(query, (empresa_id,), fetch_all=True) or []

            tot_bruto = 0.0
            tot_imposto = 0.0
            tot_despesas = 0.0

            for l in lancs:
                v = float(l['valor'])
                imp_p = float(l.get('imposto_percentual') or 0.0)
                
                if l['tipo'] == 'RECEITA':
                    tot_bruto += v
                    tot_imposto += v * (imp_p / 100.0)
                else:
                    tot_despesas += v

                col_cor = "#2A9D8F" if l['tipo'] == 'RECEITA' else "#E76F51"
                dt_br = parse_data_iso_to_br(l['data_lancamento'])

                list_financeiro.controls.append(
                    ft.Container(
                        bgcolor="#1E293B", padding=10, border_radius=6,
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"[{l['tipo']}] {l['descricao']}", weight="bold", color="white", size=13),
                                ft.Text(f"Categoria: {l.get('categoria', 'Geral')} | Data: {dt_br}", size=11, color="#94A3B8")
                            ], expand=True),
                            ft.Text(f"R$ {v:.2f}", weight="bold", color=col_cor, size=13)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                )

            lucro_liquido = tot_bruto - tot_despesas - tot_imposto
            txt_fin_resumo_bruto.value = f"R$ {tot_bruto:.2f}"
            txt_fin_resumo_imposto.value = f"R$ {tot_imposto:.2f}"
            txt_fin_resumo_despesa.value = f"R$ {tot_despesas:.2f}"
            txt_fin_resumo_liquido.value = f"R$ {lucro_liquido:.2f}"

            if tot_bruto > 0:
                perc_lucro = max(0.0, min(1.0, lucro_liquido / tot_bruto))
                pb_lucratividade.value = perc_lucro
                lbl_margem_lucro.value = f"Margem de Lucro Líquido: {(perc_lucro * 100):.1f}%"
            else:
                pb_lucratividade.value = 0.0
                lbl_margem_lucro.value = "Margem de Lucro: 0%"

        except Exception as ex:
            list_financeiro.controls.append(ft.Text(f"Erro no financeiro: {ex}", color="#E76F51"))
        page.update()

    def handle_lancar_financeiro(e):
        if not all([dd_fin_tipo.value, txt_fin_desc.value, txt_fin_valor.value]):
            show_snack("Preencha tipo, descrição e valor!")
            return
        try:
            val = float(txt_fin_valor.value.replace(',', '.'))
            imp = float(txt_fin_imposto.value.replace(',', '.')) if txt_fin_imposto.value else 0.0
            query = "INSERT INTO financeiro (empresa_id, tipo, descricao, categoria, valor, imposto_percentual) VALUES (%s, %s, %s, %s, %s, %s);"
            execute_query(query, (empresa_id, dd_fin_tipo.value, txt_fin_desc.value.strip(), txt_fin_cat.value.strip(), val, imp), commit=True)
            show_snack("Lançamento efetuado com sucesso!", is_error=False)
            txt_fin_desc.value = ""
            txt_fin_cat.value = ""
            txt_fin_valor.value = ""
            carregar_financeiro()
        except Exception as ex:
            show_snack(f"Erro ao lançar no financeiro: {ex}")

    def handle_exportar_csv(e):
        try:
            query = "SELECT id, tipo, descricao, categoria, valor, imposto_percentual, data_lancamento FROM financeiro WHERE empresa_id = %s ORDER BY id DESC;"
            lancs = execute_query(query, (empresa_id,), fetch_all=True) or []
            csv_data = generate_financial_csv(lancs)
            page.clipboard = csv_data
            show_snack("CSV copiado para a área de transferência com sucesso!", is_error=False)
        except Exception as ex:
            show_snack(f"Erro ao exportar CSV: {ex}")

    def handle_gerar_proposta_pdf(e):
        if not all([txt_prop_cliente.value, txt_prop_cnpj.value, txt_prop_evento.value, txt_prop_diaria_unit.value]):
            show_snack("Preencha os campos obrigatórios da Proposta Comercial!")
            return

        try:
            qtd_staff = int(txt_prop_qtd_staff.value or 1)
            v_unit = float(txt_prop_diaria_unit.value.replace(',', '.'))
            dias = int(txt_prop_dias.value or 1)
            val_total = qtd_staff * v_unit * dias

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            p.setFont("Helvetica-Bold", 18)
            p.drawString(50, 750, "PROPOSTA COMERCIAL — EVENT CASTING")
            p.setFont("Helvetica", 10)
            p.drawString(50, 735, f"Data: {datetime.now().strftime('%d/%m/%Y')} | Empresa ID: {empresa_id}")
            p.line(50, 725, 550, 725)

            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, 700, f"CLIENTE / TOMADOR: {txt_prop_cliente.value}")
            p.setFont("Helvetica", 10)
            p.drawString(50, 685, f"CPF/CNPJ: {txt_prop_cnpj.value}")
            p.drawString(50, 670, f"PROJETO / EVENTO: {txt_prop_evento.value}")

            p.line(50, 655, 550, 655)
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, 635, "ESCOPO DO SERVIÇO:")
            
            p.setFont("Helvetica", 10)
            text_obj = p.beginText(50, 620)
            text_obj.setFont("Helvetica", 10)
            text_obj.textLines(txt_prop_descricao.value or "Fornecimento de equipe especializada para eventos.")
            p.drawText(text_obj)

            p.line(50, 550, 550, 550)
            p.setFont("Helvetica-Bold", 11)
            p.drawString(50, 530, f"Profissionais: {qtd_staff} staff(s) | Dias: {dias} dia(s)")
            p.drawString(50, 515, f"Valor Unitário por Diária: R$ {v_unit:.2f}")
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, 485, f"VALOR TOTAL DA PROPOSTA: R$ {val_total:.2f}")

            p.line(50, 470, 550, 470)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, 450, "CONDIÇÕES DE PAGAMENTO:")
            p.setFont("Helvetica", 9)
            p.drawString(50, 435, txt_prop_condicoes.value)

            p.showPage()
            p.save()

            buffer.seek(0)
            pdf_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            page.clipboard = f"data:application/pdf;base64,{pdf_b64}"
            show_snack(f"Proposta de R$ {val_total:.2f} gerada em PDF e copiada!", is_error=False)
        except Exception as ex:
            show_snack(f"Erro ao gerar proposta PDF: {ex}")

    def carregar_notas_fiscais():
        list_notas_fiscais.controls.clear()
        try:
            query = "SELECT id, tomador_nome, tomador_cnpj, descricao_servico, valor_total, aliquota_iss, status, data_emissao FROM notas_fiscais WHERE empresa_id = %s ORDER BY id DESC;"
            nfs = execute_query(query, (empresa_id,), fetch_all=True) or []
            if not nfs:
                list_notas_fiscais.controls.append(ft.Text("Nenhuma nota fiscal registrada.", color="#94A3B8"))
            else:
                for nf in nfs:
                    v_tot = float(nf['valor_total'])
                    aliq = float(nf.get('aliquota_iss') or 0.0)
                    v_iss = v_tot * (aliq / 100.0)
                    list_notas_fiscais.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=12, border_radius=8,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"📄 NF #{nf['id']} — {nf['tomador_nome']}", weight="bold", color="white"),
                                    ft.Text(f"Status: {nf['status']}", color="#2A9D8F", weight="bold", size=12)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"CNPJ/CPF: {nf['tomador_cnpj']} | Serviço: {nf['descricao_servico']}", size=11, color="#94A3B8"),
                                ft.Text(f"Valor Total: R$ {v_tot:.2f} | Imposto ISS ({aliq}%): R$ {v_iss:.2f}", size=12, color="#4CC9F0", weight="bold")
                            ], spacing=4)
                        )
                    )
        except Exception as ex:
            list_notas_fiscais.controls.append(ft.Text(f"Erro ao carregar NF: {ex}", color="#E76F51"))
        page.update()

    def handle_gerar_nf(e):
        if not all([txt_nf_tomador.value, txt_nf_cnpj.value, txt_nf_desc.value, txt_nf_valor.value]):
            show_snack("Preencha todos os campos da Nota Fiscal!")
            return
        try:
            v_tot = float(txt_nf_valor.value.replace(',', '.'))
            aliq = float(txt_nf_aliquota.value.replace(',', '.')) if txt_nf_aliquota.value else 0.0
            query = "INSERT INTO notas_fiscais (empresa_id, tomador_nome, tomador_cnpj, descricao_servico, valor_total, aliquota_iss, status) VALUES (%s, %s, %s, %s, %s, %s, 'EMITIDA');"
            execute_query(query, (empresa_id, txt_nf_tomador.value.strip(), txt_nf_cnpj.value.strip(), txt_nf_desc.value.strip(), v_tot, aliq), commit=True)
            show_snack("Nota Fiscal registrada com sucesso!", is_error=False)
            txt_nf_tomador.value = ""
            txt_nf_cnpj.value = ""
            txt_nf_desc.value = ""
            txt_nf_valor.value = ""
            carregar_notas_fiscais()
        except Exception as ex:
            show_snack(f"Erro ao emitir NF: {ex}")

    def handle_abrir_chamado(e):
        if not all([txt_chamado_assunto.value, txt_chamado_msg.value]):
            show_snack("Preencha o assunto e a mensagem do chamado!")
            return
        try:
            q_chamado = "INSERT INTO chamados_suporte (empresa_id, assunto, categoria, prioridade, status) VALUES (%s, %s, %s, %s, 'ABERTO') RETURNING id;"
            res = execute_query(q_chamado, (empresa_id, txt_chamado_assunto.value.strip(), dd_chamado_cat.value, dd_chamado_prio.value), fetch_all=True, commit=True)
            if res:
                ch_id = res[0]['id']
                execute_query("INSERT INTO chamados_interacoes (chamado_id, remetente_tipo, mensagem) VALUES (%s, 'EMPRESA', %s);", (ch_id, txt_chamado_msg.value.strip()), commit=True)
                show_snack("Chamado aberto com sucesso!", is_error=False)
                txt_chamado_assunto.value = ""
                txt_chamado_msg.value = ""
                carregar_meus_chamados()
        except Exception as ex:
            show_snack(f"Erro ao abrir chamado: {ex}")

    def carregar_meus_chamados():
        list_meus_chamados.controls.clear()
        try:
            chams = execute_query("SELECT id, assunto, categoria, prioridade, status, data_criacao FROM chamados_suporte WHERE empresa_id = %s ORDER BY id DESC;", (empresa_id,), fetch_all=True) or []
            if not chams:
                list_meus_chamados.controls.append(ft.Text("Nenhum chamado aberto.", color="#94A3B8"))
            else:
                for ch in chams:
                    cid = ch['id']
                    st = str(ch['status']).upper()
                    inters = execute_query("SELECT remetente_tipo, mensagem FROM chamados_interacoes WHERE chamado_id = %s ORDER BY id ASC;", (cid,), fetch_all=True) or []
                    col_int = ft.Column(spacing=4)
                    for i in inters:
                        rem = "Suporte SaaS Master" if i['remetente_tipo'] == 'SUPER_ADMIN' else "Você"
                        bg_c = "#2A9D8F" if i['remetente_tipo'] == 'SUPER_ADMIN' else "#0F172A"
                        col_int.controls.append(
                            ft.Container(
                                bgcolor=bg_c, padding=8, border_radius=6,
                                content=ft.Column([
                                    ft.Text(rem, weight="bold", size=10, color="#94A3B8"),
                                    ft.Text(i['mensagem'], color="white", size=12)
                                ], spacing=2)
                            )
                        )

                    list_meus_chamados.controls.append(
                        ft.Container(
                            bgcolor="#1E293B", padding=12, border_radius=8,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"🎫 Chamado #{cid} — {ch['assunto']}", weight="bold", color="white", size=14),
                                    ft.Text(f"Status: {st}", color="#4CC9F0" if st == 'ABERTO' else ("#2A9D8F" if st == 'RESOLVIDO' else "#E76F51"), weight="bold", size=12)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Categoria: {ch.get('categoria')} | Prioridade: {ch.get('prioridade')}", size=11, color="#94A3B8"),
                                ft.Divider(color="#334155"),
                                col_int
                            ], spacing=6)
                        )
                    )
        except Exception as ex:
            list_meus_chamados.controls.append(ft.Text(f"Erro ao carregar chamados: {ex}", color="#E76F51"))
        page.update()

    def handle_copiar_link_staff(e):
        try:
            page.clipboard = staff_link
        except Exception:
            pass
        show_snack("Link de Cadastro do Staff copiado!", is_error=False)

    card_link_staff = ft.Container(
        bgcolor="#1E293B", padding=12, border_radius=8,
        content=ft.Column([
            ft.Text("🔗 Link de Convite para Cadastro de Staff:", weight="bold", size=13, color="white"),
            ft.ResponsiveRow([
                ft.TextField(value=staff_link, read_only=True, text_size=12, border_radius=8, col={"xs": 12, "sm": 8}),
                ft.ElevatedButton("Copiar Link 📋", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"), height=42, on_click=handle_copiar_link_staff, col={"xs": 12, "sm": 4})
            ], spacing=8)
        ], spacing=6)
    )

    # --- CONTROLE DE ABAS ---
    area_conteudo = ft.Container(expand=True)

    def set_aba(aba_nome):
        if aba_nome == "EVENTOS":
            area_conteudo.content = ft.Column([
                card_link_staff,
                ft.Divider(color="#334155"),
                ft.Text("1. Cadastrar Novo Evento", weight="bold", size=15, color="#4CC9F0"),
                txt_nome_evento, txt_local_evento,
                ft.ResponsiveRow([txt_data_inicio, txt_data_fim], spacing=10),
                ft.ResponsiveRow([txt_hora_inicio, txt_hora_fim], spacing=10),
                ft.ElevatedButton("Salvar Evento", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_criar_evento, width=380),
                ft.Divider(color="#334155"),
                ft.Text("2. Publicar Vaga no Evento", weight="bold", size=15, color="#4CC9F0"),
                dd_eventos_vagas, txt_funcao_vaga,
                ft.ResponsiveRow([txt_diaria_vaga, txt_qtd_vagas], spacing=10),
                ft.ElevatedButton("Publicar Vaga", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="white"), on_click=handle_criar_vaga, width=380)
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "CANDIDATOS":
            carregar_eventos_dropdowns()
            carregar_candidatos()
            area_conteudo.content = ft.Column([
                ft.Text("Aprovação de Staffs Inscritos", weight="bold", size=15, color="#4CC9F0"),
                dd_eventos_cand,
                ft.Divider(color="#334155"),
                list_candidatos
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "PAGAMENTOS":
            carregar_pagamentos_pendentes()
            area_conteudo.content = ft.Column([
                ft.Text("Pagamentos Pendentes", weight="bold", size=15, color="#4CC9F0"),
                txt_pix_lote_input,
                ft.ElevatedButton("Processar Baixa em Lote 📊", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"), on_click=handle_processar_pix_lote),
                ft.Divider(color="#334155"),
                list_pagamentos_pendentes
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "FINALIZADOS":
            carregar_pagamentos_finalizados()
            area_conteudo.content = ft.Column([
                ft.Text("Histórico de Pagamentos Finalizados", weight="bold", size=15, color="#2A9D8F"),
                list_pagamentos_finalizados
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "FINANCEIRO":
            carregar_financeiro()
            area_conteudo.content = ft.Column([
                ft.Row([
                    ft.Text("Dashboard Financeiro & DRE", weight="bold", size=15, color="#4CC9F0"),
                    ft.ElevatedButton("Exportar CSV 📊", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), height=35, on_click=handle_exportar_csv)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ResponsiveRow([
                    ft.Container(content=ft.Column([ft.Text("Faturamento", size=10, color="#94A3B8"), txt_fin_resumo_bruto]), bgcolor="#1E293B", padding=10, border_radius=6, col={"xs": 6, "sm": 3}),
                    ft.Container(content=ft.Column([ft.Text("Custos", size=10, color="#94A3B8"), txt_fin_resumo_despesa]), bgcolor="#1E293B", padding=10, border_radius=6, col={"xs": 6, "sm": 3}),
                    ft.Container(content=ft.Column([ft.Text("Impostos", size=10, color="#94A3B8"), txt_fin_resumo_imposto]), bgcolor="#1E293B", padding=10, border_radius=6, col={"xs": 6, "sm": 3}),
                    ft.Container(content=ft.Column([ft.Text("Lucro Líquido", size=10, color="#94A3B8"), txt_fin_resumo_liquido]), bgcolor="#1E293B", padding=10, border_radius=6, col={"xs": 6, "sm": 3}),
                ], spacing=8),
                lbl_margem_lucro, pb_lucratividade,
                ft.Divider(color="#334155"),
                ft.Text("Novo Lançamento", weight="bold", size=13, color="white"),
                dd_fin_tipo, txt_fin_desc,
                ft.ResponsiveRow([txt_fin_cat, txt_fin_valor, txt_fin_imposto], spacing=8),
                ft.ElevatedButton("Lançar no Financeiro", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="black"), on_click=handle_lancar_financeiro, width=380),
                ft.Divider(color="#334155"),
                list_financeiro
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "PROPOSTA":
            area_conteudo.content = ft.Column([
                ft.Text("Gerador de Proposta Comercial (PDF)", weight="bold", size=15, color="#4CC9F0"),
                txt_prop_cliente, txt_prop_cnpj, txt_prop_evento, txt_prop_descricao,
                ft.ResponsiveRow([txt_prop_qtd_staff, txt_prop_diaria_unit, txt_prop_dias], spacing=8),
                txt_prop_condicoes,
                ft.ElevatedButton("Gerar Proposta Comercial PDF 📄", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_gerar_proposta_pdf, width=380)
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "NF":
            carregar_notas_fiscais()
            area_conteudo.content = ft.Column([
                ft.Text("Emissor / Registro de Notas Fiscais", weight="bold", size=15, color="#4CC9F0"),
                txt_nf_tomador, txt_nf_cnpj, txt_nf_desc,
                ft.ResponsiveRow([txt_nf_valor, txt_nf_aliquota], spacing=10),
                ft.ElevatedButton("Emitir / Registrar NF", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_gerar_nf, width=380),
                ft.Divider(color="#334155"),
                list_notas_fiscais
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "PERFIL":
            carregar_dados_empresa_perfil()
            area_conteudo.content = ft.Column([
                ft.Text("Editar Perfil do Administrador", weight="bold", size=15, color="#4CC9F0"),
                txt_prof_nome, txt_prof_email, txt_prof_senha,
                ft.Divider(color="#334155"),
                ft.Text("Dados da Empresa (Inalteráveis pelo Admin):", size=12, color="#94A3B8"),
                txt_prof_razao, txt_prof_cnpj,
                ft.ElevatedButton("Salvar Alterações de Perfil", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_salvar_perfil, width=380)
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        elif aba_nome == "SUPORTE":
            carregar_meus_chamados()
            area_conteudo.content = ft.Column([
                ft.Text("Abrir Chamado / Ticket para Suporte SaaS", weight="bold", size=15, color="#4CC9F0"),
                txt_chamado_assunto,
                ft.ResponsiveRow([dd_chamado_cat, dd_chamado_prio], spacing=10),
                txt_chamado_msg,
                ft.ElevatedButton("Enviar Chamado ao Suporte 📩", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_abrir_chamado, width=380),
                ft.Divider(color="#334155"),
                ft.Text("Histórico de Chamados Enviados", weight="bold", size=14, color="white"),
                list_meus_chamados
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

        page.update()

    btn_aba_ev = ft.ElevatedButton("Eventos/Vagas", on_click=lambda _: set_aba("EVENTOS"), height=36)
    btn_aba_cand = ft.ElevatedButton("Aprovar Staff", on_click=lambda _: set_aba("CANDIDATOS"), height=36)
    btn_aba_pag = ft.ElevatedButton("Pagamentos", on_click=lambda _: set_aba("PAGAMENTOS"), height=36)
    btn_aba_fin_pag = ft.ElevatedButton("Finalizados ✅", on_click=lambda _: set_aba("FINALIZADOS"), height=36)
    btn_aba_fin = ft.ElevatedButton("Financeiro", on_click=lambda _: set_aba("FINANCEIRO"), height=36)
    btn_aba_prop = ft.ElevatedButton("Proposta PDF", on_click=lambda _: set_aba("PROPOSTA"), height=36)
    btn_aba_nf = ft.ElevatedButton("Emissor NF", on_click=lambda _: set_aba("NF"), height=36)
    btn_aba_prof = ft.ElevatedButton("Meu Perfil ⚙️", on_click=lambda _: set_aba("PERFIL"), height=36)
    btn_aba_sup = ft.ElevatedButton("Suporte SaaS 💬", on_click=lambda _: set_aba("SUPORTE"), height=36)

    carregar_eventos_dropdowns()
    set_aba("EVENTOS")

    return ft.Container(
        expand=True, bgcolor="#0B132B", padding=12,
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(f"Painel Empresa — {nome_admin}", size=18, weight="bold", color="white"),
                    ft.Text("Gestão da empresa e canal direto com o suporte", size=11, color="#94A3B8")
                ], expand=True),
                ft.IconButton(ft.Icons.LOGOUT, icon_color="#E76F51", tooltip="Sair da Conta", on_click=lambda e: on_logout() if on_logout else None)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([btn_aba_ev, btn_aba_cand, btn_aba_pag, btn_aba_fin_pag, btn_aba_fin, btn_aba_prop, btn_aba_nf, btn_aba_prof, btn_aba_sup], spacing=6, scroll=ft.ScrollMode.AUTO),
            ft.Divider(color="#334155", height=1),
            area_conteudo
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
    )