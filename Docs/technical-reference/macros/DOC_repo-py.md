# DOC — macros/repo.py

## Objetivo

Persistir, listar, carregar e excluir macros gravadas em `{user_data_dir()}/macros/`.

## Dependências

- `app.paths.user_data_dir`, `app.fsutil.atomic_write_json`
- `core.errors.ClickrError`
- `profiles.repo.ProfilesRepo` (regras de nome)
- `json`, `pathlib` (stdlib)

## Lógica central

- Arquivo: `{nome}.json` com `{"name", "version": 1, "events": [...]}`.
- Regras de nome iguais às dos perfis: `validate_new_name` ao gravar (inclui nomes reservados do Windows); validação de formato ao ler/excluir.
- `validate_events`: lista com até `MAX_EVENTS` (200 000) itens; cada item é dict com `kind` em `mouse_move`, `mouse_down`, `mouse_up`, `mouse_scroll`, `key_down`, `key_up` e `t` numérico ≥ 0. Fora disso → `macro.invalidFile`.
- `save` recusa lista vazia (`macro.empty`) e grava de forma atômica (sobrescreve macro de mesmo nome).
- `load` aceita também um arquivo que seja só a lista de eventos; inexistente → `macro.notFound`; JSON inválido → `macro.invalidFile`.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `MacrosRepo(root=None)` | diretório opcional | instância |
| `list_macros()` | — | `list[str]` ordenada (sem diferenciar maiúsculas) |
| `exists(name)` | nome | `bool` |
| `save(name, events)` | nome + lista | nome salvo |
| `load(name)` | nome | lista de eventos validada |
| `delete(name)` | nome | nome excluído |
| `validate_events(events)` (função) | qualquer | lista de dicts (ou `ClickrError`) |
| `root` | — | diretório das macros |
