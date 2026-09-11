"""
EcoMetric 2.0 — Interface Gráfica Desktop Profissional.
Construída com CustomTkinter. Arquitetura desacoplada do core.

Uso:
    python -m gui.app
    ou: python gui/app.py
"""

import os
import sys
import queue
import threading
import logging
import time

# --- sys.path setup (compatível com PyInstaller e execução direta) ---
_GUI_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_GUI_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from tkinter import filedialog, messagebox
import customtkinter as ctk

# Tentativa de importar TkinterDnD para suporte a arrastar-e-soltar.
# Se não estiver instalado, o app funciona normalmente via botão de seleção.
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES

    class BaseWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)

    HAS_DND = True
except ImportError:

    class BaseWindow(ctk.CTk):
        pass

    HAS_DND = False

# Imports internos da GUI (sem dependência circular)
from gui.theme.manager import ThemeManager
from gui.components.dropzone import DropZone
from gui.components.stats_card import StatsCard
from gui.handlers.log_handler import QueueLogHandler

# Imports do core — desacoplados, usados apenas via facade
from core.parsers import processar_relatorio_pdf
from core.parsers.detector import detectar_modelo_pdf
from core.constants import MODELO_CATAFACIL, MODELO_ANTIGO, MODELO_CONSOLIDADO
from core.exportador import exportar_para_excel
from core.consolidacao import consolidar_multiplos_pdfs, detectar_periodo_consolidado
from core.insights import gerar_insights
from reports.pdf_generator import gerar_relatorio_pdf, gerar_relatorio_anual


