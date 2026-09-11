from decimal import Decimal, InvalidOperation
from typing import Union, Optional
import pandas as pd
from config.settings import COLUNAS_RESULTADO


def parse_peso_brasileiro(peso_raw: Union[str, int, float, Decimal]) -> Decimal:
    """Converte valor no formato brasileiro (1.234,56) para Decimal."""
    if peso_raw is None:
        raise ValueError("Peso não pode ser nulo.")

    if isinstance(peso_raw, Decimal):
        return peso_raw

    if isinstance(peso_raw, int):
        return Decimal(peso_raw)

    if isinstance(peso_raw, float):
        return Decimal(str(peso_raw))

    # Tratamento de String (Comportamento Legado)
    peso_str = str(peso_raw).strip()
    if not peso_str:
        raise ValueError("Peso em formato string está vazio.")

    # Formato BR: "1.234,56" → "1234.56"
    if "," in peso_str:
        # Padrão brasileiro explícito (ex: 1.234,56 -> 1234.56 ou 960,9 -> 960.9)
        peso_str = peso_str.replace(".", "").replace(",", ".")
    elif "." in peso_str:
        # Se contiver apenas ponto, e se parecer com milhar (ex: "1.200" -> 1200):
        # No legado: "1.200" -> replace('.', '') -> "1200" -> Decimal("1200").
        # Mas se for "1.2" -> replace('.', '') -> "12" (seria um erro se fosse decimal float).
        # Porém, no PDF antigo todas as leituras de peso sem vírgula mas com ponto são milhares (ex: "1.200 KG").
        # Portanto, preservamos a regra legado estrita para compatibilidade com os PDFs existentes:
        peso_str = peso_str.replace(".", "")

    try:
        return Decimal(peso_str)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"Não foi possível converter peso '{peso_raw}' para Decimal: {exc}"
        )


def converter_para_toneladas(
    peso: Union[Decimal, float, int, pd.Series], nome_coluna: Optional[str]
) -> Union[Decimal, float, int, pd.Series]:
    """
    Converte uma grandeza de peso para toneladas, detectando a unidade pelo nome da coluna.

    Regras de Unidades (Legado):
    - Se a coluna contiver 'KG' (e não 'TON'): divide por 1.000.
    - Se a coluna contiver 'GRAM' ou 'GR': divide por 1.000.000.
    - Caso contrário: mantém o valor original.

    Preservação de Decimal:
    - Se a entrada for Decimal, realiza divisão usando Decimal para evitar float.
    - Se a entrada for uma série Pandas de Decimals, realiza divisão element-wise de Decimal.
    """
    nome_coluna_upper = (nome_coluna or "").upper()

    if "KG" in nome_coluna_upper and "TON" not in nome_coluna_upper:
        divisor = 1000
    elif "GRAM" in nome_coluna_upper or "GR" in nome_coluna_upper:
        divisor = 1000000
    else:
        divisor = 1

    if divisor == 1:
        return peso

    if isinstance(peso, pd.Series):
        if not peso.empty and isinstance(peso.iloc[0], Decimal):
            # Divide cada Decimal por Decimal(divisor) para manter tipo exato
            return peso.apply(
                lambda x: (
                    x / Decimal(str(divisor)) if isinstance(x, Decimal) else x / divisor
                )
            )
        return peso / divisor
    else:
        if isinstance(peso, Decimal):
            return peso / Decimal(str(divisor))
        return peso / divisor


def criar_dataframe_vazio() -> pd.DataFrame:
    """Retorna um DataFrame vazio com as colunas padronizadas do sistema."""
    return pd.DataFrame(columns=COLUNAS_RESULTADO)
