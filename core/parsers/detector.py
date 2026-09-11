import pdfplumber
from typing import Optional

from core.constants import MODELO_CATAFACIL, MODELO_ANTIGO

MARCADORES_CATAFACIL = [
    "MATERIAIS DE UNIDADE",
    "UNIDADE=>KG",
    "MATERIAL UNIDADE QTDE",
    "VENDA DE MATERIAIS",
    "CATAFÁCIL",
    "CATÁFACIL",
]


def detectar_modelo_pdf(caminho_arquivo: Optional[str]) -> str:
    """
    Detecta o formato do PDF baseado no texto da primeira pagina.

    Comportamento Legado Preservado:
    - Retorna 'antigo' como fallback padrao.
    - Captura silenciosamente qualquer excecao (Exception) retornando 'antigo'.
    - Verifica marcadores exatos apenas na primeira pagina para otimizar performance.
    """
    if not caminho_arquivo:
        return MODELO_ANTIGO

    try:
        with pdfplumber.open(caminho_arquivo) as pdf:
            if not pdf.pages:
                return MODELO_ANTIGO

            text = pdf.pages[0].extract_text() or ""

        text_upper = text.upper()

        if any(padrao in text_upper for padrao in MARCADORES_CATAFACIL):
            return MODELO_CATAFACIL

    except Exception:
        pass

    return MODELO_ANTIGO
