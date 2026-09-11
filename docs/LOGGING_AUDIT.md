# EcoMetric 2.0 — Auditoria de Logging para Produção

**Data:** 13/06/2026
**Auditor:** Inspeção completa de todos os arquivos com `print()`, `logging` e `log_*`
**Status:** ✅ IMPLEMENTADO (13/06/2026)

---

## Estado da Implementação

| Etapa | Status | Arquivo |
|-------|--------|---------|
| 1. RotatingFileHandler em settings.py | ✅ | `config/settings.py` (+4 linhas) |
| 2. Remover print() do log_debug | ✅ | `core/logger.py` (-2 linhas) |
| 3. FileHandler na GUI | ✅ | `gui/app.py` (+12 linhas) |
| 4. Migrar main.py para log_*() | ✅ | `main.py` (+3 import, ~15 alterados) |
| 5. Testes de persistência | ✅ | `tests/test_logging.py` (novo, 9 testes) |

**Localização dos logs:** `%APPDATA%/EcoMetric/logs/ecometric.log`
**Formato:** `2026-06-13 12:30:36 [INFO] Mensagem`
**Rotação:** 5 backups de 1 MB cada

---

## 1. Estado Atual

### 1.1 `core/logger.py` — 23 linhas

```python
logger = logging.getLogger("EcoMetric")    # Logger nomeado central

def log_debug(msg):    # logger.debug() + print() se DEBUG=True
def log_info(msg):     # logger.info()
def log_warning(msg):  # logger.warning()
def log_error(msg):    # logger.error()
```

**Avaliação:** Implementação mínima funcional. O `print()` extra em `log_debug()` existe porque o StreamHandler pode não estar ativo (ex: GUI remove todos os handlers). Isso é uma **gambiarra corretiva** — indica que o sistema de logging está mal configurado.

### 1.2 `config/settings.py` — Configuração central

```python
LOG_LEVEL = logging.DEBUG if DEBUG else logging.WARNING
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()    # ÚNICO handler — stdout
    ]
)
```

**Avaliação:** Apenas `StreamHandler`. Sem `FileHandler`. Sem `RotatingFileHandler`. Sem configuração de diretório de logs.

### 1.3 Handlers Existentes

| Handler | Tipo | Destino | Persiste? |
|---------|------|---------|-----------|
| `StreamHandler` (settings.py) | stdout | Console/Terminal | **Não** |
| `QueueLogHandler` (gui/handlers) | Custom | GUI textbox | **Não** |
| `FileHandler` | — | **NÃO EXISTE** | — |
| `RotatingFileHandler` | — | **NÃO EXISTE** | — |

### 1.4 Resumo

```
Handler ativos por contexto:

┌──────────┬─────────────────────┬──────────────┐
│ Contexto │ Handlers            │ Persistência │
├──────────┼─────────────────────┼──────────────┤
│ CLI      │ StreamHandler       │ NÃO          │
│ GUI      │ QueueLogHandler     │ NÃO          │
│ Testes   │ StreamHandler       │ NÃO          │
│ Em .exe  │ QueueLogHandler     │ NÃO          │
└──────────┴─────────────────────┴──────────────┘
```

**Zero persistência em qualquer cenário.**

---

## 2. Fluxo de Logs — Mapeamento Completo

### 2.1 `main.py` (CLI)

```
27 chamadas de print() direto
0 chamadas de log_*()
0 uso de logging

Padrão: [INFO], [DEBUG], [ERRO] como prefixos manuais em f-strings
Exemplo: print(f"[ERRO] Arquivo não encontrado: '{caminho_pdf}'")
```

**Problema:** Ignora completamente o sistema de logging. Logs visíveis no terminal, mas não capturáveis por handlers.

### 2.2 `core/parsers/pdf_antigo.py`

```
3x print() — apenas sob DEBUG=True (dump de texto do PDF)
2x log_warning() — peso inválido
1x log_error() — falha na leitura do PDF
```

**Problema:** `print()` direto para debug. Se DEBUG=True em produção, o dump de páginas inteiras polui stdout. Se não há handler stdout (GUI), o dump é perdido.

