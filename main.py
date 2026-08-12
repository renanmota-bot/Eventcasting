import flet as ft

# Imports das Views
from views.login_view import LoginView
from views.register_view import RegisterView
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

    current_user = [None]

    def navigate_to(route_name, empresa_id=1):
        page.controls.clear()

        if route_name == "LOGIN":
            current_user[0] = None
            page.add(
                LoginView(
                    page,
                    on_login_success=handle_login_success,
                    on_navigate_register=lambda: navigate_to("REGISTER")
                )
            )

        elif route_name == "REGISTER":
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
                try:
                    page.add(
                        AdminDashboardView(
                            page,
                            user=current_user[0],
                            on_logout=handle_logout,
                            on_navigate=navigate_to
                        )
                    )
                except TypeError:
                    page.add(
                        AdminDashboardView(
                            page,
                            user=current_user[0],
                            on_logout=handle_logout
                        )
                    )
            else:
                show_snack("Tela de Admin não encontrada no projeto.")

        elif route_name == "STAFF":
            if StaffDashboardView:
                try:
                    page.add(
                        StaffDashboardView(
                            page,
                            user=current_user[0],
                            on_logout=handle_logout,
                            on_navigate=navigate_to
                        )
                    )
                except TypeError:
                    page.add(
                        StaffDashboardView(
                            page,
                            user=current_user[0],
                            on_navigate=navigate_to
                        )
                    )
            else:
                show_snack("Tela de Staff não encontrada no projeto.")

        page.update()

    def handle_login_success(user):
        current_user[0] = user
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
        
        show_snack(f"Sessão alterada para: {target_user.get('nome')} ({perfil})", is_error=False)

        if perfil == "ADMIN":
            navigate_to("ADMIN")
        elif perfil == "SUPER_ADMIN":
            navigate_to("SUPER_ADMIN")
        else:
            navigate_to("STAFF")

    def handle_logout():
        current_user[0] = None
        navigate_to("LOGIN")

    def show_snack(msg, is_error=True):
        snack = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor="#E76F51" if is_error else "#2A9D8F"
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # Captura parâmetro de convite de empresa na URL (?empresa=ID)
    empresa_link_id = 1
    if page.route and "empresa=" in page.route:
        try:
            empresa_link_id = int(page.route.split("empresa=")[1].split("&")[0])
        except Exception:
            empresa_link_id = 1

    if "register" in page.route:
        navigate_to("REGISTER", empresa_id=empresa_link_id)
    else:
        navigate_to("LOGIN")

if __name__ == "__main__":
    ft.app(target=main)