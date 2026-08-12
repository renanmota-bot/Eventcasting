import flet as ft

# Palette - Event Casting Dark Premium
BG_DARK = "#090D16"         # Fundo principal profundo
SURFACE_DARK = "#131C2E"    # Surface dos cards
SURFACE_LIGHT = "#1E293B"   # Hover/Cards secundários
PRIMARY = "#F59E0B"         # Gold/Amber de destaque
PRIMARY_HOVER = "#D97706"
SUCCESS = "#10B981"         # Verde de aprovação/financeiro
ERROR = "#EF4444"           # Vermelho de recusa/alerta
INFO = "#3B82F6"            # Azul de status
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"
BORDER_COLOR = "#334155"

def apply_app_theme(page: ft.Page):
    """Aplica as configurações globais de tema e responsividade."""
    page.title = "Event Casting — Gestão de Equipes e Eventos"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_DARK
    page.padding = 0
    page.fonts = {
        "Inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf",
        "Inter-Bold": "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf"
    }
    page.theme = ft.Theme(font_family="Inter")

def create_glass_card(controls, padding=16, width=None, expand=False):
    """Cria um card com efeito escuro profissional e bordas suaves."""
    return ft.Container(
        content=ft.Column(controls=controls, spacing=12),
        bgcolor=SURFACE_DARK,
        padding=padding,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
        width=width,
        expand=expand
    )