### 2.3 `core/parsers/pdf_catafacil.py`

```
4x print() — dump de páginas (DEBUG) + lista de não classificados (DEBUG)
4x log_debug/log_error/log_warning
```

**Problema:** Mesmo do parser antigo. `print()` para debug, `log_*` para produção.

### 2.4 `core/exportador.py`

```
4x log_info/log_error — 100% via logger
0x print()
```

**Avaliação:** Correto. Usa apenas `log_*`.

### 2.5 `reports/pdf_generator.py`

```
4x log_info/log_warning/log_error — 100% via logger
0x print()
```

**Avaliação:** Correto. Usa apenas `log_*`.

### 2.6 `gui/app.py`

```
Configura logging no _setup_logging():
- Remove TODOS os handlers existentes do logger "EcoMetric"
- Adiciona QueueLogHandler (nível DEBUG)
- Define nível do logger como DEBUG

Logs aparecem na sidebar em tempo real.
ZERO persistência em disco.
```

### 2.7 `scripts/benchmark.py`

```
12x print() direto
0x log_*()
```

**Avaliação:** Ferramenta de diagnóstico; não é crítico para produção.

### 2.8 Matriz de cobertura

| Módulo | Usa logger? | Usa print()? | Persiste? |
|--------|-------------|-------------|-----------|
| `main.py` | **Não** | Sim (27x) | Não |
| `pdf_antigo.py` | Sim (log_warning/error) | Sim (3x debug) | Não |
| `pdf_catafacil.py` | Sim (todas) | Sim (4x debug) | Não |
| `exportador.py` | **Sim (100%)** | Não | Não |
| `pdf_generator.py` | **Sim (100%)** | Não | Não |
| `gui/app.py` | Sim (QueueHandler) | Não | Não |
| `benchmark.py` | Não | Sim (12x) | Não |

---

## 3. Persistência — Verificação

### 3.1 Algum log é salvo em disco atualmente?

**Não.** Nenhum `FileHandler` ou `RotatingFileHandler` em lugar nenhum.

### 3.2 Onde?

Não se aplica.

### 3.3 Qual formato?

Não se aplica.

### 3.4 Existe rotação?

Não.

---

## 4. Proposta de Hardening

### 4.1 Alternativas de localização

| Abordagem | Caminho | Vantagens | Desvantagens |
|-----------|---------|-----------|-------------|
| **A: Raiz do projeto** | `logs/ecometric.log` | Simples; visível para dev | Polui o diretório do app; permissões podem falhar em `Program Files`; não escala para múltiplos usuários |
| **B: %APPDATA%** | `%APPDATA%/EcoMetric/logs/ecometric.log` | Padrão Windows; isolado por usuário; permissões garantidas; não polui diretório do app | Caminho varia entre versões do Windows; invisível para usuário leigo |
| **C: %TEMP%** | `%TEMP%/EcoMetric/ecometric.log` | Sempre gravável; não polui | Apagado por limpeza de disco; não persiste entre reinicializações |

### 4.2 Recomendação: Abordagem B (%APPDATA%)

```
%APPDATA%/EcoMetric/
├── logs/
│   ├── ecometric.log        # Log atual
│   ├── ecometric.log.1      # Rotação 1 (mais recente)
│   ├── ecometric.log.2      # Rotação 2
│   ├── ecometric.log.3      # Rotação 3
│   ├── ecometric.log.4      # Rotação 4
│   └── ecometric.log.5      # Rotação 5 (mais antiga)
└── ecometric_gui_config.json  # Já existe (tema da GUI)
```

**Justificativa:**
- `%APPDATA%` é o local padrão Windows para dados de aplicação por usuário
- Não requer permissões de administrador
- O arquivo `ecometric_gui_config.json` **já está lá** — consistência
- Sobrevive a desinstalações/reinstalações
- Isolado por usuário da máquina

**Implementação:**
```python
import os
DIR_LOG = os.path.join(os.getenv('APPDATA'), 'EcoMetric', 'logs')
os.makedirs(DIR_LOG, exist_ok=True)
```

