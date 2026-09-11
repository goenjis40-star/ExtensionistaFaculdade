import os
import re
from collections import defaultdict
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

import pandas as pd

from config.settings import FATORES_CO2, MESES_POSSIVEIS
from core.constants import MODELO_CONSOLIDADO, MODELO_DESCONHECIDO
from core.parsers import processar_relatorio_pdf
from core.parsers.detector import detectar_modelo_pdf
from core.logger import log_info, log_debug, log_warning
from core.utils import criar_dataframe_vazio
from core.auditoria_periodo import auditar_periodos


def _detectar_periodo_pdf(caminho_pdf: str) -> Optional[str]:
    """
    Detecta o periodo (mes/ano) de um PDF a partir do nome do arquivo e
    do conteudo textual da primeira pagina.

    Estrategia:
    1. Buscar nome de mes no nome do arquivo
    2. Buscar nome de mes no texto do PDF
    3. Extrair ano (4 digitos) do nome do arquivo ou texto
    4. Combinar mes + ano, ou retornar apenas o ano
    """
    nome_base = os.path.splitext(os.path.basename(caminho_pdf))[0]
    texto_combinado = nome_base

    try:
        import pdfplumber

        with pdfplumber.open(caminho_pdf) as pdf:
            if pdf.pages:
                texto_pagina = pdf.pages[0].extract_text() or ""
                texto_combinado = f"{nome_base} {texto_pagina}"
    except Exception:
        pass

    texto_lower = texto_combinado.lower()

    mes_encontrado = None
    for mes in MESES_POSSIVEIS:
        if mes.lower() in texto_lower:
            mes_encontrado = mes
            break

    anos = re.findall(r"\b(20\d{2})\b", texto_combinado)
    ano_encontrado = anos[0] if anos else None

    if mes_encontrado and ano_encontrado:
        return f"{mes_encontrado} {ano_encontrado}"
    elif mes_encontrado:
        return mes_encontrado
    elif ano_encontrado:
        return ano_encontrado
    return None


