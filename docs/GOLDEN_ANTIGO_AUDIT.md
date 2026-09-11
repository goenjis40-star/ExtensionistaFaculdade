# Golden Tests — Auditoria do Modelo ANTIGO

**Data:** 13/06/2026
**Auditor:** Inspeção completa do repositório + classificação de todos os PDFs

---

## 1. PDFs Disponíveis no Repositório

### 1.1 Inventário completo

| # | Nome | Localização | Tamanho | Modelo | É input válido? |
|---|------|------------|--------|--------|-----------------|
| 1 | `05 - Vendas_Por_Materiais catafacil Maio 23.pdf` | `EcoMetric\` (legado) | 114 KB | **CATAFACIL** | Sim |
| 2 | `05 - Vendas_Por_Materiais catafacil Maio 23.pdf` | `EcoMetric 2.0\` (raiz) | 114 KB | **CATAFACIL** | Sim (duplicata do #1) |
| 3 | `exemplo_relatorio.pdf` | `EcoMetric 2.0\docs\` | 30 KB | **ANTIGO** (classificação incorreta — ver §1.2) | **NÃO** |

### 1.2 Falso positivo: `exemplo_relatorio.pdf`

O arquivo `docs/exemplo_relatorio.pdf` foi classificado como "ANTIGO" pelo detector simplesmente porque **não contém marcadores CataFácil**. Mas este PDF **não é um relatório de entrada do pipeline** — é um **relatório de saída** gerado pelo `reports/pdf_generator.py` (implementado em 13/06/2026).

Ele contém texto como:
```
RELATORIO VERDE - ACAMARTI 2026
TOTAL DE CO2 EQUIVALENTE EVITADO
43,548 Toneladas de CO2e
```

Submetê-lo ao parser legado ou novo **não produziria resultados significativos** — os parsers esperam tabelas de materiais com colunas de peso/unidade, não um documento narrativo de CO2.

### 1.3 Conclusão sobre PDFs ANTIGO

```
PDFs ANTIGO reais disponíveis: 0
PDFs CATAFACIL reais disponíveis: 1 (com duplicata)
PDFs de saída (não-inputs): 1
```

**O repositório não contém nenhum PDF real do modelo ANTIGO.** Este é o bloqueador principal.

---

## 2. Estado do Diretório `tests/golden/antigo/`

### 2.1 Conteúdo

```
tests/golden/antigo/
  (vazio — 0 arquivos, 0 subdiretórios)
```

### 2.2 Comparação com CataFácil

| Métrica | `golden/antigo/` | `golden/catafacil/` |
|---------|-----------------|---------------------|
| Arquivos | 0 | 52 |
| Meses cobertos | Nenhum | 12 (Jan-Dez) + anual |
| Formatos | — | CSV consolidado, JSON consolidado, CSV bruto, JSON bruto |
| Status | **NÃO INICIADO** | **CONCLUÍDO** |

---

## 3. Análise do `test_golden.py` (142 linhas)

### 3.1 Fluxo atual

```
setUpClass()
  ├── cls.diretorio_legado = "../EcoMetric"        (onde buscar PDFs)
  ├── cls.diretorio_golden = "tests/golden"          (onde salvar snapshots)
  ├── os.makedirs("golden/antigo", exist_ok=True)    (cria dir se não existe)
  ├── os.makedirs("golden/catafacil", exist_ok=True) (cria dir se não existe)
  └── cls.arquivos_pdf = [*.pdf em EcoMetric/]       (coleta PDFs)
      │
      ▼
test_golden_snapshots_and_equivalence()          (1 método parametrizado)
  │
  ├── assert len(arquivos_pdf) > 0               (falha se zero PDFs)
  │
  Para cada PDF:
  ├── 1. detectar_modelo_pdf(pdf) → "catafacil" | "antigo"
  ├── 2. legacy.processar_relatorio_pdf(pdf)     (referência dourada)
  ├── 3. Salvar snapshots (CSV + JSON bruto/consolidado)
  ├── 4. parse_pdf_catafacil() OU parse_pdf_antigo() (novo parser)
  └── 5-6. assertEqual / assertAlmostEqual em todas as linhas
