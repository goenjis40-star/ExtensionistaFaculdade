import re
from typing import List, Tuple, Optional
import pandas as pd

from config.settings import MESES_POSSIVEIS

_MES_MAP = {mes.lower(): i + 1 for i, mes in enumerate(MESES_POSSIVEIS)}


def normalizar_periodo(periodo: str) -> Tuple[int, int]:
    """
    Converte uma string de periodo (ex: 'Maio 2025', 'Janeiro 2026')
    em uma tupla ordenavel (mes, ano).

    Args:
        periodo: String no formato 'Mes Ano' ou apenas 'Mes' ou 'Ano'

    Returns:
        Tupla (mes, ano). Mes=0 se nao detectado.

    Examples:
        >>> normalizar_periodo('Maio 2025')
        (5, 2025)
        >>> normalizar_periodo('Janeiro 2026')
        (1, 2026)
        >>> normalizar_periodo('2025')
        (0, 2025)
    """
    periodo_lower = periodo.lower().strip()

    mes = 0
    for nome_mes, num in _MES_MAP.items():
        if nome_mes in periodo_lower:
            mes = num
            break

    anos = re.findall(r"\b(20\d{2})\b", periodo)
    ano = int(anos[0]) if anos else 0

    return (mes, ano)


def ordenar_periodos(df: pd.DataFrame, coluna_periodo: str = "Periodo") -> pd.DataFrame:
    """
    Ordena um DataFrame por periodo cronologicamente (nao alfabeticamente).

    Args:
        df: DataFrame com coluna de periodo
        coluna_periodo: Nome da coluna contendo strings de periodo

    Returns:
        DataFrame ordenado por (ano, mes)

    Raises:
        ValueError: Se a coluna nao existir ou o DataFrame estiver vazio
    """
    if df.empty:
        return df

    if coluna_periodo not in df.columns:
        raise ValueError(
            f"Coluna '{coluna_periodo}' nao encontrada. Colunas: {list(df.columns)}"
        )

    df_copy = df.copy()
    df_copy["_ordem"] = df_copy[coluna_periodo].apply(
        lambda p: normalizar_periodo(str(p)) if pd.notna(p) else (0, 0)
    )
    df_sorted = (
        df_copy.sort_values("_ordem").drop(columns=["_ordem"]).reset_index(drop=True)
    )
    return df_sorted
