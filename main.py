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
        # Salva a sessão permanentemente
        page.client_storage.set("user_session", user)
        
        perfil = user.get("perfil", "STAFF").upper()
        if perfil == "SUPER_ADMIN":
            navigate_to("SUPER_ADMIN")
        elif perfil == "ADMIN":
            navigate_to("ADMIN")
        else:
            navigate_to("STAFF")

    def handle_logout():
        current_user[0] = None
        # Limpa a sessão salva ao clicar em Sair
        if page.client_storage.contains("user_session"):
            page.client_storage.remove("user_session")
        navigate_to("LOGIN")

    # --- VERIFICAÇÃO DE SESSÃO AUTOMÁTICA ---
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
        # Checa se o usuário já tem login salvo no dispositivo
        saved_user = page.client_storage.get("user_session")
        if saved_user:
            handle_login_success(saved_user)
        else:
            navigate_to("LOGIN")