class App(BaseWindow):
    """Janela principal da aplicação EcoMetric 2.0."""

    def __init__(self):
        super().__init__()

        self.title("EcoMetric 2.0 — Conversor de Relatórios Ambientais")
        self.geometry("1050x680")
        self.minsize(850, 550)

        ThemeManager.initialize()

        self.current_pdf_path = None
        self.current_pdf_paths = []
        self.modelo_detectado = None
        self.periodo_consolidado = None
        self.df_consolidado = None
        self.df_bruto = None
        self.df_mensal = None
        self.meta_consolidado = None
        self.insights = None
        self.tempo_execucao = 0.0

        self.log_queue = queue.Queue()
        self._setup_logging()

        self._build_ui()
        self._poll_log_queue()

    # =====================================================================
    # LOGGING
    # =====================================================================
    def _setup_logging(self):
        """Configura o handler de logs para capturar mensagens do core na GUI."""
        core_logger = logging.getLogger("EcoMetric")
        core_logger.setLevel(logging.DEBUG)
        core_logger.propagate = False

        for handler in core_logger.handlers[:]:
            core_logger.removeHandler(handler)

        gui_handler = QueueLogHandler(self.log_queue)
        gui_handler.setLevel(logging.DEBUG)
        core_logger.addHandler(gui_handler)

        dir_log = os.path.join(
            os.getenv("APPDATA", os.path.expanduser("~")), "EcoMetric", "logs"
        )
        os.makedirs(dir_log, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(dir_log, "ecometric.log"),
            maxBytes=1_048_576,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        core_logger.addHandler(file_handler)

        core_logger.info("Sistema EcoMetric 2.0 iniciado.")
        if HAS_DND:
            core_logger.info("Arrastar e Soltar (Drag & Drop) ativado.")
        else:
            core_logger.info("tkinterdnd2 não encontrado — use o botão Selecionar PDF.")

    def _log(self, msg: str, level: str = "info"):
        """Atalho para emitir log no logger do core."""
        logger = logging.getLogger("EcoMetric")
        getattr(logger, level, logger.info)(msg)

    # =====================================================================
    # UI BUILD
    # =====================================================================
    def _build_ui(self):
        """Constrói todo o layout da interface."""
        self.grid_columnconfigure(0, weight=1)  # Painel principal
        self.grid_columnconfigure(1, weight=0)  # Sidebar
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_panel()

    def _build_sidebar(self):
        """Constrói a sidebar com logo, switch de tema e painel de logs."""
        self.sidebar = ctk.CTkFrame(self, width=270, corner_radius=0)
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.grid_rowconfigure(3, weight=1)  # Log expande

        # Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="♻ EcoMetric 2.0",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        self.subtitle = ctk.CTkLabel(
            self.sidebar,
            text="Conversor de Relatórios Ambientais",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        self.subtitle.grid(row=1, column=0, padx=20, pady=(0, 10))

        # Theme Toggle
        self.theme_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Modo Escuro",
            command=ThemeManager.toggle_theme,
        )
        self.theme_switch.grid(row=2, column=0, padx=20, pady=10)
        if ThemeManager.get_current_mode() == "Dark":
            self.theme_switch.select()

        # Log Panel
        self.log_label = ctk.CTkLabel(
            self.sidebar,
            text="Log de Execução",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.log_label.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="nw")

        self.log_textbox = ctk.CTkTextbox(
            self.sidebar,
            width=250,
            font=ctk.CTkFont(family="Consolas", size=10),
            wrap="word",
        )
        self.log_textbox.grid(row=4, column=0, padx=10, pady=(5, 10), sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        self.log_textbox.configure(state="disabled")

    def _build_main_panel(self):
        """Constrói o painel principal com drop zone, botões e stats."""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)

        # --- Drop Zone ---
        self.dropzone = DropZone(
            self.main_frame,
            on_file_selected=self._on_file_selected,
            on_files_selected=self._on_files_selected,
        )
        self.dropzone.grid(
            row=0, column=0, columnspan=3, sticky="new", pady=(0, 15), ipady=30
        )

        # --- Arquivo selecionado ---
        self.file_label = ctk.CTkLabel(
            self.main_frame, text="Nenhum arquivo selecionado", text_color="gray"
        )
        self.file_label.grid(row=1, column=0, columnspan=3, pady=(0, 5))

        # --- Modelo detectado ---
        self.model_label = ctk.CTkLabel(
            self.main_frame, text="", font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.model_label.grid(row=2, column=0, columnspan=3, pady=(0, 10))

        # --- Barra de Progresso ---
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, mode="indeterminate")
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        self.progress_bar.set(0)

        # --- Botão Processar ---
        self.btn_process = ctk.CTkButton(
            self.main_frame,
            text="⚙ Processar Relatório",
            command=self._start_processing,
            state="disabled",
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.btn_process.grid(row=4, column=0, columnspan=3, pady=(0, 25))

        # --- Cards de Estatísticas ---
        self.stats_peso = StatsCard(self.main_frame, "Peso Total (t)")
        self.stats_peso.grid(row=5, column=0, padx=5, sticky="nsew")

        self.stats_co2 = StatsCard(self.main_frame, "CO2 Evitado (t CO₂e)")
        self.stats_co2.grid(row=5, column=1, padx=5, sticky="nsew")

        self.stats_itens = StatsCard(self.main_frame, "Categorias")
        self.stats_itens.grid(row=5, column=2, padx=5, sticky="nsew")

        # --- Frame de Exportação ---
        self.export_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.export_frame.grid(row=6, column=0, columnspan=3, pady=(25, 0), sticky="ew")
        self.export_frame.grid_columnconfigure(0, weight=1)
        self.export_frame.grid_columnconfigure(1, weight=1)

        self.btn_export = ctk.CTkButton(
            self.export_frame,
            text="📊 Exportar para Excel",
            command=self._export_excel,
            state="disabled",
            height=38,
            fg_color="#2ea043",
            hover_color="#238636",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_export.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_export_pdf = ctk.CTkButton(
            self.export_frame,
            text="📄 Exportar Relatório PDF",
            command=self._export_pdf,
            state="disabled",
            height=38,
            fg_color="#1a7fb8",
            hover_color="#166a9a",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_export_pdf.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    # =====================================================================
    # LOG POLLING
    # =====================================================================
    def _poll_log_queue(self):
        """Lê mensagens da fila thread-safe e insere no textbox da GUI."""
        while True:
            try:
                msg = self.log_queue.get_nowait()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", msg + "\n")
                self.log_textbox.see("end")
                self.log_textbox.configure(state="disabled")
            except queue.Empty:
                break
        self.after(100, self._poll_log_queue)

    # =====================================================================
    # FILE SELECTION
    # =====================================================================
    def _on_file_selected(self, filepath: str):
        """Callback chamado quando um PDF e selecionado (via drop ou botao)."""
        self.current_pdf_path = filepath
        self.current_pdf_paths = [filepath]
        self.periodo_consolidado = None
        filename = os.path.basename(filepath)
        self.file_label.configure(text=f"📄 {filename}")
        self.btn_process.configure(state="normal")
        self.btn_export.configure(state="disabled")
        self.btn_export_pdf.configure(state="disabled")

        self.stats_peso.set_value("--")
        self.stats_co2.set_value("--")
        self.stats_itens.set_value("--")
        self.df_consolidado = None
        self.df_bruto = None
        self.df_mensal = None
        self.meta_consolidado = None
        self.modelo_detectado = None

        try:
            modelo = detectar_modelo_pdf(filepath)
            self.modelo_detectado = modelo
            if modelo == MODELO_CATAFACIL:
                label_modelo = "CataFácil"
            elif modelo == MODELO_ANTIGO:
                label_modelo = "Antigo"
            else:
                label_modelo = modelo.upper()
            self.model_label.configure(text=f"Modelo detectado: {label_modelo}")
            self._log(f"Arquivo selecionado: {filename} (modelo: {label_modelo})")
        except Exception:
            self.model_label.configure(text="Modelo: não detectado")
            self._log(
                f"Arquivo selecionado: {filename} (modelo não detectável)", "warning"
            )

    def _on_files_selected(self, filepaths: list):
        """Callback chamado quando multiplos PDFs sao selecionados."""
        if not filepaths:
            return
        self.current_pdf_paths = list(filepaths)
        self.current_pdf_path = filepaths[0]
        self.periodo_consolidado = None

        count = len(filepaths)
        self.file_label.configure(text=f"📁 {count} arquivos selecionados")
        self.model_label.configure(text="Modelo detectado: CONSOLIDADO")
        self.modelo_detectado = MODELO_CONSOLIDADO
        self.btn_process.configure(state="normal")
        self.btn_export.configure(state="disabled")
        self.btn_export_pdf.configure(state="disabled")

        self.stats_peso.set_value("--")
        self.stats_co2.set_value("--")
        self.stats_itens.set_value("--")
        self.df_consolidado = None
        self.df_bruto = None
        self.df_mensal = None
        self.meta_consolidado = None
        self.modelo_detectado = None

        self._log(f"{count} arquivos selecionados para consolidacao")
        for fp in filepaths:
            self._log(f"  {os.path.basename(fp)}")

    # =====================================================================
    # PROCESSING (THREADED)
    # =====================================================================
    def _start_processing(self):
        """Inicia o processamento do PDF em thread separada."""
        if not self.current_pdf_path:
            return

        self.btn_process.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        self.btn_export_pdf.configure(state="disabled")
        self.progress_bar.start()

        thread = threading.Thread(target=self._process_worker, daemon=True)
        thread.start()

    def _process_worker(self):
        """Worker que roda em background. Nunca toca na GUI diretamente."""
        try:
            self._log("Iniciando processamento do pipeline...")
            t0 = time.perf_counter()

            if len(self.current_pdf_paths) > 1:
                self._log(f"Modo consolidacao: {len(self.current_pdf_paths)} PDFs")
                df_cons, df_bruto, meta = consolidar_multiplos_pdfs(
                    self.current_pdf_paths
                )
                self.periodo_consolidado = detectar_periodo_consolidado(
                    meta["info_list"]
                )
                self._log(f"Periodo detectado: {self.periodo_consolidado}")
                self.modelo_detectado = meta["modelo"]
                self.df_mensal = meta.get("df_mensal")
                self.meta_consolidado = meta
                auditoria = meta.get("auditoria_periodo", {})
                avisos = auditoria.get("avisos", [])
                if avisos:
                    self._log(
                        f"Auditoria: {len(avisos)} aviso(s) detectado(s)", "warning"
                    )
                    for a in avisos:
                        self._log(f"  {a}", "warning")
                for item in meta["info_list"]:
                    if item["status"] != "OK":
                        self._log(f"  {item['arquivo']}: {item['status']}", "warning")
            else:
                df_cons, df_bruto = processar_relatorio_pdf(self.current_pdf_path)

            self.tempo_execucao = time.perf_counter() - t0
            self.df_consolidado = df_cons
            self.df_bruto = df_bruto
            self.insights = gerar_insights(df_cons, df_bruto, self.df_mensal)

            self._log(f"Pipeline concluido em {self.tempo_execucao:.3f}s.")
            self.after(0, self._on_process_success)

        except Exception as e:
            self._log(f"ERRO no processamento: {e}", "error")
            self.after(0, lambda err=e: self._on_process_error(err))

    def _on_process_success(self):
        """Callback na thread da GUI após sucesso do processamento."""
        self.progress_bar.stop()
        self.progress_bar.set(1)
        self.btn_process.configure(state="normal")
        self.btn_export.configure(state="normal")
        self.btn_export_pdf.configure(state="normal")

        if self.meta_consolidado:
            auditoria = self.meta_consolidado.get("auditoria_periodo", {})
            avisos = auditoria.get("avisos", [])
            if avisos:
                msg = f"Foram detectados {len(avisos)} aviso(s) na consolidacao:\n\n"
                msg += "\n".join(f"  \u2022 {a}" for a in avisos[:5])
                if len(avisos) > 5:
                    msg += f"\n  ... e mais {len(avisos) - 5}"
                self.after(
                    100,
                    lambda: messagebox.showwarning("Auditoria da Consolidacao", msg),
                )

        if self.df_consolidado is not None and not self.df_consolidado.empty:
            peso_total = self.df_consolidado["Peso Total (t)"].sum()
            co2_total = self.df_consolidado["CO2 Evitado (t CO2e)"].sum()
            qtde_categorias = len(self.df_consolidado)

            self.stats_peso.set_value(f"{peso_total:.4f}")
            self.stats_co2.set_value(f"{co2_total:.4f}")
            self.stats_itens.set_value(str(qtde_categorias))

            self._log(
                f"Peso Total: {peso_total:.4f} t | CO2: {co2_total:.4f} t CO2e | Categorias: {qtde_categorias}"
            )
            self._log("Processamento concluído com sucesso ✓")
        else:
            self._log("Nenhum dado consolidado retornado.", "warning")

    def _on_process_error(self, error: Exception):
        """Callback na thread da GUI após erro no processamento."""
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.btn_process.configure(state="normal")
        messagebox.showerror(
            "Erro de Processamento",
            f"Ocorreu um erro ao processar o PDF:\n\n{error}",
        )

    # =====================================================================
    # EXPORT EXCEL
    # =====================================================================
    def _export_excel(self):
        """Exporta os dados processados para um arquivo Excel multi-abas."""
        if self.df_consolidado is None or self.df_bruto is None:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")],
            title="Salvar Planilha Excel",
            initialfile="EcoMetric_Resultado.xlsx",
        )

        if not save_path:
            return

        try:
            self._log(f"Exportando para {os.path.basename(save_path)}...")

            exportar_para_excel(
                self.df_consolidado,
                self.df_bruto,
                self.current_pdf_path,
                self.modelo_detectado or "desconhecido",
                self.tempo_execucao,
                save_path,
                self.df_mensal,
                (
                    self.meta_consolidado.get("auditoria_periodo")
                    if self.meta_consolidado
                    else None
                ),
                self.insights,
            )
            self._log("Exportação concluída com sucesso ✓")
            messagebox.showinfo(
                "Sucesso", f"Planilha exportada com sucesso!\n\n{save_path}"
            )
        except Exception as e:
            self._log(f"ERRO na exportação: {e}", "error")
            messagebox.showerror("Erro de Exportação", f"Falha ao exportar:\n\n{e}")

    # =====================================================================
    # EXPORT PDF
    # =====================================================================
    def _export_pdf(self):
        """Exporta os dados processados para um relatorio PDF."""
        if self.df_consolidado is None or self.df_bruto is None:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            title="Salvar Relatorio PDF",
            initialfile="EcoMetric_Relatorio.pdf",
        )

        if not save_path:
            return

        try:
            self._log(f"Exportando relatorio PDF para {os.path.basename(save_path)}...")

            if (
                self.modelo_detectado == MODELO_CONSOLIDADO
                and self.df_mensal is not None
                and self.meta_consolidado is not None
            ):
                gerar_relatorio_anual(
                    self.df_consolidado,
                    self.df_mensal,
                    self.meta_consolidado,
                    save_path,
                    df_bruto=self.df_bruto,
                )
            else:
                gerar_relatorio_pdf(
                    self.df_consolidado,
                    self.df_bruto,
                    save_path,
                    self.modelo_detectado or "desconhecido",
                    self.current_pdf_path,
                    self.tempo_execucao,
                )
            self._log("Relatorio PDF gerado com sucesso")
            messagebox.showinfo(
                "Sucesso", f"Relatorio PDF exportado com sucesso!\n\n{save_path}"
            )
        except Exception as e:
            self._log(f"ERRO na exportacao PDF: {e}", "error")
            messagebox.showerror("Erro de Exportacao", f"Falha ao gerar PDF:\n\n{e}")


# =========================================================================
# ENTRY POINT
# =========================================================================
def run():
    """Ponto de entrada para iniciar a GUI."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
