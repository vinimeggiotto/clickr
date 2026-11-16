# DOC — app/fsutil.py

## Objetivo

Gravar arquivos de texto/JSON de forma atômica, para que uma interrupção no meio da escrita não deixe `settings.json`, perfis ou macros truncados.

## Dependências

- `json`, `os`, `tempfile`, `pathlib` (stdlib)

## Lógica central

- Cria o diretório de destino se necessário.
- Escreve em arquivo temporário no **mesmo diretório** (`.{nome}.*.tmp`), faz `flush` + `fsync` (falha de `fsync` é tolerada) e troca com `os.replace`.
- Em qualquer erro, remove o temporário e propaga a exceção; o arquivo original permanece intacto.
- JSON gravado com `ensure_ascii=False` e indentação de 2 espaços (UTF-8).

## Assinaturas

| Função | Entrada | Saída |
|--------|---------|--------|
| `atomic_write_text(path, text)` | `Path` + str | — (levanta `OSError` em falha) |
| `atomic_write_json(path, payload)` | `Path` + objeto serializável | — |
