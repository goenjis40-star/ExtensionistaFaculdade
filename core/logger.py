import logging

logger = logging.getLogger("EcoMetric")


def log_debug(msg: str):
    """Loga mensagens de depuracao."""
    logger.debug(msg)


def log_info(msg: str):
    """Loga mensagens informativas gerais."""
    logger.info(msg)


def log_warning(msg: str):
    """Loga mensagens de aviso (warnings)."""
    logger.warning(msg)


def log_error(msg: str):
    """Loga erros graves."""
    logger.error(msg)
