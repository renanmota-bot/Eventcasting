def date_to_br(date_str: str) -> str:
    """Converte 'AAAA-MM-DD' para 'DD/MM/AAAA' para exibição."""
    if not date_str:
        return ""
    if "-" in date_str:
        parts = date_str.split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            return f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0]}"
    return date_str

def date_to_iso(date_str: str) -> str:
    """Converte 'DD/MM/AAAA' para 'AAAA-MM-DD' antes de salvar na base de dados."""
    if not date_str:
        return ""
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3 and len(parts[2]) == 4:
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return date_str
