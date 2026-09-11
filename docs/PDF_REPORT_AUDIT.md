# EcoMetric 2.0 — PDF Report Generation Audit

**Data:** 13/06/2026
**Auditor:** Inspeção do código-fonte + verificação de dependências

---

## 1. Estado Atual

### 1.1 Arquivos existentes

| Arquivo | Conteúdo | Status |
|---------|----------|--------|
| `reports/pdf_generator.py` | 0 linhas | **Stub vazio** |
| `reports/charts.py` | 0 linhas | **Stub vazio** |
| `reports/templates.py` | 0 linhas | **Stub vazio** |
| `reports/__init__.py` | Não existe | **Pacote não formal** |

### 1.2 Verificação de geração de PDF no código

| Local | Referência a PDF? |
|-------|-------------------|
| `core/exportador.py` | **Não** — apenas Excel |
| `main.py` | **Não** — apenas imprime DataFrames no console |
| `gui/app.py` | **Não** — apenas botão "Exportar para Excel" |
| `core/parsers/` | **Não** — leem PDFs, não geram |

### 1.3 Dependências de geração de PDF

| Biblioteca | Instalada? | No requirements.txt legado? |
|-----------|-----------|---------------------------|
| `fpdf` (legacy) | ✗ | ✓ (v1.7.2) |
| `fpdf2` | ✓ (v2.8.7) — instalada agora | ✓ (v2.8.7) |
| `matplotlib` | ✓ (v3.11.0) — instalada agora | ✓ (v3.10.8) |
| `reportlab` | ✗ | ✗ |
| `weasyprint` | ✗ | ✗ |
| `Pillow` | ✓ (v12.2.0) | ✓ (v12.1.1) |

---

## 2. Análise do Legado

O legado (`EcoMetric/relatorioverde.py`) possui um sistema completo de geração de PDF com:

### 2.1 Estrutura do relatório (legado)

```
┌──────────────────────────────────────┐
│ HEADER: RELATÓRIO VERDE - ACAMARTI   │
├──────────────────────────────────────┤
│ DESTAQUE: Total CO2 Evitado (t)      │
│ Texto descritivo sobre impacto       │
│ Equivalências ambientais:            │
│   • Carros retirados/ano             │
│   • Residências neutralizadas/mês    │
├──────────────────────────────────────┤
│ TABELA: Materiais Recicláveis        │
│ Categoria | Peso (t) | CO2 (t) | %   │
├──────────────────────────────────────┤
│ GRÁFICO: Barras por Categoria        │
├──────────────────────────────────────┤
│ FOOTER: Página X | Gerado Auto.      │
└──────────────────────────────────────┘
```

### 2.2 Funções do legado não migradas

- `gerar_pdf()` — geração completa com CO2, tabelas, gráfico
- `gerar_relatorio_detalhado_pdf()` — tabela simplificada de pesos
- `gerar_graficos()` — gráfico de barras matplotlib
- `RelatorioPDF(FPDF)` — classe customizada com header/footer

---

## 3. Determinação

### Existe geração de PDF no EcoMetric 2.0?

**NÃO.** Zero implementação. Três stubs vazios.

### Está funcional?

**NÃO.** Inexistente.

### Está parcialmente implementada?

**NÃO.** Nenhuma linha de código.

### Está apenas planejada?

**SIM.** Os stubs indicam intenção de implementação futura.

---

## 4. O que o Pipeline Já Produz (disponível para consumo)

O core já gera DataFrames perfeitamente utilizáveis:

```python
# Do processar_relatorio_pdf():
df_consolidado: pd.DataFrame  # colunas: ['Categoria', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']
df_bruto: pd.DataFrame         # colunas: ['Material', 'Peso']
```

Constantes disponíveis em `config/settings.py`:
- `FATORES_CO2` — fatores de CO2 por categoria
- `FATOR_CARRO_ANO` — 2.1 t CO2e/carro/ano
- `FATOR_RESIDENCIA_MES` — 0.15 t CO2e/residência/mês

---

## 5. Conclusão

A geração de relatórios PDF é a **funcionalidade mais crítica ainda não migrada** do legado para a v2.0. A migração é viável porque:

- O pipeline já produz todos os dados necessários
- As bibliotecas (`fpdf2`, `matplotlib`) estão disponíveis
- O formato do relatório legado é bem documentado
- Os contratos do core não precisam ser alterados

**Recomendação:** Implementar imediatamente.
