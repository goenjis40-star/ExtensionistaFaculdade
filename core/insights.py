import re
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd

from core.utils_periodo import normalizar_periodo


def _limpar_material(nome: str) -> str:
    """Remove prefixos de numero de pagina do pdfplumber (ex: '00\\nALUMINIO')."""
    return re.sub(r"^\d+\n", "", str(nome)).strip()


def gerar_insights(
    df_consolidado: pd.DataFrame,
    df_bruto: pd.DataFrame,
    df_mensal: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Gera insights analiticos a partir dos dados processados.

    Args:
        df_consolidado: DataFrame com colunas ['Categoria', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']
        df_bruto: DataFrame com colunas ['Material', 'Peso']
        df_mensal: Opcional — DataFrame com colunas ['Periodo', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']

    Returns:
        Dict com os insights calculados
    """
    resultado = {}

    if df_consolidado.empty:
        resultado["sem_dados"] = True
        return resultado

    peso_total = float(df_consolidado["Peso Total (t)"].sum())
    co2_total = float(df_consolidado["CO2 Evitado (t CO2e)"].sum())
    resultado["peso_total"] = peso_total
    resultado["co2_total"] = co2_total

    # Categoria dominante
    idx_max = df_consolidado["Peso Total (t)"].idxmax()
    cat_dominante = df_consolidado.loc[idx_max, "Categoria"]
    peso_cat = float(df_consolidado.loc[idx_max, "Peso Total (t)"])
    pct = (peso_cat / peso_total * 100) if peso_total > 0 else 0
    resultado["categoria_dominante"] = cat_dominante
    resultado["categoria_percentual"] = round(pct, 1)

    # Participacao de todas as categorias
    participacao = {}
    for _, row in df_consolidado.iterrows():
        cat = str(row["Categoria"])
        p = (float(row["Peso Total (t)"]) / peso_total * 100) if peso_total > 0 else 0
        participacao[cat] = round(p, 1)
    resultado["participacao_categorias"] = participacao

    # Top 5 materiais (agregando por nome limpo)
    if not df_bruto.empty:
        soma_materiais = defaultdict(Decimal)
        for _, row in df_bruto.iterrows():
            nome = _limpar_material(str(row["Material"]))
            try:
                peso_val = Decimal(str(row["Peso"]))
                soma_materiais[nome] += peso_val
            except Exception:
                pass

        top_materiais = sorted(
            soma_materiais.items(), key=lambda x: x[1], reverse=True
        )[:5]
        resultado["top_5_materiais"] = [
            {"material": m, "peso_kg": float(p)} for m, p in top_materiais
        ]

        if top_materiais:
            resultado["material_dominante"] = top_materiais[0][0]
            resultado["material_peso"] = float(top_materiais[0][1])

    # Maior e menor mes
    if df_mensal is not None and not df_mensal.empty:
        df_m = df_mensal.copy()

        if (
            "CO2 Evitado (t CO2e)" in df_m.columns
            and not df_m["CO2 Evitado (t CO2e)"].isna().all()
        ):
            idx_max_mes = df_m["CO2 Evitado (t CO2e)"].idxmax()
            idx_min_mes = df_m["CO2 Evitado (t CO2e)"].idxmin()

            resultado["maior_mes"] = str(df_m.loc[idx_max_mes, "Periodo"])
            resultado["maior_mes_co2"] = float(
                df_m.loc[idx_max_mes, "CO2 Evitado (t CO2e)"]
            )
            resultado["menor_mes"] = str(df_m.loc[idx_min_mes, "Periodo"])
            resultado["menor_mes_co2"] = float(
                df_m.loc[idx_min_mes, "CO2 Evitado (t CO2e)"]
            )

    resultado["sem_dados"] = False
    return resultado
