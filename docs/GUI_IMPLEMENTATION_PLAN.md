# EcoMetric 2.0 — GUI Implementation Plan (Reference)

**Data:** 13/06/2026
**Status:** IMPLEMENTADO — este documento descreve a arquitetura existente como referência.

---

## 1. Arquitetura

```
gui/
├── __init__.py              # Docstring: "Módulo GUI para EcoMetric 2.0"
├── __main__.py              # Entry point: python -m gui
├── app.py                   # App (BaseWindow) — janela principal
├── components/
│   ├── __init__.py
│   ├── dropzone.py          # DropZone — seleção de PDF (drag & drop + botão)
│   └── stats_card.py        # StatsCard — exibição de estatísticas
├── handlers/
│   ├── __init__.py
│   └── log_handler.py       # QueueLogHandler — logging thread-safe para GUI
└── theme/
    ├── __init__.py
    └── manager.py           # ThemeManager — Dark/Light com persistência
```

### 1.1 Hierarquia de classes

```
ctk.CTk
  └── BaseWindow (ctk.CTk [+ TkinterDnD.DnDWrapper se disponível])
        └── App (app.py)
              ├── DropZone (components/dropzone.py)
              │     └── ctk.CTkFrame
              ├── StatsCard ×3 (components/stats_card.py)
              │     └── ctk.CTkFrame
              ├── ctk.CTkProgressBar
              ├── ctk.CTkButton ×2 (Processar, Exportar)
              ├── ctk.CTkTextbox (log)
              ├── ctk.CTkSwitch (tema)
              └── ctk.CTkLabel ×4 (logo, subtitle, file, model)
```

---

## 2. Fluxo da Aplicação

```
Usuário seleciona PDF (drag & drop OU botão "Selecionar PDF")
│
├── DropZone._on_drop() / DropZone._browse_file()
│   └── callback: App._on_file_selected(filepath)
│       ├── Armazena caminho (self.current_pdf_path)
│       ├── Atualiza label do arquivo
│       ├── Habilita botão "Processar"
│       ├── Reseta stats cards para "--"
│       └── Detecta modelo automaticamente
│           └── detectar_modelo_pdf(filepath) → "catafacil" | "antigo"
│
▼
Usuário clica "Processar Relatório"
│
├── App._start_processing()
│   ├── Desabilita botões
│   ├── Inicia progress bar (indeterminate)
│   └── Cria thread: threading.Thread(target=_process_worker)
│
├── App._process_worker() [thread separada]
│   ├── Mede tempo (time.perf_counter)
│   ├── Chama processar_relatorio_pdf(pdf_path)
│   │   ├── detectar_modelo_pdf()
│   │   ├── parse_pdf_catafacil() ou parse_pdf_antigo()
│   │   └── Retorna (df_consolidado, df_bruto)
│   └── Agenda callback na thread principal: self.after(0, _on_process_success)
│
▼
App._on_process_success() [thread principal]
│
├── Para progress bar
├── Habilita botões
├── Atualiza stats cards:
│   ├── Peso Total (t) = sum(df["Peso Total (t)"])
│   ├── CO2 Evitado (t CO2e) = sum(df["CO2 Evitado (t CO2e)"])
│   └── Categorias = len(df)
└── Loga resultado
│
▼
Usuário clica "Exportar para Excel"
│
├── filedialog.asksaveasfilename() → caminho .xlsx
├── exportar_para_excel(df_consolidado, df_bruto, pdf_path, modelo, tempo, save_path)
├── messagebox.showinfo("Sucesso")
└── Loga exportação
```

---

## 3. Integrações com o Core

### 3.1 Contratos utilizados

