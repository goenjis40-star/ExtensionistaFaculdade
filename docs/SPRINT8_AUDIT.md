# Sprint 8 — Auditoria Pré-Implementação

**Data:** 13/06/2026

## Estruturas disponíveis
- `df_consolidado`: Categoria, Peso Total (t), CO2 Evitado (t CO2e)
- `df_bruto`: Material, Peso, Origem
- `df_mensal`: Periodo, Arquivo, Peso Total (t), CO2 Evitado (t CO2e)

## Pontos de integração
- `reports/pdf_generator.py` — gerar_relatorio_pdf() e gerar_relatorio_anual()
- `core/exportador.py` — exportar_para_excel() (parâmetro insights opcional)
- `core/insights.py` — NOVO módulo

## Estratégia
- `gerar_insights()` recebe os 3 DataFrames e retorna dict
- PDF: nova seção "Insights Automáticos" após resumo executivo
- Excel: nova aba "Insights" opcional
- PDF anual: adicionar gráfico de categorias (já existe em charts.py)
