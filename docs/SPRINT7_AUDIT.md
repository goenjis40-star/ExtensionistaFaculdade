# Sprint 7 — Auditoria Pré-Implementação

**Data:** 13/06/2026

## Estrutura atual dos períodos

`info_list[i]` contém `periodo` como string (ex: `"Maio 2025"`, `"Nao detectado"`).
A função `normalizar_periodo()` em `utils_periodo.py` converte para `(mes, ano)`.

## Estratégia

1. `auditar_periodos(info_list)` — analisa todos os períodos
2. Detecta: faltantes, duplicados, anos múltiplos
3. Integra em `meta["auditoria_periodo"]`
4. PDF anual mostra avisos se houver
5. Excel ganha aba `Auditoria_Consolidacao`
6. GUI mostra `messagebox.showwarning` se houver avisos
