# DOC — app/notifier.py

## Objetivo

Entregar atualizações de estado à UI com limite de frequência, sem que threads de trabalho (motor, macro, script, hooks de input) fiquem bloqueadas pela UI.

## Dependências

- `threading` (stdlib)

## Lógica central

- `signal()` apenas arma um `Event` — é barato e pode ser chamado de qualquer thread, inclusive de callbacks de input.
- Uma thread daemon própria (`UiNotifier`) acorda com o evento, chama `push()` e então espera `min_interval_s` (padrão 1/15 s). Sinais recebidos nessa janela se acumulam em **um** push seguinte.
- Exceção em `push()` é engolida: o próximo sinal tenta de novo.
- `stop()` encerra a thread (join de até 1 s; não faz join se chamado da própria thread).

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `UiNotifier(push, min_interval_s=1/15)` | callable sem argumentos + intervalo | instância |
| `start()` | — | inicia a thread (idempotente) |
| `stop()` | — | encerra a thread |
| `signal()` | — | pede um push |
