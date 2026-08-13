import flet as ft

from views.login_view import LoginView
from views.register_view import RegisterView
from views.register_company_view import RegisterCompanyView
from views.super_admin_view import SuperAdminDashboardView
from views.admin.dashboard import AdminDashboardView
from views.staff.dashboard import StaffDashboardView


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
                    on_navigate_register=lambda: navigate_to("REGISTER_COMPANY")
                )
            )

        elif route_name == "REGISTER_COMPANY":
            page.add(
                RegisterCompanyView(
                    page,
                    on_back=lambda: navigate_to("LOGIN"),
                    on_registered_success=handle_login_success
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
            page.add(
                AdminDashboardView(
                    page,
                    user=current_user[0],
                    on_logout=handle_logout,
                    on_navigate=navigate_to
                )
            )

        elif route_name == "STAFF":
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
        perfil = str(user.get("perfil", "STAFF")).upper()
        if perfil == "SUPER_ADMIN":
            navigate_to("SUPER_ADMIN")
        elif perfil == "ADMIN":
            navigate_to("ADMIN")
        else:
            navigate_to("STAFF")

    def handle_ghost_login(target_user):
        current_user[0] = target_user
        perfil = str(target_user.get("perfil", "ADMIN")).upper()
        if perfil == "ADMIN":
            navigate_to("ADMIN")
        elif perfil == "SUPER_ADMIN":
            navigate_to("SUPER_ADMIN")
        else:
            navigate_to("STAFF")

    def handle_logout():
        current_user[0] = None
        navigate_to("LOGIN")

    navigate_to("LOGIN")


if __name__ == "__main__":
    ft.app(target=main)