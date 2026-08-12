import csv
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from services.financial_service import get_event_payroll

def export_payroll_csv(evento_id, evento_nome):
    """Gera um arquivo CSV com a folha de pagamento do evento para abrir no Excel."""
    records = get_event_payroll(evento_id)
    filename = f"Folha_Pagamento_{evento_nome.replace(' ', '_')}.csv"
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Colaborador', 'CPF', 'Funcao', 'Valor Diaria (R$)', 'Chave Pix'])

    for r in records:
        writer.writerow([
            r['staff_nome'],
            r['staff_cpf'] or 'N/A',
            r['funcao'],
            f"{r['valor_diaria']:.2f}",
            r['chave_pix'] or 'Não informada'
        ])

    return filename, output.getvalue()

def export_payroll_pdf(evento_id, evento_nome):
    """Gera um relatório em PDF formatado da folha de pagamento."""
    records = get_event_payroll(evento_id)
    filename = f"Relatorio_Financeiro_{evento_nome.replace(' ', '_')}.pdf"
    
    # Define o caminho temporário na pasta downloads do usuário ou pasta local
    filepath = os.path.join(os.path.expanduser('~'), 'Downloads', filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Título
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'))
    story.append(Paragraph(f"<b>Relatório Financeiro / Pix</b>", title_style))
    story.append(Paragraph(f"Evento: {evento_nome} — Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 15))

    # Tabela
    data = [['Colaborador', 'Função', 'Diária (R$)', 'Chave Pix']]
    total = 0.0

    for r in records:
        val = float(r['valor_diaria'])
        total += val
        data.append([
            r['staff_nome'],
            r['funcao'],
            f"R$ {val:.2f}",
            r['chave_pix'] or 'N/A'
        ])

    data.append(['TOTAL A PAGAR', '', f"R$ {total:.2f}", ''])

    t = Table(data, colWidths=[150, 120, 90, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F1F5F9')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))

    story.append(t)
    doc.build(story)
    return filepath
