import os
import tempfile
from datetime import datetime
from typing import Optional, Tuple, List, Dict

import pandas as pd
from fpdf import FPDF

from config.settings import FATORES_CO2, FATOR_CARRO_ANO, FATOR_RESIDENCIA_MES
from core.constants import MODELO_CATAFACIL, MODELO_ANTIGO, MODELO_CONSOLIDADO
from core.logger import log_info, log_error, log_warning

from reports.templates import (
    COR_TEXTO_TITULO,
    COR_TEXTO_HEADER,
    COR_TEXTO_FOOTER,
    COR_TEXTO_CORPO,
    COR_FUNDO_DESTAQUE,
    COR_BORDA_DESTAQUE,
    COR_FUNDO_TABELA_HEADER,
    COR_FUNDO_TABELA_DADOS,
    COR_BORDA_TABELA,
    FONTE_TITULO,
    FONTE_CORPO,
    PAGE_WIDTH,
    PAGE_HEIGHT,
    MARGIN_LEFT,
    CONTENT_WIDTH,
    TABELA_COLUNAS,
    TEXTO_TITULO_RELATORIO,
    TEXTO_ORGANIZACAO,
    TEXTO_SECAO_DESTAQUE,
    TEXTO_SECAO_EXPLICACAO,
    TEXTO_SECAO_EQUIVALENCIAS,
    TEXTO_SECAO_TABELA,
    TEXTO_SECAO_GRAFICO,
    TEXTO_SECAO_NAO_CLASSIFICADOS,
    TEXTO_EXPLICATIVO,
    TEXTO_IMPACTO_GENERICO,
    TEMPLATE_CARROS,
    TEMPLATE_RESIDENCIAS,
    sanitize_pdf_text,
)
from reports.charts import gerar_grafico_barras


class _RelatorioPDF(FPDF):
    """Classe interna do PDF com header e footer customizados."""

    def __init__(self, titulo_relatorio: str = "", ano_relatorio: Optional[int] = None):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.titulo_relatorio = titulo_relatorio or TEXTO_TITULO_RELATORIO
        self.ano_relatorio = ano_relatorio

    def header(self):
        self.set_y(10)
        self.set_font(FONTE_TITULO, "B", 15)
        self.set_text_color(*COR_TEXTO_HEADER)
        sufixo_ano = f" {self.ano_relatorio}" if self.ano_relatorio else ""
        titulo = f"{self.titulo_relatorio} - {TEXTO_ORGANIZACAO}{sufixo_ano}"
        self.set_line_width(0.5)
        self.set_draw_color(100, 100, 100)
        self.line(MARGIN_LEFT, 10, PAGE_WIDTH - MARGIN_LEFT, 10)
        self.ln(1)
        self.cell(0, 9, titulo, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(FONTE_CORPO, "I", 8)
        self.set_text_color(*COR_TEXTO_FOOTER)
        self.set_line_width(0.2)
        self.set_draw_color(100, 100, 100)
        self.line(
            MARGIN_LEFT, PAGE_HEIGHT - 17, PAGE_WIDTH - MARGIN_LEFT, PAGE_HEIGHT - 17
        )
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f"EcoMetric 2.0 | Gerado em {data_hora}", align="C")


def _calcular_equivalencias(co2_total_t: float) -> Tuple[int, int]:
    """Calcula equivalencias ambientais a partir do CO2 total em toneladas."""
    carros = round(co2_total_t / FATOR_CARRO_ANO)
    residencias = round(co2_total_t / FATOR_RESIDENCIA_MES)
    return max(0, carros), max(0, residencias)


def _garantir_espaco(pdf: FPDF, altura_mm: float, margem: float = 277):
    """
    Garante que ha espaco suficiente na pagina atual antes de renderizar
    um bloco. Se nao houver, adiciona uma nova pagina.
    """
    if pdf.get_y() + altura_mm > margem:
        pdf.add_page()


def _formatar_numero_br(valor: float, casas: int = 3) -> str:
    """Formata numero no padrao brasileiro: 1.234,567."""
    formatted = f"{valor:,.{casas}f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


