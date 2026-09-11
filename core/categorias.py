import re
from typing import Dict, Optional, Union, List, Tuple
from config.settings import FATORES_CO2

# --- COMPILAÇÃO DOS REGEXES EM ORDEM EXPLÍCITA (PRESERVA COMPATIBILIDADE) ---
# A ordem das tuplas na lista é idêntica à ordem de inserção do dicionário legado.
# Isso garante que "SUCATA CELULAR" dê match em ELETROELETRÔNICO antes de SUCATA dar match em METAL.
MAPA_CATEGORIAS_REGEX: List[Tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"\bSUCATA CELULAR\b|\bBATERIA\b|\bPLACA MARROM\b|\bPLACA VERDE\b|\bTV\b|\bCHUVEIRO\b|\bMEMORIA\b|\bPLACA MÃE\b",
            re.IGNORECASE,
        ),
        "ELETROELETRÔNICO",
    ),
    (
        re.compile(
            r"AEROSOL|ALUMINIO|ALUMÍNIO|ANTIMONIO|CHAPARIA|COBRE|FERRO|FIO INFORMATICA|MINERAL|MOTOR|PANELA|PERFIL|RADIADOR|SUCATA|METAL",
            re.IGNORECASE,
        ),
        "METAL",
    ),
    (
        re.compile(
            r"BALDE|BACIA|BLOCO S/|CAIXA DE TV|CAIXA ENGRADADO|PET|COLORIDO|COPINHO|CRISTAL|FITA|ISOPOR|LEITOSO|PP CAIXARIA|PVC|RAFIA|RÁFIA|SACO PRETO|SACOLINHA|BAG|FILME|BOMBONA|TAMPINHA",
            re.IGNORECASE,
        ),
        "PLÁSTICO",
    ),
    (re.compile(r"APARAS|CIMENTO|PAPEL|BUBINA", re.IGNORECASE), "PAPEL"),
    (
        re.compile(
            r"GARRAFAO|GARRAFINHA|LITRO PINGA|TREZENTINHA|VIDRO|CONSERVA", re.IGNORECASE
        ),
        "VIDRO",
    ),
    (re.compile(r"COMPOSTO|OLEO", re.IGNORECASE), "COMPOSTO"),
]

# --- KEYWORDS DE PRIORIDADE E FILTROS ---
PRIORIDADE_PLASTICO: List[str] = ["CAIXA DE TV", "FILME", "AZUL", "PLASTICO", "SACO"]
FILTROS_SERVICO: List[str] = [
    "SERVICO",
    "TRIAGEM",
    "COLETA",
    "TOTAL",
    "VALOR",
    "DATA:",
    "PÁGINA",
]


def normalizar_categoria_generica(
    nome_raw: Optional[Union[str, float, int]],
    fator_co2_map: Optional[Dict[str, float]] = None,
) -> Optional[str]:
    """
    Classifica um material em uma das categorias normais do sistema.

    Esta função reproduz exatamente a lógica de '_normalizar_categoria_generica' do legado:
    1. Retorna None se o nome for nulo ou vazio.
    2. Faz lookup direto (case-insensitive para chaves uppercase) no mapa de fatores de CO2.
    3. Se não houver lookup direto, realiza buscas sequenciais pelas expressões regulares mapeadas.
    4. Retorna a categoria formatada em Title Case (ex: "Plástico", "Eletroeletrônico") ou None.

    Atenção: Não aplica a prioridade de plástico do parser antigo, mantendo a assimetria intencional.
    """
    if nome_raw is None:
        return None

    nome = str(nome_raw).strip()
    if not nome:
        return None

    nome_upper = nome.upper()

    # Se não for passado o mapa, usa o padrão do sistema
    mapa_fatores = fator_co2_map if fator_co2_map is not None else FATORES_CO2

    # 1. Match direto no mapa de fatores de CO2
    if nome_upper in mapa_fatores:
        return nome_upper.title()

    # 2. Busca sequencial por expressões regulares na ordem exata de precedência
    for pattern, destino in MAPA_CATEGORIAS_REGEX:
        if pattern.search(nome_upper):
            return destino.title()

    return None


def classificar_material_antigo(
    mat_raw: str, fator_co2_map: Optional[Dict[str, float]] = None
) -> str:
    """
    Aplica a lógica de classificação específica do Parser Antigo.

    O Parser Antigo possui um comportamento assimétrico crítico em relação ao CataFácil e Excel:
    1. Verifica a prioridade de plástico: se alguma keyword contida em PRIORIDADE_PLASTICO
       estiver contida no nome do material, ele é forçado para 'PLÁSTICO'.
    2. Se não der match na prioridade, percorre as regexes do MAPA_CATEGORIAS_REGEX na ordem exata.
    3. Se não encontrar nenhuma classificação, retorna 'NÃO CLASSIFICADO' (em vez de None).
    """
    mat = str(mat_raw).strip().upper()

    # 1. PRIORIDADE PLÁSTICO (Comportamento Legado Crítico)
    # Adicionado 'AZUL' e 'FILME' etc para bater com o legado histórico
    if any(keyword in mat for keyword in PRIORIDADE_PLASTICO):
        return "PLÁSTICO"

    # 2. Busca sequencial por expressões regulares na ordem exata
    for pattern, destino in MAPA_CATEGORIAS_REGEX:
        if pattern.search(mat):
            return destino

    return "NÃO CLASSIFICADO"
