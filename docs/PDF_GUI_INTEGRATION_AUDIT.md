# EcoMetric 2.0 — PDF-GUI Integration & Log Duplication Audit

**Data:** 13/06/2026
**Auditor:** Inspeção de código + diagnóstico de handlers de logging

---

## 1. `reports/pdf_generator.py`

### 1.1 Existe?

**Sim.** `reports/pdf_generator.py` — 403 linhas. Implementado em 13/06/2026.

### 1.2 Está funcional?

**Sim.** Testado com geração real de PDF (31 KB). PDF contém header ACAMARTI, destaque CO2, equivalências, tabela, gráfico, materiais não classificados, metadados.

### 1.3 Assinatura pública

```python
def gerar_relatorio_pdf(
    df_consolidado: pd.DataFrame,       # ['Categoria', 'Peso Total (t)', 'CO2 Evitado (t CO2e)']
    df_bruto: pd.DataFrame,             # ['Material', 'Peso']
    caminho_saida: str,                 # Caminho completo do .pdf
    modelo_detectado: str = 'desconhecido',
    caminho_pdf_original: str = '',
    tempo_execucao: float = 0.0,
    incluir_grafico: bool = True,
) -> str:                               # Retorna caminho absoluto do PDF gerado
```

**Contratos consumidos:** `FATORES_CO2`, `FATOR_CARRO_ANO`, `FATOR_RESIDENCIA_MES` de `config.settings`. Nenhum contrato do core é alterado.

---

## 2. GUI — Estado Atual

### 2.1 Botão para gerar PDF?

**NÃO.** A GUI possui apenas um botão de exportação:

| Botão | Linha | Ação |
|-------|-------|------|
| "Processar Relatório" | `gui/app.py:212` | Executa pipeline |
| "Exportar para Excel" | `gui/app.py:233` | `filedialog` → `exportar_para_excel()` |

### 2.2 Menu para gerar PDF?

**NÃO.** A GUI não tem barra de menu (File, Edit, etc.).

### 2.3 Existe alguma chamada para `gerar_relatorio_pdf()`?

**NÃO.** Nenhuma referência a `reports`, `pdf_generator` ou `gerar_relatorio_pdf` em `gui/app.py`. O import não existe.

### 2.4 Importações atuais da GUI (linhas 48-51)

```python
from core.parsers import processar_relatorio_pdf
from core.parsers.detector import detectar_modelo_pdf
from core.exportador import exportar_para_excel
#                                          ← gerar_relatorio_pdf NÃO importado
```

---

## 3. Fluxo Atual — Onde Ficam os DataFrames?

Após processamento (`_process_worker` → `_on_process_success`), os dados ficam armazenados como atributos da instância `App`:

```python
# gui/app.py — classe App
self.df_consolidado = df_cons    # DataFrame: Categoria, Peso Total (t), CO2 Evitado (t CO2e)
self.df_bruto = df_bruto          # DataFrame: Material, Peso
self.current_pdf_path = filepath  # str: caminho do PDF original
self.modelo_detectado = modelo    # str: "catafacil" | "antigo"
self.tempo_execucao = tempo       # float: segundos
```

Todos os 5 parâmetros necessários para `gerar_relatorio_pdf()` já estão disponíveis como atributos de `self`.

---

## 4. Menor Implementação Necessária — Botão PDF na GUI

### 4.1 O que precisa ser feito

| Passo | Arquivo | Linhas |
|-------|---------|--------|
| 1. Adicionar import | `gui/app.py` | +1 (`from reports.pdf_generator import gerar_relatorio_pdf`) |
| 2. Adicionar botão "Exportar PDF" | `gui/app.py` | +8 (CTkButton) |
| 3. Adicionar método `_export_pdf()` | `gui/app.py` | +25 |
| 4. Habilitar/desabilitar no fluxo | `gui/app.py` | +4 (junto com btn_export) |

### 4.2 Posição do botão

O botão existente está na linha 6 do grid (após os stats cards). O novo botão deve ir na linha 7:

```
Linha 0-2: DropZone, file label, model label
Linha 3:   ProgressBar
Linha 4:   Botão "Processar Relatório"
Linha 5:   Stats Cards (3 colunas)
Linha 6:   Botão "Exportar para Excel"    ← existente
Linha 7:   Botão "Exportar Relatório PDF"  ← NOVO
```

### 4.3 Código do método `_export_pdf()`

```python
def _export_pdf(self):
    if self.df_consolidado is None or self.df_bruto is None:
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Documento PDF", "*.pdf")],
        title="Salvar Relatório PDF",
        initialfile="EcoMetric_Relatorio.pdf",
    )
    if not save_path:
        return

    try:
        self._log(f"Exportando relatorio PDF para {os.path.basename(save_path)}...")
        gerar_relatorio_pdf(
            self.df_consolidado,
            self.df_bruto,
            save_path,
            self.modelo_detectado or "desconhecido",
            self.current_pdf_path,
            self.tempo_execucao,
        )
        self._log("Relatorio PDF gerado com sucesso")
        messagebox.showinfo("Sucesso", f"Relatorio PDF exportado com sucesso!\n\n{save_path}")
    except Exception as e:
        self._log(f"ERRO na exportacao PDF: {e}", "error")
        messagebox.showerror("Erro de Exportacao", f"Falha ao gerar PDF:\n\n{e}")
```

### 4.4 Esforço estimado

| Item | Estimativa |
|------|-----------|
| Linhas de código | ~35 |
| Arquivos tocados | 1 (`gui/app.py`) |
| Tempo de implementação | ~10 minutos |
| Risco de quebrar algo | Nulo (adição pura, sem alteração de fluxo existente) |

