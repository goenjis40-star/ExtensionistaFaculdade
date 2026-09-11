"""
StatsCard — Componente reutilizável para exibição de estatísticas.
Exibe um título descritivo e um valor numérico grande.
"""

import customtkinter as ctk


class StatsCard(ctk.CTkFrame):
    """
    Card visual para exibir uma estatística chave.
    Uso: StatsCard(parent, "Peso Total (t)")
    """

    def __init__(self, master, title: str, value: str = "--", **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
        )
        self.title_label.grid(row=0, column=0, pady=(12, 2), padx=15, sticky="n")

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.value_label.grid(row=1, column=0, pady=(2, 12), padx=15, sticky="n")

    def set_value(self, value: str):
        """Atualiza o valor exibido no card."""
        self.value_label.configure(text=str(value))

    def set_title(self, title: str):
        """Atualiza o título do card."""
        self.title_label.configure(text=title)
