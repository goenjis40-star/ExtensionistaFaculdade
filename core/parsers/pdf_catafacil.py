import pdfplumber
import pandas as pd
from collections import defaultdict
from decimal import Decimal
from typing import Tuple, Dict, Optional

from config.settings import FATORES_CO2, DEBUG
from core.categorias import normalizar_categoria_generica
from core.utils import parse_peso_brasileiro, criar_dataframe_vazio
from core.logger import log_debug, log_info, log_error, log_warning


def parse_pdf_catafacil(
    caminho_arquivo: Optional[str], fator_co2_map: Optional[Dict[str, float]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parser para o modelo de PDF CataFácil do EcoMetric.

    Preserva com exatidão todas as assimetrias em relação ao parser antigo:
    - Uso de split() posicional em vez de regex para extrair materiais.
    - Captura silenciosa de erros de conversão numérica (sem prints de aviso).
    - Uso do `normalizar_categoria_generica` (sem prioridade de Plásticos do parser antigo).
    - Prints de output histórico controlados pelo modo DEBUG configurável.
    - O(N^2) print de NÃO CLASSIFICADOS otimizado para produção.
    """
    log_debug(">>> FUNÇÃO CATAFACIL SENDO EXECUTADA <<<")

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

                if DEBUG:
                    print("\n================ DEBUG PDF CATÁFACIL ================")
                    print(text)
                    print("=====================================================\n")

                for raw_line in text.splitlines():
                    line = (raw_line or "").strip()
                    if not line:
                        continue

                    if line.startswith("Material"):
                        continue
                    if line.startswith("Unidade=>"):
                        continue
                    if (
                        line.startswith("Total Geral")
                        or line.startswith("Total da Unidade")
                        or line.startswith("TOTAL DA UNIDADE")
                    ):
                        continue

                    partes = line.split()

                    # Contrato posicional do CataFácil
                    if len(partes) >= 4:
                        unidade = partes[-3].upper()
                        peso_raw = partes[-2]

                        if unidade in ["KG", "LT", "UND"]:
                            material = " ".join(partes[:-3]).strip().upper()

                            try:
                                peso_valor = parse_peso_brasileiro(peso_raw)
                            except ValueError:
                                # O legado do CataFácil captura a exceção silenciosamente
                                continue

                            if peso_valor > 0:
                                log_debug(f"CAPTURADO: {material} {peso_valor}")
                                df_lista.append(
                                    {"Material": material, "Peso": peso_valor}
                                )

    except Exception as e:
        log_error(f"[ERRO] Falha ao ler PDF Catafacil: {e}")
        return df_vazio, pd.DataFrame()

    if not df_lista:
        log_warning("[ERRO] Nenhum material capturado no PDF.")
        return df_vazio, pd.DataFrame()

    # Consolidação por material (em Decimal)
    soma_por_material = defaultdict(Decimal)
    for item in df_lista:
        soma_por_material[item["Material"]] += item["Peso"]

    pesos_por_categoria = defaultdict(Decimal)

    # Classificação assimétrica (usa normalizar_categoria_generica, não a lógica do antigo)
    for mat, peso in soma_por_material.items():
        categoria_normalizada = normalizar_categoria_generica(mat, fator_co2_map)

        if categoria_normalizada:
            pesos_por_categoria[categoria_normalizada.upper()] += peso

            # Preserva a regra implícita histórica (O(N^2) print de NÃO CLASSIFICADOS) apenas em depuração
            if DEBUG:
                print("\nMATERIAIS NÃO CLASSIFICADOS:")
                for mat_unclass, peso_unclass in soma_por_material.items():
                    if not normalizar_categoria_generica(mat_unclass, fator_co2_map):
                        print(f"  - {mat_unclass}: {peso_unclass} kg")

    lista_final = []
    for cat, peso_kg in pesos_por_categoria.items():
        # Transição Decimal -> float apenas no cálculo final
        peso_t = float(peso_kg) / 1000.0
        # CataFácil capitaliza as categorias após o upper()
        co2 = peso_t * fator_co2_map.get(cat, 0)

        lista_final.append(
            {
                "Categoria": cat.title(),
                "Peso Total (t)": peso_t,
                "CO2 Evitado (t CO2e)": co2,
            }
        )

    return pd.DataFrame(lista_final), pd.DataFrame(df_lista)


class ParserPDFCatafacil:
    """Wrapper orientado a objetos para o parser do PDF CataFácil."""

    def __init__(self, fatores_co2: Optional[Dict[str, float]] = None):
        self.fatores_co2 = fatores_co2 if fatores_co2 is not None else FATORES_CO2

    def processar(
        self, caminho_arquivo: Optional[str]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        return parse_pdf_catafacil(caminho_arquivo, self.fatores_co2)
