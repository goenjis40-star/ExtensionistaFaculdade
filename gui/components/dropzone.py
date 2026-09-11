"""
DropZone — Componente reutilizável para seleção de arquivos PDF.
Suporta drag-and-drop (via tkinterdnd2) com fallback gracioso para botão.
"""

import customtkinter as ctk


class DropZone(ctk.CTkFrame):
    """
    Área visual para arrastar e soltar arquivos PDF.
    Inclui fallback funcional via botão "Selecionar PDF" caso
    tkinterdnd2 não esteja instalado ou não funcione.
    """

    def __init__(self, master, on_file_selected, on_files_selected=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_file_selected = on_file_selected
        self.on_files_selected = on_files_selected
        self._dnd_available = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)

        self.icon_label = ctk.CTkLabel(
            self,
            text="📂",
            font=ctk.CTkFont(size=36),
        )
        self.icon_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5))

        self.label = ctk.CTkLabel(
            self,
            text="Arraste e solte o relatorio PDF aqui\nou clique no botao abaixo",
            font=ctk.CTkFont(size=14),
            justify="center",
        )
        self.label.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10))

        self.btn_select = ctk.CTkButton(
            self,
            text="📎 Selecionar PDF",
            command=self._browse_file,
            height=34,
            font=ctk.CTkFont(size=13),
        )
        self.btn_select.grid(row=2, column=0, padx=(20, 5), pady=(0, 15), sticky="ew")

        self.btn_select_multi = ctk.CTkButton(
            self,
            text="📁 Multiplos PDFs",
            command=self._browse_files,
            height=34,
            font=ctk.CTkFont(size=13),
            fg_color="#555555",
            hover_color="#444444",
        )
        self.btn_select_multi.grid(
            row=2, column=1, padx=(5, 20), pady=(0, 15), sticky="ew"
        )

        self._setup_dnd()

    def _setup_dnd(self):
        """Tenta registrar drag-and-drop. Falha silenciosa se indisponível."""
        try:
            from tkinterdnd2 import DND_FILES

            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
            self._dnd_available = True
        except Exception:
            # tkinterdnd2 não instalado ou master não suporta DnD
            self._dnd_available = False

    def _browse_file(self):
        """Abre diálogo de seleção de arquivo unico."""
        from tkinter import filedialog

        filepath = filedialog.askopenfilename(
            title="Selecione um relatorio PDF",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if filepath:
            self.on_file_selected(filepath)

    def _browse_files(self):
        """Abre dialogo de selecao de multiplos arquivos."""
        from tkinter import filedialog

        filepaths = filedialog.askopenfilenames(
            title="Selecione um ou mais relatorios PDF",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if filepaths and self.on_files_selected:
            self.on_files_selected(list(filepaths))

    def _on_drop(self, event):
        """Callback para evento de drop. Valida extensão .pdf."""
        filepath = event.data
        # tkinterdnd2 pode retornar caminhos entre chaves para nomes com espaços
        if filepath.startswith("{") and filepath.endswith("}"):
            filepath = filepath[1:-1]

        if filepath.lower().endswith(".pdf"):
            self.on_file_selected(filepath)

    @property
    def has_dnd(self) -> bool:
        """Retorna True se drag-and-drop está ativo."""
        return self._dnd_available