| Função | Assinatura | Retorno |
|--------|-----------|---------|
| `detectar_modelo_pdf(caminho)` | `Optional[str] → str` | `"catafacil"` ou `"antigo"` |
| `processar_relatorio_pdf(caminho, fator_co2_map?)` | `(str, dict?) → Tuple[DataFrame, DataFrame]` | `(df_consolidado, df_bruto)` |
| `exportar_para_excel(df_cons, df_bruto, pdf, modelo, tempo, saida)` | `(DataFrame, DataFrame, str, str, float, str) → bool` | `True`/`False` |

### 3.2 Logger

A GUI captura logs do core via `logging.getLogger("EcoMetric")` e os redireciona para o `CTkTextbox` da sidebar através do `QueueLogHandler`.

```
Core ──logging──> QueueLogHandler ──queue.Queue──> App._poll_log_queue() ──> CTkTextbox
```

---

## 4. Requisitos Respeitados

| Requisito | Status |
|-----------|--------|
| Não alterar contratos do core | ✓ A GUI é consumidora pura |
| Não alterar golden tests | ✓ Snapshots intactos |
| Não alterar parsers | ✓ Parsers não modificados |
| Não alterar benchmark | ✓ Benchmark intacto |
| Não alterar exportador | ✓ Exportador usado como API |
| Não modificar regras de negócio | ✓ Lógica está 100% no core |
| Não alterar DataFrames retornados | ✓ DataFrames consumidos read-only |
| Não alterar assinaturas públicas | ✓ Nenhuma assinatura alterada |
| Não alterar snapshots golden | ✓ Sem alterações em tests/golden/ |

---

## 5. Decisões Arquiteturais

| Decisão | Justificativa |
|---------|---------------|
| **CustomTkinter** sobre Tkinter puro | Legado já usava CTk; look moderno consistente |
| **Thread separada** para processamento | Evita congelamento da UI durante parsing de PDF |
| **Queue + polling** para logs | Thread-safe sem violar regras de single-thread do Tkinter |
| **tkinterdnd2 opcional** | Fallback para botão garante funcionalidade sem a lib |
| **Persistência de tema em JSON** | `~/.ecometric_gui_config.json` — simples, sem dependências |
| **Stats como componentes reutilizáveis** | `StatsCard` pode ser reutilizado em dashboards futuros |
| **DropZone como componente isolado** | Pode ser reutilizado em outras telas |
| **Sidebar fixa (270px)** | Layout com painel principal expansível + sidebar de log |
| **Botão Exportar verde** (#2ea043) | Diferenciação visual da ação de exportação |

---

## 6. Comandos de Execução

### Desenvolvimento

```bash
# GUI
python -m gui
# ou
python gui/__main__.py

# CLI
python main.py "caminho/do/relatorio.pdf"

# Testes
python -m pytest test_utils.py test_categorias.py test_detector.py test_pdf_antigo.py test_pdf_catafacil.py test_exportador.py

# Golden tests
python -m pytest tests/test_golden.py

# Benchmark
python scripts/benchmark.py
```

### Build

```bash
# PyInstaller (gera dist/EcoMetric/)
pyinstaller EcoMetric.spec --clean
```

---

## 7. Riscos Identificados

| Risco | Mitigação |
|-------|-----------|
| Sem testes de GUI | Regressões visuais não detectadas; mitigar com testes manuais |
| `tkinterdnd2` ausente em alguns ambientes | Fallback para botão já implementado |
| CustomTkinter muda API entre versões | Pin de versão no `requirements.txt` (a ser criado) |
| Thread pode lançar exceção não capturada | `_process_worker` tem try/except; erros vão para `_on_process_error` |
| Exportação pode falhar (openpyxl ausente) | `exportar_para_excel` retorna `False`; GUI mostra `messagebox.showerror` |

---

## 8. Estado Final

| Item | Status |
|------|--------|
| Implementação | **CONCLUÍDA** |
| Build | **CONCLUÍDO** (executável em `dist/`) |
| Testes | **PENDENTE** (zero cobertura de GUI) |
| Documentação | **CONCLUÍDA** (este documento + GUI_AUDIT.md) |
