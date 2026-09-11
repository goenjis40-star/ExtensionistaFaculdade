# EcoMetric 2.0 — PDF Report Implementation Plan

**Data:** 13/06/2026
**Status:** Planejamento para implementação imediata

---

## 1. Arquitetura Proposta

```
reports/
├── __init__.py              # (será criado) Torna reports/ um pacote Python
├── templates.py             # Constantes de estilo, helpers de formatação, estrutura do relatório
├── charts.py                # Geração de gráfico de barras (matplotlib)
└── pdf_generator.py         # Geração do PDF (fpdf2) — ponto de entrada público
```

### 1.1 Fluxo de dados

```
Pipeline Core
    │
    ├── df_consolidado (Categoria, Peso Total (t), CO2 Evitado (t CO2e))
    ├── df_bruto (Material, Peso)
    │
    ▼
pdf_generator.py
    │
    ├── Calcula CO2 total
    ├── Calcula equivalências (carros, residências)
    ├── Identifica materiais não classificados
    │
    ├── charts.py ──> gera gráfico de barras (PNG temporário)
    │
    └── templates.py ──> constantes de cores, fontes, layout
    │
    ▼
Relatório PDF (A4)
```

### 1.2 Estrutura do PDF

```
Página 1:
┌──────────────────────────────────────────┐
│ HEADER: RELATÓRIO VERDE - ACAMARTI       │
├──────────────────────────────────────────┤
│ DESTAQUE: CO2 Total Evitado (t CO2e)     │
│ (caixa verde com borda)                  │
├──────────────────────────────────────────┤
│ TEXTO: "O Poder da Ação Verde"           │
│ Parágrafo explicativo sobre CO2e         │
├──────────────────────────────────────────┤
│ EQUIVALÊNCIAS:                           │
│ • Carros de passeio retirados/ano        │
│ • Residências neutralizadas/mês          │
├──────────────────────────────────────────┤
│ TABELA: Detalhe por Categoria            │
│ Categoria | Peso (t) | CO2 (t) | %       │
│ ...                                      │
│ TOTAL                                    │
├──────────────────────────────────────────┤
│ GRÁFICO: Barras por Categoria (opcional) │
├──────────────────────────────────────────┤
│ MATERIAIS NÃO CLASSIFICADOS              │
│ Material | Peso (kg)                     │
├──────────────────────────────────────────┤
│ METADADOS DA EXECUÇÃO                    │
│ Arquivo, modelo, parser, tempo           │
├──────────────────────────────────────────┤
│ FOOTER: Página X | Gerado Automaticamente│
└──────────────────────────────────────────┘
```

---

## 2. Dependências

| Biblioteca | Versão | Uso |
|-----------|--------|-----|
| `fpdf2` | 2.8.7 | Geração do PDF |
| `matplotlib` | 3.11.0 | Gráfico de barras |
| `Pillow` | 12.2.0 | Suporte a imagens no fpdf2 |
| `pandas` | 3.0.3 | Consumo de DataFrames |

---

## 3. APIs Públicas

### 3.1 `gerar_relatorio_pdf()` — ponto de entrada principal

```python
def gerar_relatorio_pdf(
    df_consolidado: pd.DataFrame,
    df_bruto: pd.DataFrame,
    caminho_saida: str,
    modelo_detectado: str = "desconhecido",
    caminho_pdf_original: str = "",
    tempo_execucao: float = 0.0,
    incluir_grafico: bool = True,
) -> str:
```

**Parâmetros:**
- `df_consolidado` — DataFrame com colunas `['Categoria', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']`
- `df_bruto` — DataFrame com colunas `['Material', 'Peso']`
- `caminho_saida` — Caminho completo do PDF a ser gerado
- `modelo_detectado` — `"catafacil"` ou `"antigo"`
- `caminho_pdf_original` — Nome do PDF de origem (para metadata)
- `tempo_execucao` — Tempo de processamento em segundos
- `incluir_grafico` — Se True, inclui gráfico de barras

**Retorno:** Caminho absoluto do PDF gerado.

**Exceções:** Propaga exceções de I/O e bibliotecas externas.

### 3.2 `gerar_grafico_barras()` — gráfico

```python
def gerar_grafico_barras(
    df_consolidado: pd.DataFrame,
    caminho_saida: str,
) -> str:
```

### 3.3 Templates (constantes)

```python
# reports/templates.py
CORES_CATEGORIA: Dict[str, str]       # Cores por categoria para o gráfico
CORES_PDF: Dict[str, Tuple[int,...]]  # Cores para elementos do PDF
FONTE_PADRAO: str                      # "Helvetica" (equivalente Arial no fpdf2)
ESTILOS_TABELA: Dict                  # Configurações de tabela
```

---

## 4. Integração com GUI

A GUI (`gui/app.py`) pode ser estendida com um botão adicional:

```python
# Exemplo de integração futura (NÃO implementado agora):
btn_export_pdf = ctk.CTkButton(
    text="📄 Exportar PDF",
    command=self._export_pdf,
)
```

A função de callback na GUI seria:

```python
def _export_pdf(self):
    save_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Documento PDF", "*.pdf")],
        title="Salvar Relatório PDF",
    )
    if save_path:
        from reports.pdf_generator import gerar_relatorio_pdf
        gerar_relatorio_pdf(
            self.df_consolidado, self.df_bruto,
            save_path, self.modelo_detectado,
            self.current_pdf_path, self.tempo_execucao,
        )
```

**A GUI existente NÃO será alterada nesta fase.** A integração é documentada como referência.

---

## 5. Integração com Exportador Excel

Ambos (`exportador.py` e `pdf_generator.py`) consomem os mesmos DataFrames e produzem artefatos de saída. Eles são **independentes** e podem coexistir. Um pipeline típico seria:

```
processar_relatorio_pdf(pdf)
    └── (df_consolidado, df_bruto)
        ├── exportar_para_excel(...)  → .xlsx
        └── gerar_relatorio_pdf(...)  → .pdf
```

---

## 6. Riscos

| Risco | Mitigação |
|-------|-----------|
| `matplotlib` usa backend interativo em ambiente headless | Usar `matplotlib.use('Agg')` antes de importar pyplot |
| fpdf2 não suporta Arial (fonte proprietária) | Usar `Helvetica` (métrica equivalente, built-in no PDF) |
| Caracteres acentuados (pt-BR) em fontes built-in | Helvetica suporta Latin-1; OK para português |
| Gráfico temporário não é removido em caso de erro | Usar `try/finally` com `os.unlink()` |
| DataFrame vazio causa divisão por zero | Validar no início da função |
| Caminho de saída com diretório inexistente | Criar com `os.makedirs(exist_ok=True)` |

---

## 7. Estimativa

| Módulo | Linhas estimadas | Complexidade |
|--------|-----------------|--------------|
| `reports/__init__.py` | 3 | Trivial |
| `reports/templates.py` | 50 | Baixa |
| `reports/charts.py` | 60 | Média |
| `reports/pdf_generator.py` | 250 | Média-Alta |

---

## 8. Regras de Ouro (não violar)

- ✓ Não alterar `core/` — consumir apenas
- ✓ Não alterar testes existentes — adicionar novos se necessário
- ✓ Não alterar golden tests — snapshots intactos
- ✓ Não alterar GUI existente — integração futura documentada
- ✓ Não duplicar lógica de cálculo — usar `config.settings` para fatores
- ✓ Usar DataFrames já produzidos pelo pipeline
