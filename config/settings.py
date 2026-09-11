import os
import locale
import logging
import logging.handlers

# --- CONFIGURAÇÃO DE LOCALIZAÇÃO ---
# Evita alterar LC_NUMERIC: Tk/CustomTkinter espera ponto decimal em dimensões
# internas (ex.: "270.0"), mesmo quando datas/textos usam locale brasileiro.
for _locale_name in ("pt_BR.utf8", "pt_BR.UTF-8", "Portuguese_Brazil.1252"):
    try:
        locale.setlocale(locale.LC_TIME, _locale_name)
        locale.setlocale(locale.LC_COLLATE, _locale_name)
        locale.setlocale(locale.LC_CTYPE, _locale_name)
        break
    except locale.Error:
        continue

try:
    locale.setlocale(locale.LC_NUMERIC, "C")
except locale.Error:
    pass  # Opcional: logar warning futuramente se necessário

# --- MODO DEBUG CONFIGURÁVEL ---
# Ativo por padrão se ECOMETRIC_DEBUG for True, 1 ou yes. Caso contrário, inativo.
DEBUG = os.getenv("ECOMETRIC_DEBUG", "False").lower() in ("true", "1", "yes")

# --- FATORES DE CO2 (t CO2e / t material) ---
FATORES_CO2 = {
    "PLÁSTICO": 2.128,
    "PAPEL": 1.348,
    "METAL": 1.759,
    "VIDRO": 0.354,
    "ELETROELETRÔNICO": 1.440,
    "COMPOSTO": 0.17,
}

# --- LISTA DOS MESES EM PT-BR ---
MESES_POSSIVEIS = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]

# --- CONSTANTES DE EQUIVALÊNCIA ---
FATOR_CARRO_ANO = 2.1  # Equivalência de CO2 por carro/ano (exemplo histórico)
FATOR_RESIDENCIA_MES = (
    0.15  # Equivalência de CO2 por residência/mês (exemplo histórico)
)

# --- COLUNAS PADRONIZADAS ---
COLUNAS_RESULTADO = ["Categoria", "Peso Total (t)", "CO2 Evitado (t CO2e)"]

# --- CONFIGURAÇÃO DE LOGGING PADRÃO ---
LOG_LEVEL = logging.DEBUG if DEBUG else logging.WARNING

_DIR_LOG = os.path.join(
    os.getenv("APPDATA", os.path.expanduser("~")), "EcoMetric", "logs"
)
os.makedirs(_DIR_LOG, exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            os.path.join(_DIR_LOG, "ecometric.log"),
            maxBytes=1_048_576,
            backupCount=5,
            encoding="utf-8",
        ),
    ],
)
