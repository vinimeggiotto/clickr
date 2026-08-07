# DOC — profiles/repo.py

## Objetivo

Persistir, listar, importar e exportar perfis de configuração em JSON sob `%APPDATA%/Clickr/profiles/`.

## Dependências

- `json`, `os`, `re`, `pathlib` (stdlib)

## Lógica central

- Arquivo: `{nome}.json` com envelope `{ "name", "config" }`.
- `export_to` / `export_config` gravam JSON em path arbitrário.
- `import_from` lê JSON externo, valida, salva no repositório e devolve o nome.
- Nome validado por regex alfanumérica (máx. 64).

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `list_profiles()` | — | `list[str]` |
| `save(name, config)` | nome + dict | nome salvo |
| `load(name)` | nome | dict config |
| `export_to(name, dest)` | nome + Path | Path |
| `export_config(name, config, dest)` | nome + dict + Path | Path |
| `import_from(src, name=None)` | Path + nome opcional | nome salvo |
| `exists(name)` | nome | `bool` |
