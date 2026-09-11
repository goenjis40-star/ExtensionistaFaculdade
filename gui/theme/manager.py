"""
Gerenciador de tema Dark/Light com persistência.
Salva a preferência do usuário em ~/.ecometric_gui_config.json.
"""

import json
import os
import customtkinter as ctk

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".ecometric_gui_config.json")


def _load_config() -> dict:
    """Carrega configuração persistente do disco."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_config(data: dict):
    """Salva configuração persistente no disco."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass  # Falha silenciosa — não impede uso do app


class ThemeManager:
    """
    Gerenciador de tema para a aplicação EcoMetric 2.0.
    Persiste a escolha do usuário entre sessões.
    """

    @staticmethod
    def initialize():
        """Inicializa o CustomTkinter com o tema salvo (ou 'Dark' como padrão)."""
        cfg = _load_config()
        theme = cfg.get("theme", "Dark")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("green")

    @staticmethod
    def toggle_theme():
        """Alterna entre Dark e Light e persiste a escolha."""
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        cfg = _load_config()
        cfg["theme"] = new_mode
        _save_config(cfg)

    @staticmethod
    def get_current_mode() -> str:
        """Retorna o modo atual ('Dark' ou 'Light')."""
        return ctk.get_appearance_mode()
