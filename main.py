import os
import sys
from typing import Tuple
import pandas as pd

DIRETORIO_CORRENTE = os.path.dirname(os.path.abspath(__file__))
if DIRETORIO_CORRENTE not in sys.path:
    sys.path.insert(0, DIRETORIO_CORRENTE)

from core.parsers.detector import detectar_modelo_pdf
from core.parsers import processar_relatorio_pdf
from core.logger import log_info, log_debug, log_error


def main():
    """
    Camada de execução manual CLI para o pipeline do EcoMetric 2.0.
    """
    print("=" * 60)
    print("           ECOMETRIC 2.0 - CLI DE EXECUCAO MANUAL")
    print("=" * 60)

    caminho_pdf = None
    if len(sys.argv) > 1:
        caminho_pdf = sys.argv[1]
    else:
        log_info("Nenhum arquivo PDF passado como argumento.")

        pasta_legado = os.path.abspath(
            os.path.join(DIRETORIO_CORRENTE, "..", "EcoMetric")
        )
        pdfs_disponiveis = []
        if os.path.exists(pasta_legado):
            pdfs_disponiveis = [
                f for f in os.listdir(pasta_legado) if f.endswith(".pdf")
            ]

        if pdfs_disponiveis:
            print("\nPDFs reais encontrados no diretorio legado para testar:")
            for idx, pdf in enumerate(pdfs_disponiveis, start=1):
                print(f"  {idx}. {pdf}")

            try:
                escolha = input(
                    f"\nEscolha o numero do PDF (1-{len(pdfs_disponiveis)}) ou digite o caminho de outro arquivo: "
                ).strip()
                if escolha.isdigit() and 1 <= int(escolha) <= len(pdfs_disponiveis):
                    caminho_pdf = os.path.join(
                        pasta_legado, pdfs_disponiveis[int(escolha) - 1]
                    )
                elif escolha:
                    caminho_pdf = escolha
            except (KeyboardInterrupt, SystemExit):
                log_info("Execucao cancelada pelo usuario.")
                sys.exit(0)

        if not caminho_pdf:
            log_error("Eh necessario informar o caminho do arquivo PDF.")
            print("Uso: python main.py <caminho_do_arquivo.pdf>")
            sys.exit(1)

    if not os.path.exists(caminho_pdf):
        log_error(f"Arquivo nao encontrado: '{caminho_pdf}'")
        sys.exit(1)

    log_debug(f"Arquivo selecionado: {os.path.basename(caminho_pdf)}")
    log_debug(f"Caminho absoluto: {os.path.abspath(caminho_pdf)}")

    try:
        modelo_detectado = detectar_modelo_pdf(caminho_pdf)
        log_debug(f"Modelo detectado automaticamente: '{modelo_detectado.upper()}'")
    except Exception as e:
        log_error(f"Falha ao detectar modelo do PDF: {e}")
        modelo_detectado = "desconhecido"

    log_debug("Iniciando processamento do pipeline...")
    try:
        df_consolidado, df_bruto = processar_relatorio_pdf(caminho_pdf)

        print("\n" + "=" * 25 + " RESULTADOS CONSOLIDADOS " + "=" * 25)
        if df_consolidado.empty:
            log_info(
                "DataFrame consolidado vazio (nenhum material valido foi categorizado ou mapeado)."
            )
        else:
            print(df_consolidado.to_string(index=False))

        print("\n" + "=" * 28 + " DADOS BRUTOS " + "=" * 28)
        if df_bruto.empty:
            log_info(
                "DataFrame bruto vazio (nenhum material foi extraido da leitura fisica)."
            )
        else:
            if len(df_bruto) <= 40:
                print(df_bruto.to_string(index=False))
            else:
                print(
                    f"[INFO] Exibindo primeiras 20 de {len(df_bruto)} linhas extraidas:"
                )
                print(df_bruto.head(20).to_string(index=False))

        print("=" * 70)
        log_info("Execucao concluida sem erros.")

    except Exception as e:
        log_error(f"Ocorreu uma falha grave ao processar o arquivo: {e}")
        print("\n" + "!" * 20 + " ERRO NO PROCESSAMENTO " + "!" * 20)
        print(f"Ocorreu uma falha grave ao processar o arquivo: {e}")
        print(
            "Certifique-se de que o arquivo PDF esta em formato valido ou possui permissao de leitura."
        )
        print("!" * 63)
        sys.exit(1)


if __name__ == "__main__":
    main()
