import csv
import io

def generate_financial_csv(lancamentos: list) -> str:
    """Gera uma string CSV formatada a partir da lista de lançamentos financeiros."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Cabeçalho do CSV
    writer.writerow([
        'ID', 'Tipo', 'Descrição', 'Categoria', 
        'Valor (R$)', '% Imposto', 'Imposto (R$)', 'Data Lançamento'
    ])
    
    for l in lancamentos:
        val = float(l.get('valor', 0))
        imp_perc = float(l.get('imposto_percentual', 0))
        imp_val = val * (imp_perc / 100.0) if l.get('tipo') == 'RECEITA' else 0.0
        
        writer.writerow([
            l.get('id', ''),
            l.get('tipo', ''),
            l.get('descricao', ''),
            l.get('categoria', ''),
            f"{val:.2f}".replace('.', ','),
            f"{imp_perc:.2f}".replace('.', ','),
            f"{imp_val:.2f}".replace('.', ','),
            str(l.get('data_lancamento', ''))
        ])
        
    return output.getvalue()