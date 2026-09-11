from typing import Tuple, Dict, Optional
import pandas as pd

from core.constants import MODELO_CATAFACIL
from core.parsers.detector import detectar_modelo_pdf
from core.parsers.pdf_antigo import parse_pdf_antigo, ParserPDFAntigo


def processar_relatorio_pdf(
    caminho_arquivo: Optional[str], fator_co2_map: Optional[Dict[str, float]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Roteia o processamento do PDF para o parser correto baseado na detecção automática.
    """
    modelo = detectar_modelo_pdf(caminho_arquivo)
    if modelo == MODELO_CATAFACIL:
        try:
            from core.parsers.pdf_catafacil import parse_pdf_catafacil

            return parse_pdf_catafacil(caminho_arquivo, fator_co2_map)
        except ImportError:
            raise NotImplementedError("Parser CataFácil ainda não foi migrado.")

    return parse_pdf_antigo(caminho_arquivo, fator_co2_map)
