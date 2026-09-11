# EcoMetric 2.0 — Auditoria de Empacotamento PyInstaller

**Data:** 13/06/2026

---

## 1. EcoMetric.spec — Estado Atual

### 1.1 O que está presente

| Item | Método | Status |
|------|--------|--------|
| Entry point | `gui\__main__.py` | ✅ |
| `pdfplumber` | `collect_submodules` | ✅ |
| `openpyxl` | `collect_submodules` | ✅ |
| `customtkinter` | `collect_all` | ✅ |
| `tkinterdnd2` | `collect_all` (opcional) | ✅ |
| `console` | `False` (windowed) | ✅ |
| Modo | `COLLECT` (pasta) | ✅ |
| UPX | Ativo | ✅ |

### 1.2 O que está AUSENTE (bloqueador)

| Item | Impacto | Gravidade |
|------|---------|-----------|
| `fpdf` (fpdf2) | PDF não funciona no .exe | **CRÍTICO** |
| `matplotlib` | Gráficos não funcionam no .exe | **CRÍTICO** |
| `PIL` (Pillow) | Imagens no PDF quebram (gráfico) | **ALTO** |

### 1.3 Hidden imports necessários (a adicionar)

```python
hiddenimports += collect_submodules('fpdf')
hiddenimports += collect_submodules('matplotlib')
tmp_ret = collect_all('PIL')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
```

---

## 2. Verificação de Dependências

### 2.1 Bibliotecas instaladas e versões

| Biblioteca | Versão | Import no código | Coletada no spec? |
|-----------|--------|-----------------|-------------------|
| `customtkinter` | 5.2.2 | `gui/app.py`, `dropzone.py`, `stats_card.py`, `manager.py` | ✅ |
| `pdfplumber` | 0.11.9 | `detector.py`, `pdf_antigo.py`, `pdf_catafacil.py` | ✅ |
| `pandas` | 3.0.3 | 14 arquivos | ✅ (hook automático) |
| `openpyxl` | 3.1.5 | `exportador.py` (engine) | ✅ |
| `fpdf` (fpdf2) | 2.8.7 | `pdf_generator.py` | ❌ |
| `matplotlib` | 3.11.0 | `charts.py` | ❌ |
| `Pillow` (PIL) | 12.2.0 | fpdf2, matplotlib, ctk | ❌ |
| `tkinterdnd2` | 0.4.x | `app.py`, `dropzone.py` (opcional) | ✅ |
| `numpy` | 2.4.6 | pandas, matplotlib (transitivo) | ✅ (hook automático) |

### 2.2 Dependências transitivas

| Biblioteca | Necessária para | Coletada? |
|-----------|----------------|-----------|
| `fonttools` | fpdf2, matplotlib | ❌ (coberta por collect_submodules('fpdf') e 'matplotlib') |
| `defusedxml` | fpdf2 | ❌ (idem) |
| `contourpy`, `cycler`, `kiwisolver`, `pyparsing` | matplotlib | ❌ (idem) |

---

## 3. Assets (ícones, logos)

| Item | Existe? | Necessário? |
|------|---------|-------------|
| `logo.ico` | Sim (em `EcoMetric/`, legado) | Não usado no spec atual — `icon=` não definido |
| Imagens no PDF | Não — gráficos são gerados em tempfile | N/A |
| Templates | `reports/templates.py` (código, não dados) | ✅ Python module, coletado automaticamente |

**Recomendação:** Adicionar `icon='../EcoMetric/logo.ico'` ao spec ou copiar o ícone para o diretório v2.0.

---

## 4. Matplotlib — Verificação

| Ponto | Status |
|-------|--------|
| Backend `Agg` configurado antes do import | ✅ `charts.py:2-3` |
| `matplotlib.use('Agg')` chamado | ✅ |
| Arquivos temporários limpos | ✅ `finally: os.unlink()` em todos os caminhos |
| Fontes matplotlib | Coletadas por `collect_submodules('matplotlib')` |

**Risco:** `matplotlib` tem ~50 MB de dados (fonts, backends). No modo `COLLECT`, isso é aceitável. No modo `--onefile`, o .exe ficaria muito grande.

---

## 5. fpdf2 — Verificação

| Ponto | Status |
|-------|--------|
| Fonte padrão: Helvetica | ✅ Core PDF font, não requer arquivo externo |
| Imagens PNG (gráficos matplotlib) | ✅ Pillow (PIL) necessário |
| Unicode além de Latin-1 | ❌ Não suportado com fontes core — `sanitize_pdf_text()` mitiga |

**Risco:** Se `PIL` não for coletado, `pdf.image()` falha ao inserir gráficos.

---

## 6. CustomTkinter — Verificação

| Ponto | Status |
|-------|--------|
| `collect_all('customtkinter')` no spec | ✅ |
| Tema padrão: green | ✅ |
| Persistência de tema | ✅ `~/.ecometric_gui_config.json` (fora do bundle) |

---

## 7. tkinterdnd2 — Verificação

| Ponto | Status |
|-------|--------|
| `collect_all('tkinterdnd2')` no spec | ✅ |
| Fallback se ausente | ✅ `try/except ImportError` em `app.py` e `dropzone.py` |
| Bibliotecas nativas (.dll/.pyd) | Coletadas por `collect_all` |

