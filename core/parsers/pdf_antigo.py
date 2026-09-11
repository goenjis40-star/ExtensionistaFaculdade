import re
import pdfplumber
import pandas as pd
from collections import defaultdict
from decimal import Decimal
from typing import Tuple, Dict, Optional

from config.settings import FATORES_CO2, DEBUG
from core.categorias import classificar_material_antigo
from core.utils import parse_peso_brasileiro, criar_dataframe_vazio
from core.logger import log_debug, log_info, log_error, log_warning

# Regex exata para capturar números com pontos e vírgulas decimais (ex: 960,9)
LINE_REGEX = r"([A-Za-zÀ-ú0-9\s\/-]+?)\s+(?:KG|LT|UND)\s+([\d\.,]+)"


def parse_pdf_antigo(
    caminho_arquivo: Optional[str], fator_co2_map: Optional[Dict[str, float]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parser para o modelo de PDF antigo do EcoMetric.

    Preserva com exatidão matemática e lógica todas as heurísticas do legado:
    - Uso de Decimal para os cálculos intermediários de peso para evitar perdas decimais.
    - Captura e descarte silencioso de serviços e cabeçalhos.
    - Exibição de prints de debug históricos sob o modo DEBUG.
    - Prioridade especial de Plástico e regras de regex de categorias.
    - Divisão final por 1000.0 em float e conversão em Toneladas.
    """
    df_vazio = criar_dataframe_vazio()
    if not caminho_arquivo:
        return df_vazio, pd.DataFrame()

    if fator_co2_map is None:
        fator_co2_map = FATORES_CO2

    df_lista = []

    try:
        with pdfplumber.open(caminho_arquivo) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                # Preserva o cabeçalho de debug histórico sob modo DEBUG
                if DEBUG:
                    print("\n================ DEBUG PDF CATÁFACIL ================")
                    print(text)
                    print("=====================================================\n")

                matches = re.findall(LINE_REGEX, text, re.IGNORECASE)
                for material_raw, peso_raw in matches:
                    material = material_raw.strip().upper()

                    # Descarte de linhas de serviço / cabeçalhos legados
                    if any(
                        x in material
                        for x in [
                            "SERVICO",
                            "TRIAGEM",
                            "COLETA",
                            "TOTAL",
                            "VALOR",
                            "DATA:",
                            "PÁGINA",
                        ]
                    ):
                        continue

                    try:
                        peso_valor = parse_peso_brasileiro(peso_raw)
                    except ValueError as exc:
                        # Exibição de aviso controlada pelo logging
                        log_warning(
                            f"[AVISO] Não foi possível processar peso '{peso_raw}' ({material}): {exc}"
                        )
                        continue

                    if peso_valor > 0:
                        df_lista.append({"Material": material, "Peso": peso_valor})

    except Exception as e:
        log_error(f"Erro: {e}")
        return df_vazio, pd.DataFrame()

    soma_por_material = defaultdict(Decimal)
    for item in df_lista:
        soma_por_material[item["Material"]] += item["Peso"]

    pesos_por_categoria = defaultdict(Decimal)

    for mat, peso in soma_por_material.items():
        categoria_alvo = classificar_material_antigo(mat, fator_co2_map)
        pesos_por_categoria[categoria_alvo] += peso

    lista_final = []
    for cat, peso_kg in pesos_por_categoria.items():
        # Descarte silencioso de materiais não classificados
        if cat == "NÃO CLASSIFICADO":
            continue

        peso_t = float(peso_kg) / 1000.0
        co2 = peso_t * fator_co2_map.get(cat, 0)

        lista_final.append(
            {
                "Categoria": cat.title(),
                "Peso Total (t)": peso_t,
                "CO2 Evitado (t CO2e)": co2,
            }
        )

    return pd.DataFrame(lista_final), pd.DataFrame(df_lista)


class ParserPDFAntigo:
    """
    Wrapper class orientado a objetos para o parser do PDF antigo.
    Facilita a integração com a nova arquitetura de parsers modulares.
    """

    def __init__(self, fatores_co2: Optional[Dict[str, float]] = None):
        self.fatores_co2 = fatores_co2 if fatores_co2 is not None else FATORES_CO2

    def processar(
        self, caminho_arquivo: Optional[str]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        return parse_pdf_antigo(caminho_arquivo, self.fatores_co2)
