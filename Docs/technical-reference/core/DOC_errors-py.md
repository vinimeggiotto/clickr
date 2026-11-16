# DOC — core/errors.py

## Objetivo

Padronizar erros de domínio com **código estável**, para que a UI traduza a mensagem pela chave i18n `errors.<code>`.

## Dependências

- `typing` (stdlib)

## Lógica central

- Formato único de erro entregue à UI: `{"code": str, "message": str, "params": dict}`.
- `ClickrError` herda de `ValueError` (código existente que captura `ValueError` continua funcionando); carrega `code`, `message` (padrão = o próprio código) e `params` (interpolados na tradução, ex.: `line`, `name`, `key`).
- `error_from_exception`: `ClickrError` → seu dict; qualquer outra exceção → código `generic`, com o texto da exceção em `message` e em `params.detail`.
- `normalize_error`: aceita `None` / string vazia (→ `None`), dict (devolvido como está), exceção ou string (→ `generic`).
- Códigos em uso seguem o padrão `<área>.<motivo>`: `config.*`, `hotkey.*`, `key.*`, `sequence.*`, `macro.*`, `script.*`, `schedule.*`, `profile.*`, `filter.*`, `autostart.*`, além de `overlayMissing`, `alwaysOnTop` e `generic`.

## Assinaturas

| Símbolo | Entrada | Saída |
|---------|---------|--------|
| `ClickrError(code, message="", **params)` | código + texto + parâmetros | exceção |
| `ClickrError.to_dict()` | — | dict de erro |
| `error_dict(code, message="", **params)` | — | dict de erro |
| `error_from_exception(exc)` | exceção | dict de erro |
| `normalize_error(value)` | `None` / str / dict / exceção | dict de erro ou `None` |