### 4.3 Configuração do RotatingFileHandler

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `maxBytes` | 1 MB (1.048.576) | Suficiente para semanas de uso normal |
| `backupCount` | 5 | 5 arquivos de rotação = ~6 MB máximo |
| `encoding` | `utf-8` | Suporte a caracteres acentuados (pt-BR) |
| Formato | `%(asctime)s [%(levelname)s] %(name)s: %(message)s` | Consistente com o StreamHandler atual |
| Nível | `INFO` em produção; `DEBUG` se `ECOMETRIC_DEBUG=true` | Não poluir com debug em produção |

---

## 5. Plano de Implementação

### Etapa 1: Configuração central do logger (`config/settings.py`)

**O que fazer:**
- Adicionar `RotatingFileHandler` ao `logging.basicConfig()`
- Definir `DIR_LOG` baseado em `%APPDATA%/EcoMetric/logs`
- Criar o diretório automaticamente
- Manter `StreamHandler` existente (útil para CLI/dev)
- Adicionar `FileHandler` como handler adicional (não substituto)

**Alteração necessária:**
```python
# settings.py — adicionar após a linha 57 (fim do basicConfig)

import logging.handlers

DIR_LOG = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'EcoMetric', 'logs')
os.makedirs(DIR_LOG, exist_ok=True)

file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(DIR_LOG, 'ecometric.log'),
    maxBytes=1_048_576,  # 1 MB
    backupCount=5,
    encoding='utf-8',
)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
))

# Adicionar ao logger raiz para capturar tudo
logging.getLogger().addHandler(file_handler)
```

**Arquivos tocados:** `config/settings.py` (+8 linhas)

### Etapa 2: Ajuste no `core/logger.py`

**O que fazer:**
- Remover `print(msg)` do `log_debug()` — não é mais necessário porque o `RotatingFileHandler` captura tudo
- Ajustar `log_debug()` para usar apenas `logger.debug()`

**Alteração necessária:**
```python
# logger.py — alterar log_debug

def log_debug(msg: str):
    """Loga mensagens de depuração."""
    logger.debug(msg)
    # print() removido — FileHandler cobre persistência
```

**Arquivos tocados:** `core/logger.py` (-2 linhas)

### Etapa 3: Integração GUI (`gui/app.py`)

**O que fazer:**
- **NÃO remover** o `QueueLogHandler` existente (ele alimenta a textbox)
- **NÃO remover** a lógica que limpa handlers antigos (evita duplicação)
- **ADICIONAR** um `RotatingFileHandler` ao logger "EcoMetric" no `_setup_logging()`

**Por que adicionar (não substituir):**
- O `QueueLogHandler` → textbox (visibilidade em tempo real)
- O novo `RotatingFileHandler` → disco (persistência para debug pós-crash)
- Ambos coexistem como handlers do mesmo logger

**Alteração necessária:**
```python
# app.py — em _setup_logging(), após adicionar gui_handler

file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(os.getenv('APPDATA', '~'), 'EcoMetric', 'logs', 'ecometric.log'),
    maxBytes=1_048_576, backupCount=5, encoding='utf-8',
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
))
core_logger.addHandler(file_handler)
```

**Arquivos tocados:** `gui/app.py` (+10 linhas)

### Etapa 4: Integração CLI (`main.py`)

**O que fazer:**
- Adicionar `import logging` e configurar o logger "EcoMetric" no início do `main()`
- Substituir `print()` por `log_info()` / `log_error()` / `log_debug()` onde fizer sentido
- **MANTER** `print()` para saída de dados (DataFrames, banners, prompts interativos)
- **SUBSTITUIR** `print()` para mensagens de status/erro por `log_*()`

**Regra de substituição:**
```
print(f"[INFO] ...")    → log_info(...)
print(f"[DEBUG] ...")   → log_debug(...)
print(f"[ERRO] ...")    → log_error(...)
print("[SUCESSO] ...")  → log_info(...)
print(df.to_string())   → MANTER print()  (saída de dados, não log)
print("=" * 60)         → MANTER print()  (banner visual)
```