def consolidar_multiplos_pdfs(
    caminhos: List[str],
    fator_co2_map: Optional[Dict[str, float]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Processa multiplos PDFs e consolida os resultados em um unico par de DataFrames.

    Args:
        caminhos: Lista de caminhos absolutos para arquivos PDF
        fator_co2_map: Mapa opcional de fatores de CO2

    Returns:
        Tuple com:
        - df_consolidado: DataFrame consolidado com colunas padronizadas
        - df_bruto: DataFrame bruto com todos os materiais de todos os PDFs
        - meta: Dicionario com:
            - modelo: MODELO_CONSOLIDADO
            - info_list: Lista de metadados de cada PDF processado
            - df_mensal: DataFrame com totais por periodo (Periodo, Arquivo, Peso, CO2)
            - quantidade_pdfs: Total de PDFs submetidos
            - periodo_inicial: Primeiro periodo detectado
            - periodo_final: Ultimo periodo detectado
    """
    meta_vazio = {
        "modelo": MODELO_CONSOLIDADO,
        "info_list": [],
        "df_mensal": pd.DataFrame(
            columns=["Periodo", "Arquivo", "Peso Total (t)", "CO2 Evitado (t CO2e)"]
        ),
        "quantidade_pdfs": 0,
        "periodo_inicial": None,
        "periodo_final": None,
    }

    if not caminhos:
        return criar_dataframe_vazio(), pd.DataFrame(), meta_vazio

    if fator_co2_map is None:
        fator_co2_map = FATORES_CO2

    df_vazio = criar_dataframe_vazio()
    todos_brutos = []
    todos_cons = []
    soma_categorias = defaultdict(Decimal)
    info_list = []
    erros = 0
    periodos_detectados = []

    for idx, caminho in enumerate(caminhos):
        nome = os.path.basename(caminho)
        log_info(f"Processando [{idx + 1}/{len(caminhos)}]: {nome}")

        try:
            modelo = detectar_modelo_pdf(caminho)
            periodo = _detectar_periodo_pdf(caminho)

            df_cons, df_bruto = processar_relatorio_pdf(caminho, fator_co2_map)

            if not df_bruto.empty:
                df_bruto["Origem"] = nome
                todos_brutos.append(df_bruto)

            if not df_cons.empty:
                peso_total_pdf = float(df_cons["Peso Total (t)"].sum())
                co2_total_pdf = float(df_cons["CO2 Evitado (t CO2e)"].sum())
                todos_cons.append(
                    {
                        "Periodo": periodo or "Nao detectado",
                        "Arquivo": nome,
                        "Peso Total (t)": peso_total_pdf,
                        "CO2 Evitado (t CO2e)": co2_total_pdf,
                    }
                )

                for _, row in df_cons.iterrows():
                    chave = str(row["Categoria"]).upper()
                    soma_categorias[chave] += Decimal(str(row["Peso Total (t)"]))

            info_list.append(
                {
                    "arquivo": nome,
                    "modelo": modelo,
                    "periodo": periodo or "Nao detectado",
                    "linhas": len(df_bruto),
                    "categorias": len(df_cons),
                    "status": "OK",
                }
            )

            if periodo:
                periodos_detectados.append(periodo)

            log_debug(
                f'  Modelo: {modelo} | Periodo: {periodo or "?"} | Linhas: {len(df_bruto)} | Categorias: {len(df_cons)}'
            )

        except Exception as e:
            log_warning(f"[AVISO] Falha ao processar {nome}: {e}")
            info_list.append(
                {
                    "arquivo": nome,
                    "modelo": MODELO_DESCONHECIDO,
                    "periodo": "?",
                    "linhas": 0,
                    "categorias": 0,
                    "status": f"ERRO: {e}",
                }
            )
            erros += 1

    if not todos_brutos:
        log_warning("Nenhum PDF produziu dados.")
        meta_vazio["info_list"] = info_list
        meta_vazio["quantidade_pdfs"] = len(caminhos)
        return df_vazio, pd.DataFrame(), meta_vazio

    df_bruto_total = pd.concat(todos_brutos, ignore_index=True)

    linhas_consolidado = []
    for cat, peso_t in sorted(soma_categorias.items()):
        co2 = float(peso_t) * fator_co2_map.get(cat, 0)
        linhas_consolidado.append(
            {
                "Categoria": cat.title(),
                "Peso Total (t)": float(peso_t),
                "CO2 Evitado (t CO2e)": co2,
            }
        )

    df_consolidado_total = pd.DataFrame(linhas_consolidado)
    df_mensal = pd.DataFrame(todos_cons)

    periodo_inicial = periodos_detectados[0] if periodos_detectados else None
    periodo_final = periodos_detectados[-1] if periodos_detectados else None

    meta = {
        "modelo": MODELO_CONSOLIDADO,
        "info_list": info_list,
        "df_mensal": df_mensal,
        "quantidade_pdfs": len(caminhos),
        "periodo_inicial": periodo_inicial,
        "periodo_final": periodo_final,
        "auditoria_periodo": auditar_periodos(info_list),
    }

    total_linhas = len(df_bruto_total)
    log_info(
        f"Consolidacao concluida: {len(caminhos)} PDF(s), "
        f"{total_linhas} linhas brutas, "
        f"{len(df_consolidado_total)} categorias, "
        f"{len(df_mensal)} periodos, "
        f"{erros} erro(s)"
    )

    return df_consolidado_total, df_bruto_total, meta


def detectar_periodo_consolidado(info_list: List[Dict]) -> str:
    """
    Compoe uma string descritiva do periodo com base nos metadados de cada PDF.
    """
    periodos = [
        i["periodo"]
        for i in info_list
        if i.get("periodo") and i["periodo"] != "Nao detectado"
    ]
    if not periodos:
        return "Periodo nao detectado"

    meses_encontrados = []
    anos_encontrados = set()
    for p in periodos:
        for mes in MESES_POSSIVEIS:
            if mes.lower() in p.lower():
                meses_encontrados.append(mes)
                break
        anos_match = re.findall(r"\b(20\d{2})\b", p)
        anos_encontrados.update(anos_match)

    if meses_encontrados:
        primeiro = meses_encontrados[0]
        ultimo = meses_encontrados[-1]
        base = f"{primeiro} a {ultimo}" if len(meses_encontrados) > 1 else primeiro
        if anos_encontrados:
            anos_str = ", ".join(sorted(anos_encontrados))
            return f"{base} {anos_str}"
        return base

    if anos_encontrados:
        return ", ".join(sorted(anos_encontrados))

    return periodos[0]