def _identificar_nao_classificados(
    df_bruto: pd.DataFrame,
    df_consolidado: pd.DataFrame,
    modelo_detectado: str,
) -> pd.DataFrame:
    """
    Identifica materiais do df_bruto que nao aparecem em nenhuma categoria do df_consolidado.
    Abordagem simplificada: agrupa por material e cruza com categorias conhecidas.
    """
    from core.categorias import (
        normalizar_categoria_generica,
        classificar_material_antigo,
    )

    categorias_validas = set()
    if not df_consolidado.empty:
        categorias_validas = set(df_consolidado["Categoria"].str.upper())

    nao_classificados = []
    if not df_bruto.empty:
        for _, row in df_bruto.iterrows():
            material = str(row["Material"])
            peso = row["Peso"]

            if modelo_detectado == MODELO_CATAFACIL:
                cat = normalizar_categoria_generica(material)
                if cat is None:
                    nao_classificados.append((material, float(peso)))
            elif modelo_detectado == MODELO_ANTIGO:
                cat = classificar_material_antigo(material)
                if cat == "NÃO CLASSIFICADO" or cat is None:
                    nao_classificados.append((material, float(peso)))
            else:
                cat = normalizar_categoria_generica(material)
                if cat is None:
                    nao_classificados.append((material, float(peso)))

    df_result = pd.DataFrame(nao_classificados, columns=["Material", "Peso (kg)"])
    return df_result


