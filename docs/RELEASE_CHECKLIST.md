# EcoMetric 2.0 — Release Checklist v1.0

**Data alvo:** A definir
**Versão:** 1.0.0

---

## Pré-lançamento

### Dependências

- [ ] **Criar `requirements.txt`** na raiz do `EcoMetric 2.0/`
  ```txt
  customtkinter>=5.2.0
  pdfplumber>=0.11.0
  pandas>=3.0.0
  openpyxl>=3.1.0
  fpdf2>=2.8.0
  matplotlib>=3.10.0
  pillow>=12.0.0
  tkinterdnd2>=0.4.0  # opcional
  ```
- [ ] **Validar `requirements.txt`** — `pip install -r requirements.txt` em ambiente limpo
- [ ] **Criar `pyproject.toml`** com metadados:
  ```toml
  [project]
  name = "ecometric"
  version = "1.0.0"
  description = "Conversor de Relatórios Ambientais - ACAMARTI"
  requires-python = ">=3.10"
  ```

### Build

- [ ] **Atualizar `EcoMetric.spec`** — adicionar `fpdf2` e `matplotlib` aos hiddenimports
  ```python
  hiddenimports += collect_submodules('fpdf')
  hiddenimports += collect_submodules('matplotlib')
  ```
- [ ] **Build PyInstaller limpo** — `pyinstaller EcoMetric.spec --clean`
- [ ] **Verificar executável standalone** — copiar `dist/EcoMetric/` para máquina sem Python e testar
- [ ] **Testar todas as funcionalidades no .exe**:
  - [ ] Abrir GUI
  - [ ] Selecionar PDF (botão)
  - [ ] Drag & drop PDF
  - [ ] Detectar modelo automaticamente
  - [ ] Processar relatório
  - [ ] Exibir stats cards
  - [ ] Exportar Excel
  - [ ] Exportar PDF (NOVO)
  - [ ] Alternar tema Dark/Light
  - [ ] Logs na sidebar
- [ ] **Testar com PDF real CataFácil**
- [ ] **Testar com PDF real modelo Antigo**
- [ ] **Testar PDF sem dados** (vazio)
- [ ] **Testar PDF corrompido** (tratamento de erro)
- [ ] **Verificar ausência de console window** (`console=False` no spec)

### Código

- [ ] **28/28 testes passando** ✅ (confirmado 13/06/2026)
- [ ] **Rodar golden tests** com PDFs reais:
  - [ ] Modelo CataFácil (52 snapshots existentes)
  - [ ] Modelo Antigo (0 snapshots — GERAR ANTES DO RELEASE)
- [ ] **Verificar imports não utilizados** — `pip install vulture && vulture .`
- [ ] **Verificar B01-B09 resolvidos** ou documentados como known issues

### Logs e Erros

- [ ] **Adicionar `FileHandler`** ao logger — salvar em `%APPDATA%/EcoMetric/logs/`
- [ ] **Log de sessão** — arquivo por execução com timestamp
- [ ] **Handler global de exceções** na GUI — capturar exceções não tratadas
- [ ] **Modo DEBUG documentado** — `ECOMETRIC_DEBUG=true`

---

## Documentação

### Usuário

- [ ] **Criar `README.md`** com:
  - [ ] Descrição do projeto
  - [ ] Requisitos de sistema (Windows 10+, Python 3.10+)
  - [ ] Instalação (passo a passo)
  - [ ] Como usar (GUI e CLI)
  - [ ] Formatos de PDF aceitos (CataFácil e Antigo)
  - [ ] Significado das métricas (CO2e, equivalências)
  - [ ] Troubleshooting comum
- [ ] **Gerar screenshots da GUI**:
  - [ ] Tela inicial (Dark)
  - [ ] Tela inicial (Light)
  - [ ] PDF selecionado com modelo detectado
  - [ ] Após processamento (stats cards preenchidos)
  - [ ] Exportação concluída
- [ ] **Criar `CHANGELOG.md`**:
  ```markdown
  # Changelog
  ## [1.0.0] - 2026-XX-XX
  ### Added
  - Interface gráfica com CustomTkinter
  - Suporte a drag & drop de PDFs
  - Detecção automática de modelo (CataFácil / Antigo)
  - Processamento em thread separada
  - Exportação Excel multi-abas (5 abas)
  - Geração de relatório PDF com gráficos
  - Tema Dark/Light com persistência
  - CLI com modo interativo
  - Benchmark de performance
  - Golden tests (52 snapshots CataFácil)
  ### Changed
  - Arquitetura modular (migrada do monolito legado)
  - Uso de Decimal para precisão em cálculos
  ### Fixed
  - (bugs corrigidos da v0.x)
  ```

### Técnica

- [ ] **Docstrings em todas as funções públicas**
- [ ] **Diagrama de arquitetura** (SVG ou PNG)
- [ ] **Documentar API do core**:
  - `processar_relatorio_pdf()`
  - `detectar_modelo_pdf()`
  - `exportar_para_excel()`
  - `gerar_relatorio_pdf()`

---

## Empacotamento Final

- [ ] **Definir formato de distribuição**:
  - [ ] ZIP com executável + `_internal/` (modo COLLECT)
  - [ ] OU onefile .exe (modo `--onefile`, ~80-120 MB)
  - [ ] Instalador (NSIS/InnoSetup)
- [ ] **Incluir na distribuição**:
  - [ ] `EcoMetric.exe`
  - [ ] `_internal/` (se COLLECT)
  - [ ] `README.md`
  - [ ] `CHANGELOG.md`
  - [ ] `requirements.txt` (para modo dev)
- [ ] **Testar distribuição em máquina limpa** (Windows 10/11 sem Python)
- [ ] **Verificar antivírus** — falso positivo comum com PyInstaller
- [ ] **Assinar executável** (codesign) — opcional para distribuição corporativa

---

## Pós-lançamento

- [ ] **Tag no git** — `v1.0.0`
- [ ] **Criar `.gitignore`**
  ```
  __pycache__/
  *.pyc
  build/
  dist/
  .pytest_cache/
  *.xlsx
  *.pdf
  ```
- [ ] **Configurar CI/CD** — GitHub Actions para rodar testes automaticamente
- [ ] **Plano de atualização** — como entregar novas versões ao cliente

---

## Resumo

| Categoria | Itens | Concluídos |
|-----------|-------|------------|
| Dependências | 3 | 0 |
| Build | 10 | 0 |
| Código | 6 | 1 (testes passam) |
| Logs e Erros | 4 | 0 |
| Docs Usuário | 13 | 0 |
| Docs Técnica | 4 | 0 |
| Empacotamento | 7 | 0 |
| Pós-lançamento | 4 | 0 |

**Total: 51 itens | Concluídos: 1 (28 testes passam)**
