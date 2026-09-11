import sys
import os
import time
import tracemalloc
import pandas as pd

# Adiciona o diretório EcoMetric 2.0 no Python Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.parsers import processar_relatorio_pdf
from core.parsers.detector import detectar_modelo_pdf


def format_bytes(size: int) -> str:
    """Formata bytes de forma legível (KB/MB)."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"


def run_benchmarks():
    """
    Executa testes de performance e consumo de memória (diagnóstico completo).
    Mede tempo de processamento com precisão e pico de memória com o módulo nativo tracemalloc.
    Valida toda a suite contra os relatórios mensais reais da pasta legada.
    """
    print("=" * 70)
    print("          BENCHMARK DE PERFORMANCE & CONSUMO DE MEMÓRIA - ECOMETRIC 2.0")
    print("=" * 70)

    diretorio_legado = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "EcoMetric")
    )
    if not os.path.exists(diretorio_legado):
        print(f"[ERRO] Diretório legado não encontrado: '{diretorio_legado}'")
        sys.exit(1)

    arquivos_pdf = sorted(
        [
            os.path.join(diretorio_legado, f)
            for f in os.listdir(diretorio_legado)
            if f.endswith(".pdf")
        ]
    )

    if not arquivos_pdf:
        print("[ERRO] Nenhum PDF real encontrado para benchmark.")
        sys.exit(1)

    resultados = []

    print(f"\nIniciando testes em {len(arquivos_pdf)} arquivos de relatórios reais...")

    for idx, pdf_path in enumerate(arquivos_pdf, start=1):
        nome_base = os.path.basename(pdf_path)

        # Inicia medição de memória
        tracemalloc.start()
        tracemalloc.reset_peak()

        # Inicia medição de tempo
        tempo_inicio = time.perf_counter()

        try:
            # Detecta o modelo
            modelo = detectar_modelo_pdf(pdf_path)

            # Processa o PDF
            df_cons, df_bruto = processar_relatorio_pdf(pdf_path)

            tempo_fim = time.perf_counter()
            tempo_decorrido_ms = (tempo_fim - tempo_inicio) * 1000

            # Obtém pico de memória consumido no bloco
            _, memoria_pico = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            resultados.append(
                {
                    "PDF": nome_base,
                    "Modelo": modelo.upper(),
                    "Tempo (ms)": tempo_decorrido_ms,
                    "Memória Pico": memoria_pico,
                    "Status": "SUCESSO",
                }
            )

            print(
                f"  [{idx:02d}/{len(arquivos_pdf):02d}] {nome_base:<45} | Modelo: {modelo.upper():<10} | Tempo: {tempo_decorrido_ms:.2f} ms | Memória Pico: {format_bytes(memoria_pico)}"
            )

        except Exception as e:
            tracemalloc.stop()
            resultados.append(
                {
                    "PDF": nome_base,
                    "Modelo": "DESCONHECIDO",
                    "Tempo (ms)": 0,
                    "Memória Pico": 0,
                    "Status": f"FALHA ({e})",
                }
            )
            print(
                f"  [{idx:02d}/{len(arquivos_pdf):02d}] {nome_base:<45} | FALHOU: {e}"
            )

    # Exibe Relatório Consolidado Final
    print("\n" + "=" * 30 + " RELATÓRIO FINAL DE BENCHMARK " + "=" * 30)
    df_res = pd.DataFrame(resultados)

    # Formata resultados numéricos
    df_res_print = df_res.copy()
    df_res_print["Tempo (ms)"] = df_res_print["Tempo (ms)"].apply(
        lambda x: f"{x:.2f} ms"
    )
    df_res_print["Memória Pico"] = df_res_print["Memória Pico"].apply(format_bytes)

    print(df_res_print.to_string(index=False))

    # Estatísticas gerais
    df_sucesso = df_res[df_res["Status"] == "SUCESSO"]
    if not df_sucesso.empty:
        tempo_medio = df_sucesso["Tempo (ms)"].mean()
        tempo_max = df_sucesso["Tempo (ms)"].max()
        mem_pico_media = df_sucesso["Memória Pico"].mean()
        mem_pico_max = df_sucesso["Memória Pico"].max()

        print("\n" + "-" * 35 + " ESTATÍSTICAS GERAIS " + "-" * 35)
        print(f"  - Tempo Médio de Processamento: {tempo_medio:.2f} ms")
        print(f"  - Tempo Máximo de Processamento: {tempo_max:.2f} ms")
        print(
            f"  - Média de Consumo de Pico de Memória: {format_bytes(mem_pico_media)}"
        )
        print(
            f"  - Consumo de Pico de Memória Máximo Registrado: {format_bytes(mem_pico_max)}"
        )

    print("=" * 90)


if __name__ == "__main__":
    run_benchmarks()