def gerar_relatorio_pdf(
    df_consolidado: pd.DataFrame,
    df_bruto: pd.DataFrame,
    caminho_saida: str,
    modelo_detectado: str = "desconhecido",
    caminho_pdf_original: str = "",
    tempo_execucao: float = 0.0,
    incluir_grafico: bool = True,
) -> str:
    """
    Gera um relatorio PDF completo com os resultados do processamento EcoMetric.

    Args:
        df_consolidado: DataFrame com colunas ['Categoria', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']
        df_bruto: DataFrame com colunas ['Material', 'Peso']
        caminho_saida: Caminho completo do arquivo PDF a ser gerado
        modelo_detectado: 'catafacil' ou 'antigo'
        caminho_pdf_original: Nome do PDF de origem
        tempo_execucao: Tempo de processamento em segundos
        incluir_grafico: Se True, inclui grafico de barras

    Returns:
        Caminho absoluto do PDF gerado

    Raises:
        ValueError: Se df_consolidado estiver vazio
    """
    log_info(f"Iniciando geracao de relatorio PDF: '{caminho_saida}'")

    if df_consolidado.empty:
        raise ValueError(
            "DataFrame consolidado vazio. Nao e possivel gerar relatorio sem dados processados."
        )

    diretorio_destino = os.path.dirname(os.path.abspath(caminho_saida))
    os.makedirs(diretorio_destino, exist_ok=True)

    co2_total = float(df_consolidado["CO2 Evitado (t CO2e)"].sum())
    peso_total = float(df_consolidado["Peso Total (t)"].sum())
    carros, residencias = _calcular_equivalencias(co2_total)

    df_tabela = df_consolidado.copy()
    df_tabela["% do Total"] = (
        (df_tabela["CO2 Evitado (t CO2e)"] / co2_total * 100)
        if co2_total > 0
        else 100.0
    )
    df_tabela = df_tabela.sort_values("CO2 Evitado (t CO2e)", ascending=False)

    ano_atual = datetime.now().year

    pdf = _RelatorioPDF(
        titulo_relatorio=TEXTO_TITULO_RELATORIO, ano_relatorio=ano_atual
    )
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- 0. TIPO DE RELATORIO (consolidado) ---
    if modelo_detectado == MODELO_CONSOLIDADO:
        pdf.set_font(FONTE_CORPO, "I", 9)
        pdf.set_text_color(*COR_TEXTO_FOOTER)
        pdf.cell(CONTENT_WIDTH, 5, "Tipo de Relatorio: Consolidado", align="C")
        pdf.ln(6)

    # --- 1. DESTAQUE: CO2 TOTAL ---
    pdf.ln(5)
    pdf.set_fill_color(*COR_FUNDO_DESTAQUE)
    pdf.set_draw_color(*COR_BORDA_DESTAQUE)
    pdf.set_line_width(0.6)

    y_destaque_inicio = pdf.get_y()
    pdf.set_font(FONTE_TITULO, "B", 12)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(CONTENT_WIDTH, 7, TEXTO_SECAO_DESTAQUE, align="C")
    pdf.ln(9)

    pdf.set_font(FONTE_TITULO, "B", 22)
    pdf.set_text_color(*COR_TEXTO_TITULO)
    co2_formatado = _formatar_numero_br(co2_total, 3)
    pdf.cell(CONTENT_WIDTH, 12, f"{co2_formatado} Toneladas de CO2e", align="C")
    pdf.ln(10)

    y_destaque_fim = pdf.get_y()
    pdf.set_fill_color(*COR_FUNDO_DESTAQUE)
    pdf.set_draw_color(*COR_BORDA_DESTAQUE)
    pdf.rect(
        MARGIN_LEFT - 2,
        y_destaque_inicio - 3,
        CONTENT_WIDTH + 4,
        y_destaque_fim - y_destaque_inicio + 6,
        style="D",
    )
    pdf.ln(8)

    # --- 2. TEXTO EXPLICATIVO ---
    pdf.set_font(FONTE_TITULO, "B", 12)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(0, 7, TEXTO_SECAO_EXPLICACAO)
    pdf.ln(9)

    pdf.set_font(FONTE_CORPO, "", 10)
    pdf.set_text_color(*COR_TEXTO_CORPO)
    pdf.multi_cell(CONTENT_WIDTH, 5, TEXTO_EXPLICATIVO)
    pdf.ln(5)

    # --- 3. EQUIVALENCIAS ---
    pdf.set_font(FONTE_TITULO, "B", 10)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(0, 6, TEXTO_SECAO_EQUIVALENCIAS)
    pdf.ln(8)

    pdf.set_font(FONTE_CORPO, "", 10)
    pdf.set_text_color(*COR_TEXTO_CORPO)

    equivalencias = [
        TEMPLATE_CARROS.format(carros),
        TEMPLATE_RESIDENCIAS.format(residencias),
        TEXTO_IMPACTO_GENERICO,
    ]
    for texto in equivalencias:
        pdf.cell(5, 5, "-")
        pdf.multi_cell(CONTENT_WIDTH - 5, 5, texto)
        pdf.ln(2)
    pdf.ln(5)

    # --- 4. TABELA DE DADOS ---
    _garantir_espaco(pdf, 40)
    pdf.set_font(FONTE_TITULO, "B", 12)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(0, 7, TEXTO_SECAO_TABELA)
    pdf.ln(10)

    colunas_tabela = [
        "Categoria",
        "Peso Total (t)",
        "CO2 Evitado (t CO2e)",
        "% do Total",
    ]
    larguras = [TABELA_COLUNAS[c] for c in colunas_tabela]

    # Cabecalho da tabela
    pdf.set_fill_color(*COR_FUNDO_TABELA_HEADER)
    pdf.set_draw_color(*COR_BORDA_TABELA)
    pdf.set_font(FONTE_TITULO, "B", 9)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.set_line_width(0.3)

    for i, (coluna, largura) in enumerate(zip(colunas_tabela, larguras)):
        alinhamento = "L" if coluna == "Categoria" else "C"
        pdf.cell(largura, 7, coluna, border=1, fill=True, align=alinhamento)
    pdf.ln()

    # Dados da tabela
    pdf.set_font(FONTE_CORPO, "", 9)
    pdf.set_fill_color(*COR_FUNDO_TABELA_DADOS)
    row_height = 6.5

    for _, row in df_tabela.iterrows():
        if pdf.get_y() > PAGE_HEIGHT - 35:
            pdf.add_page()

        pdf.set_text_color(*COR_TEXTO_CORPO)

        valores = [
            sanitize_pdf_text(str(row["Categoria"])),
            _formatar_numero_br(float(row["Peso Total (t)"]), 3),
            _formatar_numero_br(float(row["CO2 Evitado (t CO2e)"]), 3),
            f"{float(row['% do Total']):.1f}%",
        ]

        for valor, largura in zip(valores, larguras):
            alinhamento = "L" if str(row["Categoria"]) else "C"
            pdf.cell(largura, row_height, valor, border=1, fill=True, align=alinhamento)
        pdf.ln()

    # Linha de total
    pdf.set_font(FONTE_TITULO, "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_text_color(*COR_TEXTO_HEADER)

    pdf.cell(larguras[0], 7, "TOTAL GERAL", border=1, fill=True, align="L")
    pdf.cell(
        larguras[1],
        7,
        _formatar_numero_br(peso_total, 3),
        border=1,
        fill=True,
        align="C",
    )
    pdf.cell(
        larguras[2],
        7,
        _formatar_numero_br(co2_total, 3),
        border=1,
        fill=True,
        align="C",
    )
    pdf.cell(larguras[3], 7, "100.0%", border=1, fill=True, align="C")
    pdf.ln(12)

    # --- 5. GRAFICO ---
    _garantir_espaco(pdf, 80)
    grafico_path = None
    if incluir_grafico:
        try:
            if pdf.get_y() > PAGE_HEIGHT - 100:
                pdf.add_page()

            pdf.set_font(FONTE_TITULO, "B", 12)
            pdf.set_text_color(*COR_TEXTO_HEADER)
            pdf.cell(0, 7, TEXTO_SECAO_GRAFICO)
            pdf.ln(10)

            grafico_path = os.path.join(
                tempfile.gettempdir(),
                f'ecometric_grafico_{datetime.now().strftime("%Y%m%d%H%M%S")}.png',
            )
            gerar_grafico_barras(df_consolidado, grafico_path)

            pdf.image(grafico_path, w=CONTENT_WIDTH)
            pdf.ln(5)

        except Exception as e:
            log_warning(f"[AVISO] Nao foi possivel gerar o grafico: {e}")
        finally:
            if grafico_path and os.path.exists(grafico_path):
                try:
                    os.unlink(grafico_path)
                except OSError:
                    pass

    # --- 6. MATERIAIS NAO CLASSIFICADOS ---
    _garantir_espaco(pdf, 50)
    df_nao_classificados = _identificar_nao_classificados(
        df_bruto, df_consolidado, modelo_detectado
    )

    if not df_nao_classificados.empty:
        if pdf.get_y() > PAGE_HEIGHT - 60:
            pdf.add_page()

        pdf.set_font(FONTE_TITULO, "B", 12)
        pdf.set_text_color(*COR_TEXTO_HEADER)
        pdf.cell(0, 7, TEXTO_SECAO_NAO_CLASSIFICADOS)
        pdf.ln(8)

        pdf.set_font(FONTE_CORPO, "", 9)
        pdf.set_text_color(*COR_TEXTO_CORPO)
        pdf.cell(
            0, 5, f"Total de materiais nao classificados: {len(df_nao_classificados)}"
        )
        pdf.ln(6)

        # Limitar a 15 itens para nao sobrecarregar o relatorio
        itens_exibir = df_nao_classificados.head(15)

        pdf.set_fill_color(*COR_FUNDO_TABELA_HEADER)
        pdf.set_font(FONTE_TITULO, "B", 9)
        pdf.set_text_color(*COR_TEXTO_HEADER)
        pdf.cell(120, 6, "Material", border=1, fill=True, align="L")
        pdf.cell(50, 6, "Peso (kg)", border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font(FONTE_CORPO, "", 9)
        pdf.set_fill_color(*COR_FUNDO_TABELA_DADOS)

        for _, row in itens_exibir.iterrows():
            if pdf.get_y() > PAGE_HEIGHT - 25:
                pdf.add_page()
            pdf.set_text_color(*COR_TEXTO_CORPO)
            pdf.cell(
                120,
                5,
                sanitize_pdf_text(str(row["Material"])),
                border=1,
                fill=True,
                align="L",
            )
            pdf.cell(
                50,
                5,
                _formatar_numero_br(float(row["Peso (kg)"]), 2),
                border=1,
                fill=True,
                align="C",
            )
            pdf.ln()

        if len(df_nao_classificados) > 15:
            pdf.set_font(FONTE_CORPO, "I", 8)
            pdf.cell(
                0,
                5,
                f"... e mais {len(df_nao_classificados) - 15} materiais. Consulte o Excel para a lista completa.",
            )
            pdf.ln()

        pdf.ln(8)

    # --- SALVAR ---
    try:
        pdf.output(caminho_saida)
        log_info(f"Relatorio PDF gerado com sucesso: '{caminho_saida}'")
        return os.path.abspath(caminho_saida)
    except Exception as e:
        log_error(f"[ERRO] Falha ao salvar PDF: {e}")
        raise


def gerar_relatorio_anual(
    df_consolidado: pd.DataFrame,
    df_mensal: pd.DataFrame,
    meta: Dict,
    caminho_saida: str,
    df_bruto: Optional[pd.DataFrame] = None,
) -> str:
    """
    Gera um relatorio PDF anual consolidado a partir de multiplos PDFs mensais.

    Args:
        df_consolidado: DataFrame consolidado total (categorias)
        df_mensal: DataFrame com evolucao mensal (Periodo, Peso, CO2)
        meta: Dicionario de metadados da consolidacao
        caminho_saida: Caminho completo do PDF a ser gerado
        df_bruto: Opcional — DataFrame bruto para insights de materiais

    Returns:
        Caminho absoluto do PDF gerado
    """
    from reports.charts import gerar_grafico_co2_mensal, gerar_grafico_peso_mensal
    from core.utils_periodo import ordenar_periodos

    log_info(f"Iniciando geracao de relatorio anual: '{caminho_saida}'")

    if df_consolidado.empty:
        raise ValueError("DataFrame consolidado vazio.")

    diretorio_destino = os.path.dirname(os.path.abspath(caminho_saida))
    os.makedirs(diretorio_destino, exist_ok=True)

    co2_total = float(df_consolidado["CO2 Evitado (t CO2e)"].sum())
    peso_total = float(df_consolidado["Peso Total (t)"].sum())
    qtd_pdfs = meta.get("quantidade_pdfs", 0)
    p_inicial = meta.get("periodo_inicial") or "Nao detectado"
    p_final = meta.get("periodo_final") or "Nao detectado"

    df_tabela = df_consolidado.copy()
    df_tabela["% do Total"] = (
        (df_tabela["CO2 Evitado (t CO2e)"] / co2_total * 100)
        if co2_total > 0
        else 100.0
    )
    df_tabela = df_tabela.sort_values("CO2 Evitado (t CO2e)", ascending=False)

    carros, residencias = _calcular_equivalencias(co2_total)
    ano_atual = datetime.now().year

    pdf = _RelatorioPDF(
        titulo_relatorio="RELATORIO ANUAL CONSOLIDADO", ano_relatorio=ano_atual
    )
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- 1. CAPA ---
    pdf.ln(30)
    pdf.set_font(FONTE_TITULO, "B", 24)
    pdf.set_text_color(*COR_TEXTO_TITULO)
    pdf.cell(CONTENT_WIDTH, 14, "EcoMetric 2.0", align="C")
    pdf.ln(16)

    pdf.set_font(FONTE_TITULO, "B", 18)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(CONTENT_WIDTH, 12, "Relatorio Anual Consolidado", align="C")
    pdf.ln(18)

    pdf.set_draw_color(*COR_BORDA_DESTAQUE)
    pdf.set_line_width(0.6)
    y_line = pdf.get_y()
    pdf.line(MARGIN_LEFT + 30, y_line, PAGE_WIDTH - MARGIN_LEFT - 30, y_line)
    pdf.ln(10)

    pdf.set_font(FONTE_CORPO, "", 12)
    pdf.set_text_color(*COR_TEXTO_CORPO)
    pdf.cell(
        CONTENT_WIDTH,
        8,
        f"Periodo: {sanitize_pdf_text(p_inicial)} a {sanitize_pdf_text(p_final)}",
        align="C",
    )
    pdf.ln(8)
    pdf.cell(CONTENT_WIDTH, 8, f"PDFs processados: {qtd_pdfs}", align="C")
    pdf.ln(8)
    pdf.cell(
        CONTENT_WIDTH,
        8,
        f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        align="C",
    )
    pdf.ln(20)

    # --- 2. RESUMO EXECUTIVO ---
    pdf.add_page()
    pdf.set_font(FONTE_TITULO, "B", 16)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(0, 10, "Resumo Executivo")
    pdf.ln(14)

    pdf.set_fill_color(*COR_FUNDO_DESTAQUE)
    pdf.set_draw_color(*COR_BORDA_DESTAQUE)
    pdf.set_line_width(0.6)

    y_box = pdf.get_y()
    pdf.set_font(FONTE_TITULO, "B", 20)
    pdf.set_text_color(*COR_TEXTO_TITULO)
    pdf.cell(
        CONTENT_WIDTH,
        12,
        f"{_formatar_numero_br(co2_total, 3)} t CO2e Evitado",
        align="C",
    )
    pdf.ln(10)
    pdf.set_font(FONTE_CORPO, "", 11)
    pdf.set_text_color(*COR_TEXTO_CORPO)
    pdf.cell(
        CONTENT_WIDTH,
        7,
        f"Peso total processado: {_formatar_numero_br(peso_total, 3)} t",
        align="C",
    )
    pdf.ln(7)
    pdf.cell(
        CONTENT_WIDTH,
        7,
        f"Categorias: {len(df_consolidado)} | Meses consolidados: {qtd_pdfs}",
        align="C",
    )
    pdf.ln(6)
    y_box_end = pdf.get_y()
    pdf.rect(
        MARGIN_LEFT - 2, y_box - 3, CONTENT_WIDTH + 4, y_box_end - y_box + 6, style="D"
    )
    pdf.ln(12)

    pdf.set_font(FONTE_CORPO, "", 10)
    pdf.set_text_color(*COR_TEXTO_CORPO)
    pdf.cell(0, 6, f"Equivalencias ambientais:")
    pdf.ln(8)
    pdf.cell(5, 5, "-")
    pdf.multi_cell(CONTENT_WIDTH - 5, 5, TEMPLATE_CARROS.format(carros))
    pdf.ln(2)
    pdf.cell(5, 5, "-")
    pdf.multi_cell(CONTENT_WIDTH - 5, 5, TEMPLATE_RESIDENCIAS.format(residencias))
    pdf.ln(2)
    pdf.cell(5, 5, "-")
    pdf.multi_cell(CONTENT_WIDTH - 5, 5, TEXTO_IMPACTO_GENERICO)
    pdf.ln(8)

    # --- 2.5. AUDITORIA DA CONSOLIDACAO ---
    _garantir_espaco(pdf, 40)
    auditoria = meta.get("auditoria_periodo", {})
    avisos = auditoria.get("avisos", [])
    if avisos:
        pdf.set_fill_color(255, 245, 220)
        pdf.set_draw_color(200, 170, 80)
        pdf.set_line_width(0.4)

        y_audit = pdf.get_y()
        pdf.set_font(FONTE_TITULO, "B", 11)
        pdf.set_text_color(180, 130, 30)
        pdf.cell(CONTENT_WIDTH, 7, "Auditoria da Consolidacao", align="C")
        pdf.ln(10)

        pdf.set_font(FONTE_CORPO, "", 9)
        pdf.set_text_color(*COR_TEXTO_CORPO)

        if auditoria.get("meses_faltantes"):
            pdf.set_font(FONTE_TITULO, "B", 9)
            pdf.cell(0, 5, "Meses faltantes:")
            pdf.ln(5)
            pdf.set_font(FONTE_CORPO, "", 9)
            faltantes = auditoria.get("meses_faltantes", [])
            for m in faltantes[:10]:
                pdf.cell(5, 4, "-")
                pdf.cell(0, 4, sanitize_pdf_text(m))
                pdf.ln()
            if len(faltantes) > 10:
                pdf.set_font(FONTE_CORPO, "I", 8)
                pdf.cell(0, 4, f"... e mais {len(faltantes) - 10}")
                pdf.ln()
            pdf.ln(3)

        if auditoria.get("meses_duplicados"):
            pdf.set_font(FONTE_TITULO, "B", 9)
            pdf.cell(0, 5, "Meses duplicados:")
            pdf.ln(5)
            pdf.set_font(FONTE_CORPO, "", 9)
            duplicados = auditoria.get("meses_duplicados", [])
            for m in duplicados[:10]:
                pdf.cell(5, 4, "-")
                pdf.cell(0, 4, sanitize_pdf_text(m))
                pdf.ln()
            pdf.ln(3)

        if auditoria.get("anos_multiplos"):
            pdf.set_font(FONTE_TITULO, "B", 9)
            pdf.cell(
                0,
                5,
                f"Anos detectados: {', '.join(str(a) for a in auditoria.get('anos_detectados', []))}",
            )
            pdf.ln(6)

        pdf.set_font(FONTE_CORPO, "I", 9)
        pdf.set_text_color(150, 120, 20)
        pdf.cell(0, 5, "O relatorio foi gerado com dados incompletos.")
        pdf.ln(4)

        y_audit_end = pdf.get_y()
        pdf.rect(
            MARGIN_LEFT - 1,
            y_audit - 3,
            CONTENT_WIDTH + 2,
            y_audit_end - y_audit + 5,
            style="D",
        )
        pdf.ln(8)
    else:
        pdf.set_font(FONTE_CORPO, "", 9)
        pdf.set_text_color(40, 140, 40)
        pdf.cell(0, 5, "Consolidacao validada. Nenhuma inconsistencia detectada.")
        pdf.ln(8)

    # --- 3. EVOLUCAO MENSAL ---
    pdf.add_page()
    pdf.set_font(FONTE_TITULO, "B", 14)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(0, 8, "Evolucao Mensal")
    pdf.ln(12)

    if not df_mensal.empty:
        df_ord = ordenar_periodos(df_mensal)

        colunas_tab = ["Periodo", "Peso Total (t)", "CO2 Evitado (t CO2e)"]
        larguras_tab = [60, 55, 55]

        pdf.set_fill_color(*COR_FUNDO_TABELA_HEADER)
        pdf.set_draw_color(*COR_BORDA_TABELA)
        pdf.set_font(FONTE_TITULO, "B", 9)
        pdf.set_text_color(*COR_TEXTO_HEADER)
        pdf.set_line_width(0.3)
        for col, larg in zip(colunas_tab, larguras_tab):
            pdf.cell(larg, 7, col, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font(FONTE_CORPO, "", 9)
        pdf.set_fill_color(*COR_FUNDO_TABELA_DADOS)

        for _, row in df_ord.iterrows():
            if pdf.get_y() > PAGE_HEIGHT - 30:
                pdf.add_page()
            pdf.set_text_color(*COR_TEXTO_CORPO)
            pdf.cell(
                larguras_tab[0],
                6.5,
                sanitize_pdf_text(str(row["Periodo"])),
                border=1,
                fill=True,
                align="L",
            )
            pdf.cell(
                larguras_tab[1],
                6.5,
                _formatar_numero_br(float(row["Peso Total (t)"]), 3),
                border=1,
                fill=True,
                align="C",
            )
            pdf.cell(
                larguras_tab[2],
                6.5,
                _formatar_numero_br(float(row["CO2 Evitado (t CO2e)"]), 3),
                border=1,
                fill=True,
                align="C",
            )
            pdf.ln()

        pdf.set_font(FONTE_TITULO, "B", 9)
        pdf.set_fill_color(230, 230, 230)
        pdf.set_text_color(*COR_TEXTO_HEADER)
        pdf.cell(larguras_tab[0], 7, "TOTAL ANUAL", border=1, fill=True, align="L")
        pdf.cell(
            larguras_tab[1],
            7,
            _formatar_numero_br(peso_total, 3),
            border=1,
            fill=True,
            align="C",
        )
        pdf.cell(
            larguras_tab[2],
            7,
            _formatar_numero_br(co2_total, 3),
            border=1,
            fill=True,
            align="C",
        )
        pdf.ln(12)
    else:
        pdf.set_font(FONTE_CORPO, "I", 10)
        pdf.cell(0, 6, "Dados mensais nao disponiveis.")
        pdf.ln(10)

    # --- 4. GRAFICOS MENSAIS ---
    _garantir_espaco(pdf, 90)
    grafico_paths = []
    if not df_mensal.empty:
        try:
            if pdf.get_y() > PAGE_HEIGHT - 90:
                pdf.add_page()

            path_co2 = os.path.join(
                tempfile.gettempdir(),
                f'ecometric_co2_mensal_{datetime.now().strftime("%Y%m%d%H%M%S")}.png',
            )
            gerar_grafico_co2_mensal(df_mensal, path_co2)
            grafico_paths.append(path_co2)
            pdf.image(path_co2, w=CONTENT_WIDTH)
            pdf.ln(8)

            path_peso = os.path.join(
                tempfile.gettempdir(),
                f'ecometric_peso_mensal_{datetime.now().strftime("%Y%m%d%H%M%S")}.png',
            )
            gerar_grafico_peso_mensal(df_mensal, path_peso)
            grafico_paths.append(path_peso)
            pdf.image(path_peso, w=CONTENT_WIDTH)
            pdf.ln(8)

        except Exception as e:
            log_warning(f"[AVISO] Nao foi possivel gerar graficos mensais: {e}")
        finally:
            for p in grafico_paths:
                if os.path.exists(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    # --- 4.5. GRAFICO DE CATEGORIAS ---
    _garantir_espaco(pdf, 80)
    grafico_cat_path = None
    try:
        if pdf.get_y() > PAGE_HEIGHT - 80:
            pdf.add_page()
        grafico_cat_path = os.path.join(
            tempfile.gettempdir(),
            f'ecometric_cat_{datetime.now().strftime("%Y%m%d%H%M%S")}.png',
        )
        from reports.charts import gerar_grafico_barras

        gerar_grafico_barras(
            df_consolidado,
            grafico_cat_path,
            titulo="Participacao por Categoria — CO2 Evitado (t CO2e)",
        )
        pdf.image(grafico_cat_path, w=CONTENT_WIDTH)
        pdf.ln(6)
    except Exception as e:
        log_warning(f"[AVISO] Nao foi possivel gerar grafico de categorias: {e}")
    finally:
        if grafico_cat_path and os.path.exists(grafico_cat_path):
            try:
                os.unlink(grafico_cat_path)
            except OSError:
                pass

    # --- 5. CONSOLIDADO POR CATEGORIA ---
    _garantir_espaco(pdf, 60)
    if pdf.get_y() > PAGE_HEIGHT - 70:
        pdf.add_page()

    pdf.set_font(FONTE_TITULO, "B", 14)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(0, 8, "Consolidado por Categoria")
    pdf.ln(10)

    colunas_cat = ["Categoria", "Peso Total (t)", "CO2 Evitado (t CO2e)", "% do Total"]
    larguras_cat = [TABELA_COLUNAS[c] for c in colunas_cat]

    pdf.set_fill_color(*COR_FUNDO_TABELA_HEADER)
    pdf.set_draw_color(*COR_BORDA_TABELA)
    pdf.set_font(FONTE_TITULO, "B", 9)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.set_line_width(0.3)
    for col, larg in zip(colunas_cat, larguras_cat):
        alinhamento = "L" if col == "Categoria" else "C"
        pdf.cell(larg, 7, col, border=1, fill=True, align=alinhamento)
    pdf.ln()

    pdf.set_font(FONTE_CORPO, "", 9)
    pdf.set_fill_color(*COR_FUNDO_TABELA_DADOS)
    row_height = 6.5
    for _, row in df_tabela.iterrows():
        if pdf.get_y() > PAGE_HEIGHT - 35:
            pdf.add_page()
        pdf.set_text_color(*COR_TEXTO_CORPO)
        vals = [
            sanitize_pdf_text(str(row["Categoria"])),
            _formatar_numero_br(float(row["Peso Total (t)"]), 3),
            _formatar_numero_br(float(row["CO2 Evitado (t CO2e)"]), 3),
            f"{float(row['% do Total']):.1f}%",
        ]
        for v, larg in zip(vals, larguras_cat):
            alinhamento = "L" if str(row["Categoria"]) else "C"
            pdf.cell(larg, row_height, v, border=1, fill=True, align=alinhamento)
        pdf.ln()

    pdf.set_font(FONTE_TITULO, "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_text_color(*COR_TEXTO_HEADER)
    pdf.cell(larguras_cat[0], 7, "TOTAL GERAL", border=1, fill=True, align="L")
    pdf.cell(
        larguras_cat[1],
        7,
        _formatar_numero_br(peso_total, 3),
        border=1,
        fill=True,
        align="C",
    )
    pdf.cell(
        larguras_cat[2],
        7,
        _formatar_numero_br(co2_total, 3),
        border=1,
        fill=True,
        align="C",
    )
    pdf.cell(larguras_cat[3], 7, "100.0%", border=1, fill=True, align="C")

    # --- SALVAR ---
    try:
        pdf.output(caminho_saida)
        log_info(f"Relatorio anual PDF gerado com sucesso: '{caminho_saida}'")
        return os.path.abspath(caminho_saida)
    except Exception as e:
        log_error(f"[ERRO] Falha ao salvar PDF anual: {e}")
        raise
