import flet as ft

# Imports das Views
from views.login_view import LoginView
from views.register_view import RegisterView  # Cadastro de Staff (via link de convite)
from views.register_company_view import RegisterCompanyView  # Cadastro de Empresa / Produtora
from views.super_admin_view import SuperAdminDashboardView

# Tenta importar os outros dashboards
try:
    from views.admin.dashboard import AdminDashboardView
except ImportError:
    try:
        from views.admin_view import AdminDashboardView
    except ImportError:
        AdminDashboardView = None

try:
    from views.staff.dashboard import StaffDashboardView
except ImportError:
    try:
        from views.staff_view import StaffDashboardView
    except ImportError:
        StaffDashboardView = None

def main(page: ft.Page):
    page.title = "Event Casting — Gestão de Equipes e Eventos"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.AUTO

    current_user = [None]

    def navigate_to(route_name, empresa_id=1):
        page.controls.clear()

        if route_name == "LOGIN":
            current_user[0] = None
            page.add(
                LoginView(
                    page,
                    on_login_success=handle_login_success,
                    on_navigate_register=lambda: navigate_to("REGISTER_COMPANY")
                )
            )

        elif route_name == "REGISTER_COMPANY":
            # Abre o cadastro de Empresa/Produtora para pagamento
            page.add(
                RegisterCompanyView(
                    page,
                    on_back=lambda: navigate_to("LOGIN"),
                    on_registered_success=handle_login_success
                )
            )

        elif route_name == "REGISTER_STAFF":
            # Abre o cadastro do Staff vindo do link com ID da empresa
            page.add(
                RegisterView(
                    page,
                    on_back=lambda: navigate_to("LOGIN"),
                    default_empresa_id=empresa_id
                )
            )

        elif route_name == "SUPER_ADMIN":
            page.add(
                SuperAdminDashboardView(
                    page,
                    user=current_user[0],
                    on_logout=handle_logout,
                    on_ghost_login=handle_ghost_login
                )
            )

        elif route_name == "ADMIN":
            if AdminDashboardView:
                page.add(
                    AdminDashboardView(
                        page,
                        user=current_user[0],
                        on_logout=handle_logout,
                        on_navigate=navigate_to
                    )
                )

        elif route_name == "STAFF":
            if StaffDashboardView:
                page.add(
                    StaffDashboardView(
                        page,
                        user=current_user[0],
                        on_logout=handle_logout,
                        on_navigate=navigate_to
                    )
                )

        page.update()

    def handle_login_success(user):
        current_user[0] = user
        page.client_storage.set("user_session", user)
        
        perfil = user.get("perfil", "STAFF").upper()
        if perfil == "SUPER_ADMIN":
            navigate_to("SUPER_ADMIN")
        elif perfil == "ADMIN":
            navigate_to("ADMIN")
        else:
            navigate_to("STAFF")

    def handle_ghost_login(target_user):
        current_user[0] = target_user
        perfil = target_user.get("perfil", "ADMIN").upper()
        if perfil == "ADMIN":
            navigate_to("ADMIN")
        elif perfil == "SUPER_ADMIN":
            navigate_to("SUPER_ADMIN")
        else:
            navigate_to("STAFF")

    def handle_logout():
        current_user[0] = None
        if page.client_storage.contains("user_session"):
            page.client_storage.remove("user_session")
        navigate_to("LOGIN")

    # --- CONTROLE DE ROTAS ---
    empresa_link_id = 1
    
    # Se a URL contiver 'empresa=', entende que é um convite de Staff
    if page.route and "empresa=" in page.route:
        try:
            empresa_link_id = int(page.route.split("empresa=")[1].split("&")[0])
        except Exception:
            empresa_link_id = 1
        navigate_to("REGISTER_STAFF", empresa_id=empresa_link_id)
    else:
        # Checa login salvo no dispositivo
        saved_user = page.client_storage.get("user_session")
        if saved_user:
            handle_login_success(saved_user)
        else:
            navigate_to("LOGIN")

if __name__ == "__main__":
    ft.app(target=main)