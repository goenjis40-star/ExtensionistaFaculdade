# Sprint 6 — Auditoria Pré-Implementação

**Data:** 13/06/2026

---

## 1. Estado Atual — Estruturas de Dados Reais

### `meta` (dict retornado por `consolidar_multiplos_pdfs`)

```python
{
    'modelo': 'CONSOLIDADO',
    'info_list': [{'arquivo': ..., 'modelo': ..., 'periodo': ..., ...}, ...],
    'df_mensal': DataFrame(columns=['Periodo', 'Arquivo', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']),
    'quantidade_pdfs': 2,
    'periodo_inicial': 'Maio 2026',
    'periodo_final': 'Maio 2026',
}
```

### `df_mensal` (n linhas, uma por PDF processado)

| Periodo | Arquivo | Peso Total (t) | CO2 Evitado (t CO2e) |
|---------|---------|---------------|---------------------|
| Maio 2026 | Relatorio Maio.pdf | 69.97 | 112.88 |

### `df_consolidado` — colunas padronizadas

```
['Categoria', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']
```

### `df_bruto` — colunas com Origem

```
['Material', 'Peso', 'Origem']
```

---

## 2. Pontos de Integração

| Módulo | Função atual | O que precisa |
|--------|-------------|---------------|
| `core/consolidacao.py` | `consolidar_multiplos_pdfs()` → 3-tuple | Já pronto (df_mensal, meta) |
| `core/exportador.py` | `exportar_para_excel(...)` → 6 params | + `df_mensal=None` param; nova aba |
| `reports/charts.py` | `gerar_grafico_barras()` (categoria) | + `gerar_grafico_co2_mensal()`, `gerar_grafico_peso_mensal()` |
| `reports/pdf_generator.py` | `gerar_relatorio_pdf()` (padrão) | + `gerar_relatorio_anual()` (nova função) |
| `gui/app.py` | `_process_worker`, `_export_excel`, `_export_pdf` | Armazenar `meta`, rotear anual |
| `core/utils_periodo.py` | — (não existe) | NOVO: normalizar/ordenar períodos |

---

## 3. Estratégia

### Etapa 2 — `core/utils_periodo.py`
- `normalizar_periodo("Maio 2026")` → tupla (5, 2026) para ordenação
- `ordenar_periodos(df)` → DataFrame ordenado cronologicamente

### Etapa 3 — Excel
- Adicionar `df_mensal=None` ao final da assinatura (default mantém compatibilidade)
- Se `df_mensal` não for None nem vazio, adicionar aba `Evolucao_Mensal`

### Etapa 4 — Gráficos
- `gerar_grafico_co2_mensal(df_mensal)` → barras verticais, eixo X = período, Y = CO2
- `gerar_grafico_peso_mensal(df_mensal)` → idem para peso
- Ambos usam matplotlib Agg, arquivo temp, limpeza automática

### Etapa 5 — PDF Anual
- Nova função `gerar_relatorio_anual()` no pdf_generator.py
- Reaproveita a classe `_RelatorioPDF`
- Seções: Capa, Resumo Executivo, Evolução Mensal, Gráficos, Consolidado

### Etapa 6 — GUI
- Armazenar `self.df_mensal` e `self.meta_consolidado` no worker
- `_export_pdf` roteia para `gerar_relatorio_anual()` se `modelo == CONSOLIDADO`
- `_export_excel` passa `df_mensal` se disponível

---

## 4. Riscos

| Risco | Mitigação |
|-------|-----------|
| `df_mensal` vazio quebra gráficos | Validar antes de gerar |
| Períodos com formato inconsistente | `normalizar_periodo` robusto com fallback |
| Nova assinatura quebra callers existentes | Usar `df_mensal=None` como default |
| Ordenação alfabética (Abril < Agosto < Dezembro) | Ordenação por tupla (mês_num, ano) |
