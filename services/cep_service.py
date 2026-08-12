import urllib.request
import json

def fetch_address_by_cep(cep: str):
    """Busca dados de endereço pelo CEP usando a API pública do ViaCEP."""
    cep_clean = "".join(filter(str.isdigit, cep or ""))
    if len(cep_clean) != 8:
        return None
    try:
        url = f"https_viacep_com_br_ws_{cep_clean}_json_".replace("_", "/")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if "erro" in data:
                return None
            return {
                "logradouro": data.get("logradouro", ""),
                "bairro": data.get("bairro", ""),
                "cidade": data.get("localidade", ""),
                "uf": data.get("uf", "")
            }
    except Exception:
        return None
