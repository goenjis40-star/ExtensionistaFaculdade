# EcoMetric 2.0 — Release Audit (v1.0)

**Data:** 13/06/2026
**Critério:** Prontidão para distribuição ao cliente final

---

## 1. requirements.txt

| Status | Detalhes |
|--------|----------|
| **AUSENTE** | Não existe `requirements.txt` na raiz do `EcoMetric 2.0/` |

O único `requirements.txt` existente está no diretório legado (`EcoMetric/requirements.txt`) e lista 30 pacotes incluindo `fpdf==1.7.2` (obsoleto). A v2.0 usa `fpdf2==2.8.7` e `matplotlib==3.11.0` que não estão documentados em arquivo de dependências.

**Ação necessária:** Criar `requirements.txt` na raiz da v2.0.

---

## 2. pyproject.toml / setup.py

| Status | Detalhes |
|--------|----------|
| **AUSENTE** | Nenhum arquivo de metadados de pacote |

O projeto não pode ser instalado via `pip install .` e não possui metadados formais (nome, versão, autor, licença).

**Ação necessária:** Criar `pyproject.toml` com metadados básicos do projeto.

---

## 3. Build PyInstaller

| Status | Detalhes |
|--------|----------|
| **PARCIAL** | Spec existe, executável gerado, mas desatualizado |

**O que funciona:**
- `EcoMetric.spec` existe e referencia `gui/__main__.py` como entry point
- Coleta `pdfplumber`, `openpyxl`, `customtkinter`, `tkinterdnd2`
- `console=False` (windowed)
- Executável existe: `dist/EcoMetric/EcoMetric.exe` (14.5 MB, 1981 arquivos)

**O que falta:**
- `fpdf2` e `matplotlib` NÃO estão nos `hiddenimports` — o build atual não inclui geração de PDF
- Script de build automatizado (sem equivalente ao `Build.bat` do legado)
- Modo `COLLECT` (pasta) em vez de `--onefile` — distribuição menos portátil
- `disable_windowed_traceback=False` — usuário NÃO vê stack traces se app crashar

**Ação necessária:** Atualizar spec com `fpdf2`, `matplotlib`; criar script de build.

---

## 4. Tratamento de Erros da GUI

| Status | Detalhes |
|--------|----------|
| **PARCIAL** | Cobertura básica mas incompleta |

**Presente:**
- `try/except` no worker de processamento → `messagebox.showerror` (linha 339)
- `try/except` na exportação Excel → `messagebox.showerror` (linha 380)
- `try/except` na detecção de modelo → label atualizada (linha 275)
- `try/except ImportError` para `tkinterdnd2` → fallback gracioso (linha 36)
- `try/except queue.Empty` no poll de logs (linha 245)

**Ausente:**
- Tratamento de `KeyboardInterrupt` (Ctrl+C)
- Tratamento de erro na inicialização do `ThemeManager`
- Validação de integridade dos DataFrames antes de exibir stats
- Log de erros fatais em arquivo (apenas na textbox da sidebar)
- Diálogo de confirmação antes de sobrescrever arquivo na exportação

**Ação necessária:** Adicionar handler global de exceções; log em arquivo.

---

## 5. Logs em Produção

| Status | Detalhes |
|--------|----------|
| **PARCIAL** | Logger funcional mas sem persistência |

**Presente:**
- Logger nomeado `"EcoMetric"` via `logging.getLogger()`
- `DEBUG` controlado por variável de ambiente `ECOMETRIC_DEBUG`
- `QueueLogHandler` redireciona logs para a GUI em tempo real
- Níveis: `DEBUG`, `INFO`, `WARNING`, `ERROR`

**Ausente:**
- Sem `FileHandler` — logs não são persistidos em disco
- Sem rotação de arquivos de log
- Sem separação de logs por sessão
- `StreamHandler` em `settings.py` imprime no stdout (invisível em app windowed)

**Ação necessária:** Adicionar `FileHandler` com rotação para `%APPDATA%/EcoMetric/logs/`.

---

## 6. Configuração de Ambiente

| Status | Detalhes |
|--------|----------|
| **PARCIAL** | Funcional mas frágil |

