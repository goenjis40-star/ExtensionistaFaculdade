# EcoMetric 2.0 — Consolidação Multi-PDF

**Sprint:** 5
**Data:** 13/06/2026

---

## Estrutura Implementada

```
core/consolidacao.py          (novo — 182 linhas)
gui/components/dropzone.py    (modificado — +botão múltiplos PDFs)
gui/app.py                    (modificado — +consolidação no pipeline)
```

---

## API Pública

### `consolidar_multiplos_pdfs()`

```python
def consolidar_multiplos_pdfs(
    caminhos: List[str],
    fator_co2_map: Optional[Dict[str, float]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict]]:
```

**Entrada:** Lista de caminhos absolutos para PDFs.

**Saída:**
- `df_consolidado`: Soma de pesos e CO2 por categoria de todos os PDFs
- `df_bruto`: Concatenação de todas as linhas brutas, com coluna extra `Origem` indicando o PDF de origem
- `info`: Lista de metadados por PDF (arquivo, modelo, período, linhas, status)

### `detectar_periodo_pdf()` (interna)

Detecta mês/ano de um PDF via nome do arquivo e texto da primeira página.

### `detectar_periodo_consolidado()`

```python
def detectar_periodo_consolidado(info_list: List[Dict]) -> str:
```

Compõe string descritiva: ex: `"Janeiro a Dezembro 2025"`, `"Maio 2023"`.

---

## Fluxo na GUI

```
Usuário clica "📁 Múltiplos PDFs"
    │
    ├── filedialog.askopenfilenames(multiple=True)
    │
    ▼
_on_files_selected([pdf1, pdf2, ...])
    │
    ├── self.current_pdf_paths = [pdf1, pdf2, ...]
    ├── label: "📁 12 arquivos selecionados"
    │
    ▼
Usuário clica "Processar Relatório"
    │
    ▼
_process_worker()
    │
    ├── len(self.current_pdf_paths) > 1 ?
    │   ├── SIM: consolidar_multiplos_pdfs(paths)
    │   │   └── Para cada PDF:
    │   │       ├── detectar_modelo_pdf()
    │   │       ├── processar_relatorio_pdf()  (usa parser existente)
    │   │       ├── _detectar_periodo_pdf()
    │   │       └── Soma pesos por categoria (Decimal)
    │   │
    │   └── NÃO: processar_relatorio_pdf(path)  (single, unchanged)
    │
    ▼
_on_process_success()
    ├── Stats cards (peso, CO2, categorias)
    ├── Botões Excel e PDF habilitados
    └── Exportação funciona normalmente com df_consolidado total
```

---

## Detecção de Período

### Estratégia

1. **Nome do arquivo:** `"Relatorio Maio 2025.pdf"` → detecta "Maio" + "2025"
2. **Texto da primeira página do PDF:** busca por nomes de meses (`MESES_POSSIVEIS`) e anos (4 dígitos)
3. **Fallback:** retorna `None` se nada for detectado

### Exemplos

| Arquivo | Período detectado |
|---------|-------------------|
| `Relatorio Janeiro_bruto.csv` (nome original) | `Janeiro` |
| `Relatorio geral de vendas 2025.pdf` | `2025` |
| PDF sem mês/ano no nome ou texto | `Nao detectado` |

---

## Consolidação — Regras

| Operação | Como |
|----------|------|
| **df_bruto** | `pd.concat()` de todos os brutos, com coluna `Origem` |
| **df_consolidado** | Soma de `Peso Total (t)` por categoria (usando `Decimal`), recálculo de `CO2 Evitado` com `FATORES_CO2` |
| **Erro em PDF individual** | Capturado, registrado no `info_list`, não interrompe os demais |
| **Lista vazia** | Retorna DataFrames vazios |

---

## Compatibilidade

| Componente | Status |
|-----------|--------|
| Parsers (`pdf_antigo`, `pdf_catafacil`) | **Não alterados** — consumidos via `processar_relatorio_pdf()` |
| Exportador Excel | **Não alterado** — recebe os mesmos DataFrames consolidados |
| Gerador PDF | **Não alterado** — idem |
| GUI (single PDF) | **Preservado** — se 1 PDF selecionado, usa o fluxo original |
| Testes existentes | **37/37 passam** — zero regressões |

---

## Limitações Identificadas

| Limitação | Impacto |
|-----------|---------|
| Sem barra de progresso por PDF | Usuário não sabe quantos PDFs já foram processados até o fim |
| Sem paralelismo | PDFs processados sequencialmente (1 thread) |
| Detecção de período é heurística | Pode falhar com formatos de nome incomuns |
| Sem limite de PDFs | 100+ PDFs pode travar a UI (single thread) |
| `Origem` no df_bruto é o nome do arquivo | Colisão se dois PDFs tiverem o mesmo nome em pastas diferentes |
| Modelo "consolidado" no exportador | `exportador.py` usa `modelo_detectado` para escolher classificador; `"consolidado"` cai no `else` (antigo) |