---

## 5. Logs Duplicados — Diagnóstico

### 5.1 Causa raiz

O problema ocorre porque há **dois RotatingFileHandlers** apontando para o mesmo arquivo, em loggers diferentes, com `propagate=True`:

```
┌──────────────────────────────────────────────┐
│                 ROOT LOGGER                   │
│  level=WARNING                                │
│  handlers:                                    │
│    - StreamHandler          → stderr          │
│    - RotatingFileHandler    → ecometric.log   │  ← DUPLICATA #1
├──────────────────────────────────────────────┤
│             EcoMetric LOGGER                  │
│  level=DEBUG   propagate=True ──────────────► propaga para root
│  handlers (após GUI setup):                   │
│    - QueueLogHandler        → GUI textbox     │
│    - RotatingFileHandler    → ecometric.log   │  ← DUPLICATA #2
└──────────────────────────────────────────────┘
```

**Fluxo de uma chamada `log_info("teste")`:**

1. `EcoMetric` logger recebe a mensagem (level=DEBUG, passa)
2. `QueueLogHandler` escreve na textbox da GUI ✓
3. `RotatingFileHandler` do EcoMetric escreve em `ecometric.log` (1ª vez)
4. `propagate=True` → mensagem sobe para o root logger
5. Root `StreamHandler` escreve em stderr ✓
6. Root `RotatingFileHandler` escreve em `ecometric.log` (2ª vez — **DUPLICATA**)

**Resultado:** Cada mensagem de log aparece **2 vezes** no arquivo `ecometric.log` quando a GUI está rodando.

### 5.2 Handlers ativos por contexto

| Contexto | EcoMetric handlers | Root handlers | propagate | Duplicata? |
|----------|-------------------|---------------|-----------|------------|
| **CLI pura** | 0 (sem handlers próprios) | StreamHandler + RotatingFileHandler | True | **Não** (EcoMetric não tem handlers, só root escreve) |
| **GUI** (após `_setup_logging`) | QueueLogHandler + RotatingFileHandler | StreamHandler + RotatingFileHandler | True | **SIM** (RotatingFileHandler em ambos) |

### 5.3 `_setup_logging()` — o que ele faz

```python
# gui/app.py:84-109
def _setup_logging(self):
    core_logger = logging.getLogger("EcoMetric")
    core_logger.setLevel(logging.DEBUG)

    for handler in core_logger.handlers[:]:     # Remove handlers DO EcoMetric
        core_logger.removeHandler(handler)       # (mas a lista já está vazia na primeira execução)

    gui_handler = QueueLogHandler(self.log_queue)   # Adiciona QueueLogHandler
    core_logger.addHandler(gui_handler)

    file_handler = RotatingFileHandler(...)          # Adiciona RotatingFileHandler
    core_logger.addHandler(file_handler)

    # NOTA: root handlers NÃO são removidos
    # NOTA: propagate NÃO é desabilitado
```

### 5.4 Verificação de `addHandler()` múltiplo

A cada inicialização da GUI, `_setup_logging` é chamado **uma vez** no `__init__`. O loop `for handler in core_logger.handlers[:]` previne duplicação se o método for chamado novamente. Isso está correto.

O problema **não** é múltiplos `addHandler()` no mesmo logger — é a **propagação para o root**.

---

## 6. Plano de Correção

### 6.1 Correção primária: `propagate = False`

Adicionar **1 linha** em `gui/app.py:_setup_logging()`:

```python
core_logger.propagate = False
```

Isso impede que mensagens do logger "EcoMetric" propaguem para o root. Como o root só tem handlers configurados para o caso CLI (onde o EcoMetric não tem handlers próprios), desabilitar propagação na GUI é seguro.

**Após a correção:**

| Contexto | Comportamento |
|----------|---------------|
| CLI | `EcoMetric.propagate=True` → root handlers escrevem no arquivo e stderr (correto) |
| GUI | `EcoMetric.propagate=False` → apenas QueueLogHandler + RotatingFileHandler do EcoMetric (sem duplicata) |

### 6.2 Correção secundária (opcional): limpar root handlers na GUI

Remover o `RotatingFileHandler` do root quando a GUI inicia, já que a GUI adiciona seu próprio:

```python
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    if isinstance(handler, logging.handlers.RotatingFileHandler):
        root_logger.removeHandler(handler)
```

Isso é redundante se `propagate=False`, mas adiciona resiliência.

### 6.3 Verificação pós-correção

| Verificação | Como testar |
|-------------|------------|
| Cada mensagem aparece 1× no arquivo | Contar ocorrências de uma string única no log |
| GUI textbox recebe mensagens | Inspeção visual |
| CLI continua funcionando | `python main.py` com PDF real |
| Rotação funciona | Teste existente `test_rotacao_cria_backups` |

---

## 7. Resumo

| Item | Status |
|------|--------|
| `pdf_generator.py` existe e funciona | ✅ |
| GUI tem botão PDF | ❌ (apenas Excel) |
| `gerar_relatorio_pdf()` chamado na GUI | ❌ |
| DataFrames disponíveis na GUI | ✅ (`self.df_consolidado`, `self.df_bruto`) |
| Logs duplicados na GUI | ✅ Confirmado — `propagate=True` + 2 RotatingFileHandlers |
| Correção da duplicata | 1 linha: `core_logger.propagate = False` |
| Implementação botão PDF | ~35 linhas em `gui/app.py` |