---

## 8. Caminhos Relativos (`__file__`)

### 8.1 Uso de `__file__` no código

| Arquivo | Linha | Uso | Compatível PyInstaller? |
|---------|-------|-----|------------------------|
| `gui/__main__.py` | 11 | `os.path.dirname(os.path.abspath(__file__))` | ✅ PyInstaller define `__file__` |
| `gui/app.py` | 17-20 | `_GUI_DIR = os.path.dirname(...)` e `sys.path.insert` | ✅ |
| `main.py` | 7 | `DIRETORIO_CORRENTE = os.path.dirname(...)` | ⚠️ CLI — não usado no .exe |
| `test_golden.py` | 9-10 | `sys.path.insert` com caminhos relativos | ✅ Testes não vão no bundle |

### 8.2 Caminhos absolutos problemáticos

| Local | Caminho | Problema? |
|-------|---------|-----------|
| `config/settings.py` | `os.getenv('APPDATA', ...)` | ✅ Resolvido em runtime |
| `gui/theme/manager.py` | `os.path.expanduser('~')` | ✅ Resolvido em runtime |
| `reports/pdf_generator.py` | `tempfile.gettempdir()` | ✅ Resolvido em runtime |

---

## 9. Gravação de Logs em %APPDATA%

| Ponto | Status |
|-------|--------|
| `_DIR_LOG` definido em `settings.py` | ✅ `os.getenv('APPDATA', os.path.expanduser('~'))` |
| Fallback para `~` se `APPDATA` não definido | ✅ |
| `os.makedirs(exist_ok=True)` | ✅ |
| `RotatingFileHandler` em `gui/app.py` | ✅ Mesmo caminho, mesma lógica |

**Conclusão:** Funciona corretamente dentro do .exe. `APPDATA` é uma variável de ambiente do Windows — sempre disponível.

---

## 10. Exportação Excel e PDF dentro do .exe

| Funcionalidade | Dependência | No spec? | Funciona? |
|---------------|------------|----------|-----------|
| Exportação Excel | `openpyxl` | ✅ | ✅ |
| Exportação PDF individual | `fpdf`, `matplotlib`, `PIL` | ❌ (faltam) | ❌ |
| Exportação PDF anual | `fpdf`, `matplotlib`, `PIL` | ❌ (faltam) | ❌ |
| Gráficos no PDF | `matplotlib`, `PIL` | ❌ (faltam) | ❌ |

---

## 11. Spec Final Recomendado

```python
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# Core
hiddenimports += collect_submodules('pdfplumber')
hiddenimports += collect_submodules('openpyxl')

# PDF Generation (SPRINT 4-6)
hiddenimports += collect_submodules('fpdf')
hiddenimports += collect_submodules('matplotlib')

# GUI
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# GUI: Drag & Drop (opcional)
tmp_ret = collect_all('tkinterdnd2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Image support (Pillow — requerido por fpdf2, matplotlib, ctk)
tmp_ret = collect_all('PIL')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Icon (from legacy directory)
# icon_path = '../EcoMetric/logo.ico'  # descomentar se quiser ícone

a = Analysis(
    ['gui\\__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EcoMetric',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=icon_path,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EcoMetric',
)
```

### Mudanças do spec atual:

```diff
+ hiddenimports += collect_submodules('fpdf')
+ hiddenimports += collect_submodules('matplotlib')
+ tmp_ret = collect_all('PIL')
+ datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
```

---

## 12. Comando Final de Build

```bash
cd "EcoMetric 2.0"
pyinstaller EcoMetric.spec --clean --noconfirm
```

**Saída esperada:** `dist/EcoMetric/EcoMetric.exe` com todos os módulos.

**Tamanho estimado:** ~80-100 MB (devido a matplotlib, numpy, pandas).

---

## 13. Riscos Encontrados

| Risco | Impacto | Probabilidade |
|-------|---------|---------------|
| **fpdf2/matplotlib não coletados** — PDF quebra | Crítico | 100% (build atual) |
| PIL não coletado — gráficos não aparecem | Alto | 100% (build atual) |
| Tamanho do bundle (COLLECT) ~100 MB | Médio | 100% (com matplotlib) |
| `disable_windowed_traceback=False` — erros invisíveis | Médio | Permanente |
| UPX pode corromper .pyd do matplotlib | Baixo | Raro |
| Antivírus falso positivo (comum PyInstaller) | Médio | ~30% |
| Fontes matplotlib podem faltar em COLLECT | Baixo | `collect_submodules` cobre |

---

## 14. Status

| Item | Status |
|------|--------|
| Spec funcional para GUI + Excel | ✅ |
| Spec funcional para PDF + Gráficos | ❌ (faltam 3 hidden imports) |
| Build testado em máquina limpa | ❌ (não verificado) |
| Ícone do executável | ❌ (não configurado) |
| Instalador (NSIS/InnoSetup) | ❌ (não implementado) |

**Conclusão:** O spec atual cobre apenas o MVP original (GUI + Excel). Para release completo com PDF, são necessários 3 hidden imports adicionais (`fpdf`, `matplotlib`, `PIL`).