**Presente:**
- `config/settings.py` centraliza constantes (CO2, locale, DEBUG)
- `DEBUG` via `ECOMETRIC_DEBUG` env var
- Tema da GUI persistido em `~/.ecometric_gui_config.json`
- Locale brasileiro configurado (tentativa com fallback)

**Ausente:**
- Arquivo de configuração `.env` ou `.ini` para overrides
- Validação dos fatores de CO2 (valores hardcoded)
- Configuração de proxy/network
- Detecção de primeiro uso (first-run wizard)

**Ação necessária:** Documentar variáveis de ambiente; adicionar validação.

---

## 7. Documentação de Usuário

| Status | Detalhes |
|--------|----------|
| **AUSENTE** | Zero documentação orientada ao usuário final |

- Sem `README.md` com instruções de instalação/uso
- Sem manual do usuário
- Sem screenshots da GUI
- Sem FAQ ou troubleshooting
- Sem descrição dos formatos de PDF aceitos
- Sem explicação dos fatores de CO2 ou equivalências

**Ação necessária:** Criar `README.md`; gerar screenshots.

---

## 8. Documentação Técnica

| Status | Detalhes |
|--------|----------|
| **PARCIAL** | 6 documentos de auditoria/planejamento, zero docs de API |

**Presente (docs/):**
- `PROJECT_STATUS.md` — auditoria geral (483 linhas)
- `STATUS_REPORT.md` — status report resumido
- `GUI_AUDIT.md` — validação da GUI
- `GUI_IMPLEMENTATION_PLAN.md` — arquitetura da GUI
- `PDF_REPORT_AUDIT.md` — auditoria de PDF
- `PDF_REPORT_IMPLEMENTATION_PLAN.md` — plano de PDF

**Ausente:**
- Documentação de API (`core.parsers.processar_relatorio_pdf`, etc.)
- Docstrings em algumas funções públicas (parsers têm; exportador tem; utils parcial)
- Diagramas de arquitetura (apenas ASCII no PROJECT_STATUS.md)
- Guia de contribuição
- Documentação das regras de categorização

**Ação necessária:** Adicionar docs de API; melhorar docstrings.

---

## 9. Instalação Limpa em Máquina Nova

| Status | Detalhes |
|--------|----------|
| **PARCIAL** | Executável existe mas não cobre todas as dependências |

**Cenário testado (simulado):**

| Passo | Resultado |
|-------|-----------|
| Python 3.14 instalado | OK |
| `pip install customtkinter pdfplumber pandas openpyxl fpdf2 matplotlib pillow` | OK (8 pacotes) |
| `python -m gui` | OK (imports funcionam) |
| `python main.py relatorio.pdf` | OK (CLI funciona) |
| Executar `dist/EcoMetric/EcoMetric.exe` diretamente | **NÃO TESTADO** |

**Problemas identificados:**
- Sem `requirements.txt` — usuário não sabe quais pacotes instalar
- PyInstaller spec desatualizado (falta fpdf2, matplotlib)
- Executável atual foi gerado ANTES da implementação do PDF generator
- Modo COLLECT requer a pasta `_internal/` inteira (1981 arquivos)
- Sem instalador (NSIS, InnoSetup, MSI)

**Ação necessária:** Rebuild do PyInstaller; criar `requirements.txt`; considerar onefile.

---

## 10. Resumo

| # | Critério | Classificação |
|---|----------|---------------|
| 1 | `requirements.txt` | **AUSENTE** |
| 2 | `pyproject.toml` / `setup.py` | **AUSENTE** |
| 3 | Build PyInstaller | **PARCIAL** (spec desatualizado) |
| 4 | Tratamento de erros da GUI | **PARCIAL** (sem log em arquivo) |
| 5 | Logs em produção | **PARCIAL** (sem FileHandler) |
| 6 | Configuração de ambiente | **PARCIAL** (sem .env, sem validação) |
| 7 | Documentação de usuário | **AUSENTE** |
| 8 | Documentação técnica | **PARCIAL** (docs internos apenas) |
| 9 | Instalação limpa | **PARCIAL** (build desatualizado) |

**Média:** 0 OK / 6 PARCIAL / 3 AUSENTE

**Conclusão:** O EcoMetric 2.0 **não está pronto para distribuição ao cliente**. O core técnico é sólido, mas a infraestrutura de release (dependências documentadas, build atualizado, documentação) está ausente ou desatualizada.