**Arquivos tocados:** `main.py` (+3 linhas de import/config, ~20 linhas alteradas de print→log)

### Etapa 5: Testes

**O que testar:**
1. `RotatingFileHandler` cria arquivo em `%APPDATA%/EcoMetric/logs/`
2. Arquivo recebe entradas de `log_info()`, `log_warning()`, `log_error()`
3. Rotação funciona quando arquivo atinge 1 MB
4. Logs da GUI aparecem tanto na textbox quanto no arquivo
5. Logs da CLI aparecem tanto no terminal quanto no arquivo
6. `log_debug()` não chama mais `print()` (sem saída duplicada)
7. Testes existentes continuam passando (28/28)

**Arquivos tocados:** Novo arquivo `test_logging.py` (~30 linhas)

---

## 6. Compatibilidade

### 6.1 Contratos do core

| Contrato | Impacto |
|----------|---------|
| `log_info(msg)`, `log_warning(msg)`, `log_error(msg)` | **Nenhuma alteração** de assinatura ou comportamento externo |
| `log_debug(msg)` | Remove `print()` extra — **melhoria**, não quebra |
| `logger = logging.getLogger("EcoMetric")` | **Não alterado** |

### 6.2 Parsers

| Parser | Impacto |
|--------|---------|
| `pdf_antigo.py` | `print()` de debug permanece (controlado por `if DEBUG:`) |
| `pdf_catafacil.py` | `print()` de debug permanece (controlado por `if DEBUG:`) |
| `detector.py` | **Não usa logging nem print** |

**Nenhum parser sofre mudança funcional.**

### 6.3 Golden tests

| Teste | Impacto |
|-------|---------|
| `test_golden.py` | **Nenhum** — não depende de logging |
| Snapshots | **Nenhum** — não contêm dados de log |

### 6.4 GUI

| Componente | Impacto |
|------------|---------|
| `QueueLogHandler` | **Mantido** — textbox continua funcionando |
| `_setup_logging()` | **Estendido** — adiciona FileHandler, não remove nada |

---

## 7. Estimativa de Esforço

| Etapa | Arquivos | Linhas alteradas | Tempo |
|-------|----------|-----------------|-------|
| 1. Configuração central | `config/settings.py` | +8 | 10 min |
| 2. Ajuste logger.py | `core/logger.py` | -2 | 2 min |
| 3. Integração GUI | `gui/app.py` | +10 | 10 min |
| 4. Integração CLI | `main.py` | ~23 (3 import, 20 replace) | 15 min |
| 5. Testes | `test_logging.py` (novo) | ~30 | 15 min |
| **Total** | **4 modificados + 1 novo** | **~70 linhas** | **~50 min** |

---

## 8. Riscos

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| `%APPDATA%` não definido em Wine/Linux | Baixa | Fallback para `os.path.expanduser('~')` |
| Permissão negada ao criar `logs/` | Muito baixa | `%APPDATA%` é sempre gravável pelo usuário |
| Arquivo de log cresce indefinidamente | Nula | `RotatingFileHandler` limita a 5×1 MB |
| Conflito entre handlers (mensagens duplicadas) | Baixa | `gui/app.py` já remove handlers antigos antes de adicionar novos |
| `log_debug()` sem `print()` quebra fluxo existente | Nula | `log_debug()` é usado 2× (pdf_catafacil.py), ambas as chamadas vão para o logger igual |
| Testes existentes quebram | Nula | Nenhum teste depende de logging ou captura stdout |

---

## 9. Lista de Arquivos que Precisariam ser Modificados

| Arquivo | Ação | Linhas |
|---------|------|--------|
| `config/settings.py` | Adicionar RotatingFileHandler | +8 |
| `core/logger.py` | Remover print() do log_debug | -2 |
| `gui/app.py` | Adicionar FileHandler ao setup | +10 |
| `main.py` | Substituir print() por log_*() | ~23 |
| `test_logging.py` | **NOVO** — teste de persistência | +30 |