```

### 3.2 Suporte ao modelo ANTIGO

O `test_golden.py` **já possui suporte completo ao modelo ANTIGO**:

| Aspecto | Suporte | Evidência |
|---------|---------|-----------|
| Detecção de modelo | Sim | `detectar_modelo_pdf()` retorna `"antigo"` como fallback |
| Roteamento de parser | Sim | Linha 86-87: `else` chama `parse_pdf_antigo` |
| Roteamento de snapshots | Sim | `subpasta = "catafacil" if modelo == "catafacil" else "antigo"` |
| Criação de diretório | Sim | `os.makedirs(..., "antigo", exist_ok=True)` |
| Comparação linha a linha | Sim | Lógica é agnóstica ao modelo |
| Tolerância numérica | Sim | `assertAlmostEqual(places=7)` para ambos |

**Nenhuma alteração no `test_golden.py` é necessária.** O código está pronto.

### 3.3 O que falta

O teste já funciona para o modelo ANTIGO — ele simplesmente nunca foi executado porque **não há PDFs ANTIGO** no diretório legado. A condição `assertTrue(len(arquivos_pdf) > 0)` na linha 46 nunca falhou porque o único PDF real (`catafacil Maio 23.pdf`) existe.

Se um PDF ANTIGO fosse colocado na pasta `EcoMetric/`, o teste:
1. Detectaria `modelo = "antigo"`
2. Criaria snapshots em `golden/antigo/`
3. Chamaria `parse_pdf_antigo()`
4. Compararia com o legado

---

## 4. Menor Implementação Necessária

### 4.1 Sem alterações de código

A **única** ação necessária para atingir cobertura Golden do modelo ANTIGO é:

> **Obter PDFs reais do modelo ANTIGO e colocá-los na pasta `EcoMetric/`.**

Nenhuma alteração em `test_golden.py`, parsers, core, ou infraestrutura é necessária.

### 4.2 O que NÃO é necessário

- Alterar `test_golden.py` — já suporta ANTIGO
- Alterar `core/parsers/pdf_antigo.py` — já implementado e testado com mocks
- Alterar `core/parsers/detector.py` — já retorna `"antigo"` como fallback
- Criar nova infraestrutura de teste — o framework golden já existe
- Alterar snapshots CataFácil — são independentes

### 4.3 O que É necessário

| Ação | Esforço | Dependência |
|------|---------|-------------|
| Obter 1+ PDFs reais do modelo ANTIGO | Externo | Cliente / ACAMARTI |
| Copiar PDF(s) para `EcoMetric/` | 1 minuto | — |
| Executar `python -m pytest tests/test_golden.py -v` | 30 segundos | — |
| Verificar snapshots gerados em `golden/antigo/` | 1 minuto | — |

**Esforço total estimado: ~5 minutos** (uma vez obtidos os PDFs).

---

## 5. Plano de Execução

### Etapa 1: Localizar PDFs ANTIGO

**Situação atual:** Nenhum PDF ANTIGO no repositório.

**Ação:** Solicitar ao cliente/usuário da ACAMARTI exemplos de relatórios que NÃO sejam do CataFácil (formato antigo). O legado (`EcoMetric/relatorioverde.py`) processava esses PDFs antes da migração — os arquivos originais devem existir no computador do cliente.

**Produto:** 1-5 PDFs do modelo ANTIGO copiados para `EcoMetric/`.

### Etapa 2: Gerar Snapshots

**Comando:**
```bash
cd EcoMetric 2.0
python -m pytest tests/test_golden.py -v -s
```

**O que acontece:**
1. `setUpClass` coleta todos os PDFs de `EcoMetric/` (CataFácil + ANTIGO)
2. Para cada PDF, o detector classifica o modelo
3. O parser legado (`relatorioverde.py`) é executado como referência
4. Snapshots CSV + JSON são salvos em `golden/catafacil/` e `golden/antigo/`
5. O parser novo é executado
6. Resultados são comparados linha a linha

**Produto:** 4 arquivos por PDF ANTIGO em `tests/golden/antigo/`:
- `<nome>_consolidado.csv`
- `<nome>_consolidado.json`
- `<nome>_bruto.csv`
- `<nome>_bruto.json`

### Etapa 3: Validar Equivalência

Se o teste passar (todos os asserts verdes), a equivalência está confirmada.

Se falhar, os asserts indicam exatamente qual linha/material/peso/CO2 divergiu — permitindo correção pontual no `pdf_antigo.py`.

**Possíveis fontes de divergência:**
- Regex `LINE_REGEX` no `pdf_antigo.py` capturando linha a mais ou a menos
- Filtro de serviços (`SERVICO`, `TRIAGEM`, etc.) descartando material válido
- Prioridade de plástico em `classificar_material_antigo` divergindo da implementação legada
- Conversão `parse_peso_brasileiro` vs implementação inline do legado

### Etapa 4: Integrar ao Pipeline de Testes

Após snapshots gerados e validados, os testes golden passam a cobrir ambos os modelos automaticamente em todas as execuções futuras.

**Comando contínuo:**
```bash
python -m pytest tests/test_golden.py -v
```

Nenhuma integração adicional necessária — o teste já está no local correto.

---

## 6. Riscos de Regressão

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **PDF ANTIGO real tem formato diferente do esperado** pelo parser | Média | Alto — teste falha | O parser foi escrito baseado no legado; se houver divergência, é um bug real que precisa ser corrigido |
| **Legado `processar_relatorio_pdf` tem comportamento diferente** do novo `parse_pdf_antigo` | Baixa | Alto — snapshots inválidos | O golden test serve exatamente para detectar isso; se falhar, o bug está no parser novo |
| **Múltiplos PDFs ANTIGO com formatos inconsistentes** | Média | Médio — snapshots não representativos | Coletar o máximo de PDFs possível; priorizar diversidade de meses/anos |
| **`relatorioverde.py` do legado não é importável** em Python 3.14 | Baixa | Bloqueante — teste não roda | Testar import primeiro: `python -c "import relatorioverde"` |
| **Snapshots existentes do CataFácil são sobrescritos** acidentalmente | Nula | Alto | O código salva em subpastas separadas (`catafacil/` vs `antigo/`); sem risco de colisão |
| **`exemplo_relatorio.pdf` é detectado como ANTIGO** e causa falsos positivos | Alta | Baixo | O PDF está em `docs/`, não em `EcoMetric/`; o teste só varre a pasta `EcoMetric/` |

---

## 7. Estimativa Final

| Item | Estimativa |
|------|-----------|
| Alterações de código necessárias | **0** (zero) |
| Alterações de infraestrutura | **0** (zero) |
| PDFs ANTIGO disponíveis no repositório | **0** (zero) |
| PDFs ANTIGO necessários | **1+** (idealmente 3-5 de meses/anos diferentes) |
| Tempo para obter PDFs do cliente | Variável (externo) |
| Tempo para executar e validar | **~5 minutos** |
| Cobertura após conclusão | **100%** dos modelos de PDF suportados |

### Estado atual do bloqueador

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   BLOQUEADOR: Ausência de PDFs reais do modelo      │
│   ANTIGO no repositório.                            │
│                                                     │
│   Este é um bloqueador EXTERNO — não depende de     │
│   código, implementação ou infraestrutura.          │
│                                                     │
│   Ação: Obter PDFs ANTIGO do cliente ACAMARTI.      │
│                                                     │
└─────────────────────────────────────────────────────┘
```
