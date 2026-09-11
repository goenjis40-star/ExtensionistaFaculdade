from typing import Dict, Tuple

# --- CORES DO GRÁFICO DE BARRAS (MATPLOTLIB) ---
CORES_CATEGORIA: Dict[str, str] = {
    "Plástico": "#007BFF",
    "Papel": "#28A745",
    "Metal": "#FFC107",
    "Vidro": "#DC3545",
    "Eletroeletrônico": "#17A2B8",
    "Composto": "#6C757D",
}

COR_PADRAO_GRAFICO = "#6C757D"

# --- CORES DO PDF (RGB 0-255) ---
COR_TEXTO_TITULO: Tuple[int, int, int] = (0, 0, 0)
COR_TEXTO_HEADER: Tuple[int, int, int] = (40, 40, 40)
COR_TEXTO_FOOTER: Tuple[int, int, int] = (100, 100, 100)
COR_TEXTO_CORPO: Tuple[int, int, int] = (50, 50, 50)

COR_FUNDO_DESTAQUE: Tuple[int, int, int] = (220, 240, 220)
COR_BORDA_DESTAQUE: Tuple[int, int, int] = (150, 200, 150)

COR_FUNDO_TABELA_HEADER: Tuple[int, int, int] = (240, 240, 240)
COR_FUNDO_TABELA_DADOS: Tuple[int, int, int] = (255, 255, 255)
COR_BORDA_TABELA: Tuple[int, int, int] = (180, 180, 180)

# --- FONTES (fpdf2 built-in: Helvetica = equivalente a Arial) ---
FONTE_TITULO = "Helvetica"
FONTE_CORPO = "Helvetica"

# --- DIMENSÕES DA PÁGINA (A4 em mm) ---
PAGE_WIDTH = 210
PAGE_HEIGHT = 297
MARGIN_LEFT = 15
MARGIN_RIGHT = 15
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

# --- LARGURAS DAS COLUNAS DA TABELA (mm) ---
TABELA_COLUNAS = {
    "Categoria": 50,
    "Peso Total (t)": 38,
    "CO2 Evitado (t CO2e)": 42,
    "% do Total": 30,
}

# --- TEXTOS PADRONIZADOS ---
TEXTO_TITULO_RELATORIO = "RELATÓRIO VERDE"
TEXTO_ORGANIZACAO = "ACAMARTI"
TEXTO_FOOTER = "Relatório Gerado Automaticamente"
TEXTO_SECAO_DESTAQUE = "TOTAL DE CO2 EQUIVALENTE EVITADO"
TEXTO_SECAO_EXPLICACAO = "O Poder da Ação Verde: Traduzindo o CO2 Evitado"
TEXTO_SECAO_EQUIVALENCIAS = "O que o seu trabalho representa na prática:"
TEXTO_SECAO_TABELA = "Detalhe do CO2 Evitado por Tipo de Material"
TEXTO_SECAO_GRAFICO = "Visualização: CO2 Evitado (t CO2e) por Categoria"
TEXTO_SECAO_NAO_CLASSIFICADOS = "Materiais Não Classificados"
TEXTO_SECAO_METADADOS = "Metadados da Execução"

TEXTO_EXPLICATIVO = (
    "O CO2 equivalente (CO2e) é uma métrica que unifica o impacto de diferentes gases "
    "de efeito estufa em uma única unidade. Cada tonelada de material reciclado evita "
    "a emissão de gases que ocorreria na produção de matéria-prima virgem, extração de "
    "recursos naturais e destinação em aterros sanitários. O valor apresentado neste "
    "relatório representa a contribuição ambiental direta do processo de triagem e "
    "comercialização dos materiais recicláveis processados pela ACAMARTI."
)

TEXTO_IMPACTO_GENERICO = (
    "Sua ação combate diretamente o Aquecimento Global e reduz a poluição ambiental."
)

# --- TEMPLATES DE TEXTO DE EQUIVALÊNCIA ---
TEMPLATE_CARROS = (
    "Isso equivale a retirar de circulação aproximadamente {:,} carros "
    "de passeio por um ano inteiro."
)

TEMPLATE_RESIDENCIAS = (
    "Isso neutraliza o consumo de energia de mais de {:,} residencias " "por um mes."
)

_UNICODE_TO_ASCII = {
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "\u2022": "*",  # bullet
    "\u2713": "OK",  # check mark
    "\u2717": "X",  # ballot x
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
}


def sanitize_pdf_text(text: str) -> str:
    """
    Substitui caracteres Unicode incompativeis com fontes core do FPDF2
    (Latin-1 / Helvetica) por equivalentes ASCII seguros.
    """
    for uni_char, ascii_replacement in _UNICODE_TO_ASCII.items():
        text = text.replace(uni_char, ascii_replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")
