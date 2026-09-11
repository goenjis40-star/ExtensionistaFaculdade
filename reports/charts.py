import os
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional

from reports.templates import CORES_CATEGORIA, COR_PADRAO_GRAFICO
from core.utils_periodo import ordenar_periodos


def gerar_grafico_barras(
    df_consolidado: pd.DataFrame,
    caminho_saida: str,
    titulo: Optional[str] = None,
) -> str:
    """
    Gera um grafico de barras horizontais com o CO2 evitado por categoria.

    Args:
        df_consolidado: DataFrame com colunas ['Categoria', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']
        caminho_saida: Caminho para salvar a imagem PNG
        titulo: Titulo opcional do grafico

    Returns:
        Caminho absoluto da imagem gerada

    Raises:
        ValueError: Se o DataFrame estiver vazio
    """
    if df_consolidado.empty:
        raise ValueError("DataFrame consolidado vazio - nao e possivel gerar grafico.")

    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(10, max(3, len(df_consolidado) * 0.7)))

    df_sorted = df_consolidado.sort_values("CO2 Evitado (t CO2e)", ascending=True)

    categorias = df_sorted["Categoria"].tolist()
    co2_valores = df_sorted["CO2 Evitado (t CO2e)"].tolist()
    cores = [CORES_CATEGORIA.get(c, COR_PADRAO_GRAFICO) for c in categorias]

    barras = ax.barh(
        categorias, co2_valores, color=cores, edgecolor="white", linewidth=0.5
    )

    max_co2 = max(co2_valores) if co2_valores else 1
    for bar, valor in zip(barras, co2_valores):
        label = f"{valor:.3f} t"
        ax.text(
            valor + (max_co2 * 0.02),
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#333333",
        )

    titulo_final = titulo or "CO2 Evitado por Categoria (t CO2e)"
    ax.set_title(titulo_final, fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("CO2 Evitado (t CO2e)", fontsize=11)
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=10)
    ax.tick_params(axis="x", labelsize=9)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    diretorio = os.path.dirname(os.path.abspath(caminho_saida))
    os.makedirs(diretorio, exist_ok=True)

    fig.savefig(caminho_saida, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return os.path.abspath(caminho_saida)


def gerar_grafico_co2_mensal(
    df_mensal: pd.DataFrame,
    caminho_saida: str,
    titulo: Optional[str] = None,
) -> str:
    """
    Gera um grafico de linhas com a evolucao mensal do CO2 evitado.

    Args:
        df_mensal: DataFrame com colunas ['Periodo', 'CO2 Evitado (t CO2e)']
        caminho_saida: Caminho para salvar a imagem PNG
        titulo: Titulo opcional

    Returns:
        Caminho absoluto da imagem gerada
    """
    if df_mensal.empty:
        raise ValueError("df_mensal vazio - nao e possivel gerar grafico.")

    df = ordenar_periodos(df_mensal)

    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(11, 5))

    periodos = df["Periodo"].tolist()
    valores = df["CO2 Evitado (t CO2e)"].tolist()

    ax.fill_between(range(len(periodos)), valores, alpha=0.15, color="#17A2B8")
    ax.plot(
        range(len(periodos)),
        valores,
        marker="o",
        linewidth=2.2,
        color="#17A2B8",
        markersize=7,
        markerfacecolor="white",
        markeredgewidth=2,
        markeredgecolor="#17A2B8",
    )

    for i, val in enumerate(valores):
        ax.text(
            i,
            val + (max(valores) * 0.03),
            f"{val:.1f}",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color="#333333",
        )

    ax.set_xticks(range(len(periodos)))
    ax.set_xticklabels(periodos, rotation=45, ha="right", fontsize=9)

    titulo_final = titulo or "Evolucao Mensal — CO2 Evitado (t CO2e)"
    ax.set_title(titulo_final, fontsize=13, fontweight="bold", pad=15)
    ax.set_ylabel("CO2 Evitado (t CO2e)", fontsize=10)
    ax.set_xlabel("")
    ax.tick_params(axis="y", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    diretorio = os.path.dirname(os.path.abspath(caminho_saida))
    os.makedirs(diretorio, exist_ok=True)

    fig.savefig(caminho_saida, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return os.path.abspath(caminho_saida)


def gerar_grafico_peso_mensal(
    df_mensal: pd.DataFrame,
    caminho_saida: str,
    titulo: Optional[str] = None,
) -> str:
    """
    Gera um grafico de barras com a evolucao mensal do peso total.

    Args:
        df_mensal: DataFrame com colunas ['Periodo', 'Peso Total (t)']
        caminho_saida: Caminho para salvar a imagem PNG
        titulo: Titulo opcional

    Returns:
        Caminho absoluto da imagem gerada
    """
    if df_mensal.empty:
        raise ValueError("df_mensal vazio - nao e possivel gerar grafico.")

    df = ordenar_periodos(df_mensal)

    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(11, 5))

    periodos = df["Periodo"].tolist()
    valores = df["Peso Total (t)"].tolist()

    ax.bar(
        range(len(periodos)),
        valores,
        color="#28A745",
        edgecolor="white",
        linewidth=0.5,
        alpha=0.85,
    )

    for i, val in enumerate(valores):
        ax.text(
            i,
            val + (max(valores) * 0.03),
            f"{val:.1f}",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color="#333333",
        )

    ax.set_xticks(range(len(periodos)))
    ax.set_xticklabels(periodos, rotation=45, ha="right", fontsize=9)

    titulo_final = titulo or "Evolucao Mensal — Peso Total (t)"
    ax.set_title(titulo_final, fontsize=13, fontweight="bold", pad=15)
    ax.set_ylabel("Peso Total (t)", fontsize=10)
    ax.set_xlabel("")
    ax.tick_params(axis="y", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    diretorio = os.path.dirname(os.path.abspath(caminho_saida))
    os.makedirs(diretorio, exist_ok=True)

    fig.savefig(caminho_saida, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return os.path.abspath(caminho_saida)
