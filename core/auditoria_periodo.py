from collections import Counter
from typing import List, Dict

from config.settings import MESES_POSSIVEIS
from core.utils_periodo import normalizar_periodo


def auditar_periodos(info_list: List[Dict]) -> Dict:
    """
    Analisa os periodos detectados na consolidacao e gera diagnosticos.

    Args:
        info_list: Lista de dicts com chave 'periodo' de cada PDF processado

    Returns:
        Dict com:
        - periodo_completo: bool — True se todos os meses entre min e max estao presentes
        - meses_faltantes: List[str] — periodos esperados mas ausentes
        - meses_duplicados: List[str] — periodos que aparecem mais de uma vez
        - anos_detectados: List[int] — anos encontrados (ordenados)
        - anos_multiplos: bool — True se ha mais de um ano
        - quantidade_meses: int — total de periodos unicos com mes
        - quantidade_arquivos: int — total de PDFs processados
        - avisos: List[str] — mensagens descritivas
    """
    periodos_raw = []
    for item in info_list:
        p = item.get("periodo", "")
        if p and p not in ("Nao detectado", "?"):
            periodos_raw.append(p)

    if not periodos_raw:
        return {
            "periodo_completo": False,
            "meses_faltantes": [],
            "meses_duplicados": [],
            "anos_detectados": [],
            "anos_multiplos": False,
            "quantidade_meses": 0,
            "quantidade_arquivos": len(info_list),
            "avisos": ["Nenhum periodo detectado nos PDFs processados."],
        }

    normalizados = []
    for p in periodos_raw:
        mes, ano = normalizar_periodo(p)
        if mes > 0 and ano > 0:
            normalizados.append((mes, ano, p))

    if not normalizados:
        return {
            "periodo_completo": False,
            "meses_faltantes": [],
            "meses_duplicados": [],
            "anos_detectados": [],
            "anos_multiplos": False,
            "quantidade_meses": 0,
            "quantidade_arquivos": len(info_list),
            "avisos": ["Periodos detectados, mas nao foi possivel extrair mes e ano."],
        }

    anos_set = sorted(set(a for _, a, _ in normalizados))
    anos_multiplos = len(anos_set) > 1

    contagem = Counter((m, a) for m, a, _ in normalizados)
    duplicados_raw = [(m, a) for (m, a), c in contagem.items() if c > 1]
    meses_duplicados = []
    for m, a in duplicados_raw:
        nome_mes = MESES_POSSIVEIS[m - 1] if 1 <= m <= 12 else f"Mes {m}"
        meses_duplicados.append(f"{nome_mes} {a}")

    meses_presentes = set((m, a) for m, a, _ in normalizados)
    meses_faltantes = []

    for ano in anos_set:
        meses_do_ano = sorted(m for m, a in meses_presentes if a == ano)
        if not meses_do_ano:
            continue
        mes_min = meses_do_ano[0]
        mes_max = meses_do_ano[-1]
        for m in range(mes_min, mes_max + 1):
            if (m, ano) not in meses_presentes:
                nome_mes = MESES_POSSIVEIS[m - 1] if 1 <= m <= 12 else f"Mes {m}"
                meses_faltantes.append(f"{nome_mes} {ano}")

    qtd_meses_unicos = len(set((m, a) for m, a, _ in normalizados))
    periodo_completo = len(meses_faltantes) == 0 and not anos_multiplos

    avisos = []
    if meses_faltantes:
        avisos.append(
            f'{len(meses_faltantes)} mes(es) faltante(s): {", ".join(meses_faltantes[:5])}'
            + ("..." if len(meses_faltantes) > 5 else "")
        )
    if meses_duplicados:
        avisos.append(
            f'{len(meses_duplicados)} mes(es) duplicado(s): {", ".join(meses_duplicados[:5])}'
            + ("..." if len(meses_duplicados) > 5 else "")
        )
    if anos_multiplos:
        avisos.append(f"Multiplos anos detectados: {anos_set}")

    return {
        "periodo_completo": periodo_completo,
        "meses_faltantes": meses_faltantes,
        "meses_duplicados": meses_duplicados,
        "anos_detectados": anos_set,
        "anos_multiplos": anos_multiplos,
        "quantidade_meses": qtd_meses_unicos,
        "quantidade_arquivos": len(info_list),
        "avisos": avisos,
    }
