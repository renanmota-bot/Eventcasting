# Correção: usa 'label' em vez de 'text'
    tabs_painel = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                label="Eventos & Vagas",
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text("1. Cadastrar Novo Evento", weight="bold", size=15, color="#4CC9F0"),
                        txt_nome_evento,
                        txt_local_evento,
                        ft.Row([txt_data_inicio, txt_data_fim], spacing=10),
                        ft.ElevatedButton("Criar Evento", style=ft.ButtonStyle(bgcolor="#2A9D8F", color="white"), on_click=handle_criar_evento, width=380),
                        ft.Divider(color="#334155"),
                        ft.Text("2. Publicar Vaga no Evento", weight="bold", size=15, color="#4CC9F0"),
                        dd_eventos,
                        txt_funcao,
                        ft.Row([txt_valor_diaria, txt_qtd_vagas], spacing=10),
                        ft.ElevatedButton("Publicar Vaga", style=ft.ButtonStyle(bgcolor="#4CC9F0", color="white"), on_click=handle_criar_vaga, width=380),
                    ], spacing=10, scroll=ft.ScrollMode.AUTO)
                )
            ),
            ft.Tab(
                label="Meus Eventos",
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text("Eventos Cadastrados", weight="bold", size=15, color="white"),
                        list_eventos
                    ], spacing=10, scroll=ft.ScrollMode.AUTO)
                )
            )
        ],
        expand=True
    )