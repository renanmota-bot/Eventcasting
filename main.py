import flet as ft
from views.login_view import LoginView
from views.register_view import RegisterView
from views.register_company_view import RegisterCompanyView
from views.admin.dashboard import AdminDashboardView
from views.staff.dashboard import StaffDashboardView
from views.profile_view import ProfileView
from views.checkout_view import CheckoutView
from views.super_admin_view import SuperAdminDashboardView

def main(page: ft.Page):
    page.title = "Event Casting — Gestão de Equipes e Eventos"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B132B"
    page.padding = 0

    current_user = [None]

    def navigate_to(route_name, target_empresa_id=1):
        page.controls.clear()

        if route_name == "LOGIN":
            page.add(LoginView(
                page, 
                on_login_success=handle_login_success, 
                on_navigate_register=lambda: navigate_to("REGISTER_COMPANY")
            ))
        elif route_name == "REGISTER_COMPANY":
            page.add(RegisterCompanyView(
                page, 
                on_back=lambda: navigate_to("LOGIN"),
                on_registered_success=handle_company_created
            ))
        elif route_name == "REGISTER_STAFF":
            page.add(RegisterView(
                page, 
                on_back=lambda: navigate_to("LOGIN"),
                default_empresa_id=target_empresa_id
            ))
        elif route_name == "SUPER_ADMIN":
            page.add(SuperAdminDashboardView(
                page,
                user=current_user[0],
                on_logout=handle_logout
            ))
        elif route_name == "ADMIN":
            page.add(AdminDashboardView(
                page, 
                user=current_user[0], 
                on_navigate=navigate_to, 
                on_logout=handle_logout
            ))
        elif route_name == "STAFF":
            page.add(StaffDashboardView(
                page, 
                user=current_user[0], 
                on_navigate=navigate_to, 
                on_logout=handle_logout
            ))
        elif route_name == "PROFILE":
            page.add(ProfileView(
                page, 
                user=current_user[0], 
                on_back=lambda: navigate_to("STAFF")
            ))
        elif route_name == "CHECKOUT":
            page.add(CheckoutView(
                page,
                user=current_user[0],
                on_success=lambda: navigate_to("ADMIN")
            ))
        page.update()

    def handle_company_created(user_admin_data):
        current_user[0] = user_admin_data
        navigate_to("CHECKOUT")

    def handle_login_success(user_data):
        current_user[0] = user_data
        perfil = user_data.get('perfil')

        if perfil == 'SUPER_ADMIN':
            navigate_to("SUPER_ADMIN")
        elif perfil == 'ADMIN':
            navigate_to("ADMIN")
        else:
            navigate_to("STAFF")

    def handle_logout():
        current_user[0] = None
        navigate_to("LOGIN")

    navigate_to("LOGIN")

if __name__ == "__main__":
    ft.app(target=main)