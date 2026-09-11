import os
from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional
from decimal import Decimal

from config.settings import DEBUG, FATORES_CO2
from core.categorias import normalizar_categoria_generica, classificar_material_antigo
from core.constants import MODELO_CATAFACIL, MODELO_ANTIGO, MODELO_CONSOLIDADO
from core.logger import log_info, log_error, log_warning


def exportar_para_excel(
    df_consolidado: pd.DataFrame,
    df_bruto: pd.DataFrame,
    caminho_arquivo_pdf: str,
    modelo_detectado: str,
    tempo_execucao_segundos: float,
    caminho_saida_excel: str,
    df_mensal: Optional[pd.DataFrame] = None,
    auditoria_periodo: Optional[Dict] = None,
    insights: Optional[Dict] = None,
) -> bool:
    """
    Exporta os resultados do processamento do EcoMetric para uma planilha Excel multi-abas estruturada.

    Abas geradas:
    1. Consolidado: Categoria, Peso Total (t), CO2 Evitado (t CO2e)
    2. Dados_Brutos: Material, Peso
    3. Materiais_Nao_Classificados: Material, Peso, Motivo
    4. Auditoria: Estatísticas e metadados de execução do pipeline
    5. Metadata: Informações extras para integrações, dashboards e APIs futuras
    """
    log_info(f"Iniciando exportação para Excel: '{caminho_saida_excel}'")

    try:
        # Garante a existência do diretório de destino
        diretorio_destino = os.path.dirname(os.path.abspath(caminho_saida_excel))
        os.makedirs(diretorio_destino, exist_ok=True)

        lista_nao_classificados = []
        qtd_classificados = 0
        qtd_descartados = 0

        if not df_bruto.empty:
            for _, row in df_bruto.iterrows():
                material = row["Material"]
                peso = row["Peso"]

                # Classifica usando a heurística correspondente ao modelo do PDF
                if modelo_detectado == MODELO_CATAFACIL:
                    cat = normalizar_categoria_generica(material)
                    nao_classificado = cat is None
                    motivo = "Sem correspondência nas regras de categorias genéricas"
                elif modelo_detectado == MODELO_ANTIGO:
                    cat = classificar_material_antigo(material)
                    nao_classificado = cat == "NÃO CLASSIFICADO" or cat is None
                    motivo = "Sem correspondência nas prioridades ou regexes do modelo antigo"
                else:
                    cat = normalizar_categoria_generica(material)
                    nao_classificado = cat is None
                    motivo = "Sem correspondência nas regras de categorias genéricas"

                if nao_classificado:
                    # Converte Decimal para float para exportação Excel
                    peso_val = float(peso) if isinstance(peso, Decimal) else float(peso)
                    lista_nao_classificados.append(
                        {"Material": material, "Peso": peso_val, "Motivo": motivo}
                    )
                    qtd_descartados += 1
                else:
                    qtd_classificados += 1

        df_nao_classificados = pd.DataFrame(lista_nao_classificados)
        if df_nao_classificados.empty:
            df_nao_classificados = pd.DataFrame(columns=["Material", "Peso", "Motivo"])

        # Converte pesos da tabela bruta para float para compatibilidade no Excel
        df_bruto_export = df_bruto.copy()
        if not df_bruto_export.empty and "Peso" in df_bruto_export.columns:
            df_bruto_export["Peso"] = df_bruto_export["Peso"].apply(
                lambda x: float(x) if isinstance(x, Decimal) else x
            )

        dados_auditoria = {
            "Métrica": [
                "Arquivo processado",
                "Modelo detectado",
                "Parser utilizado",
                "Data/hora de processamento",
                "Tempo de execução",
                "Quantidade de linhas capturadas",
                "Quantidade de materiais classificados",
                "Quantidade de materiais descartados",
                "DEBUG ativo/inativo",
            ],
            "Valor": [
                os.path.basename(caminho_arquivo_pdf),
                modelo_detectado.upper(),
                (
                    "ConsolidacaoMultiPDF"
                    if modelo_detectado == MODELO_CONSOLIDADO
                    else (
                        "ParserPDFCatafacil"
                        if modelo_detectado == MODELO_CATAFACIL
                        else "ParserPDFAntigo"
                    )
                ),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                f"{tempo_execucao_segundos:.6f} segundos",
                len(df_bruto),
                qtd_classificados,
                qtd_descartados,
                "ATIVO (DEBUG=True)" if DEBUG else "INATIVO (DEBUG=False)",
            ],
        }
        df_auditoria = pd.DataFrame(dados_auditoria)

        dados_metadata = {
            "Chave": [
                "pipeline_name",
                "pipeline_version",
                "generated_by",
                "target_os",
                "factors_used_plastic",
                "factors_used_paper",
                "factors_used_metal",
                "factors_used_glass",
                "factors_used_eletro",
                "factors_used_composto",
            ],
            "Valor": [
                "EcoMetric Pipeline",
                "2.0.0-production",
                "Antigravity AI Engine",
                "Windows",
                str(FATORES_CO2.get("PLÁSTICO")),
                str(FATORES_CO2.get("PAPEL")),
                str(FATORES_CO2.get("METAL")),
                str(FATORES_CO2.get("VIDRO")),
                str(FATORES_CO2.get("ELETROELETRÔNICO")),
                str(FATORES_CO2.get("COMPOSTO")),
            ],
        }
        df_metadata = pd.DataFrame(dados_metadata)

        with pd.ExcelWriter(caminho_saida_excel, engine="openpyxl") as writer:
            df_consolidado.to_excel(writer, sheet_name="Consolidado", index=False)
            df_bruto_export.to_excel(writer, sheet_name="Dados_Brutos", index=False)
            df_nao_classificados.to_excel(
                writer, sheet_name="Materiais_Nao_Classificados", index=False
            )
            df_auditoria.to_excel(writer, sheet_name="Auditoria", index=False)
            df_metadata.to_excel(writer, sheet_name="Metadata", index=False)
            if df_mensal is not None and not df_mensal.empty:
                df_mensal.to_excel(writer, sheet_name="Evolucao_Mensal", index=False)
            if auditoria_periodo and auditoria_periodo.get("avisos"):
                linhas_audit = []
                if auditoria_periodo.get("meses_faltantes"):
                    for m in auditoria_periodo["meses_faltantes"]:
                        linhas_audit.append({"Tipo": "Meses Faltantes", "Descricao": m})
                if auditoria_periodo.get("meses_duplicados"):
                    for m in auditoria_periodo["meses_duplicados"]:
                        linhas_audit.append(
                            {"Tipo": "Meses Duplicados", "Descricao": m}
                        )
                if auditoria_periodo.get("anos_multiplos"):
                    linhas_audit.append(
                        {
                            "Tipo": "Anos Multiplos",
                            "Descricao": ", ".join(
                                str(a) for a in auditoria_periodo["anos_detectados"]
                            ),
                        }
                    )
                if linhas_audit:
                    df_audit_periodo = pd.DataFrame(linhas_audit)
                    df_audit_periodo.to_excel(
                        writer, sheet_name="Auditoria_Consolidacao", index=False
                    )
            if insights and not insights.get("sem_dados"):
                linhas_insights = []
                for chave, rotulo in [
                    ("peso_total", "Peso Total (t)"),
                    ("co2_total", "CO2 Total Evitado (t)"),
                    ("categoria_dominante", "Categoria Dominante"),
                    ("categoria_percentual", "Participacao da Categoria (%)"),
                    ("material_dominante", "Material Dominante"),
                    ("material_peso", "Peso Material Dominante (kg)"),
                    ("maior_mes", "Maior Mes (CO2)"),
                    ("maior_mes_co2", "CO2 Maior Mes (t)"),
                    ("menor_mes", "Menor Mes (CO2)"),
                    ("menor_mes_co2", "CO2 Menor Mes (t)"),
                ]:
                    if chave in insights:
                        linhas_insights.append(
                            {"Indicador": rotulo, "Valor": str(insights[chave])}
                        )
                if insights.get("top_5_materiais"):
                    for i, item in enumerate(insights["top_5_materiais"], 1):
                        mat = item["material"]
                        pes = item["peso_kg"]
                        linhas_insights.append(
                            {
                                "Indicador": f"Top {i} Material",
                                "Valor": f"{mat} ({pes:.1f} kg)",
                            }
                        )
                if linhas_insights:
                    df_insights = pd.DataFrame(linhas_insights)
                    df_insights.to_excel(writer, sheet_name="Insights", index=False)

        abas = 5
        if df_mensal is not None and not df_mensal.empty:
            abas += 1
        if auditoria_periodo and auditoria_periodo.get("avisos"):
            abas += 1
        if insights and not insights.get("sem_dados"):
            abas += 1
        log_info(
            f"Excel exportado com sucesso contendo {abas} abas em: '{caminho_saida_excel}'"
        )
        return True

    except ImportError:
        log_error(
            "[ERRO] Erro ao exportar para Excel: biblioteca 'openpyxl' não instalada."
        )
        return False
    except Exception as e:
        log_error(f"[ERRO] Erro inesperado ao gravar planilha Excel: {e}")
        return False
