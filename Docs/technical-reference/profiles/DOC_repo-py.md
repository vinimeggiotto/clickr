# DOC — profiles/repo.py

## Objetivo

Persistir, listar, renomear, excluir, importar e exportar perfis de configuração em JSON sob `{user_data_dir()}/profiles/`.

## Dependências

- `app.paths.user_data_dir`, `app.fsutil.atomic_write_json`
- `core.errors.ClickrError`, `core.types.PROFILE_VERSION`
- `json`, `re`, `pathlib` (stdlib)

## Lógica central

- Arquivo: `{nome}.json`. Formato atual (v2): `{ "name", "version": 2, "config" }`.
- **Leitura (`_read_document`)** devolve sempre `{"name", "version", "config"}`:
  - com envelope (`config` é dict): `version` do arquivo, ou `1` se ausente/inválida;
  - sem envelope: o próprio dict é a config e a versão é `1` (formato "cru" da 1.0.x);
  - não é objeto JSON, ou `config` não é dict → `profile.invalidFile`. Lê UTF-8 com ou sem BOM.
- **Carregar não reescreve** o arquivo.
- **Escrita (`_export_payload`)**: `name`, depois `version` (omitida quando é 1 — um v1 exportado/importado continua v1) e `config`. Toda escrita é atômica.
- `save` grava no formato atual (`version = PROFILE_VERSION`).
- `rename` copia o documento como está (ajustando só o `name` do envelope) e apaga o antigo; nome de destino em uso por outro perfil → `profile.exists`; mudança só de maiúsculas/minúsculas é permitida.
- `import_from` lê o JSON externo, valida e grava na pasta de perfis com o nome resolvido, preservando a config (inclusive chaves legadas) e a versão. `resolve_import_name` calcula esse nome sem gravar: nome informado → `name` do arquivo → stem do path.
- **Nomes:** `_NAME_RE` (unicode) — começa com letra ou dígito; depois letras, dígitos, espaço, `_` `.` `-`; até 64 caracteres; `< > : " / \ | ? *` proibidos → `profile.invalidName`. `validate_new_name` (usada ao gravar) recusa também nomes reservados do Windows (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`, com ou sem extensão) → `profile.reservedName`. Ler/excluir usam só a validação de formato.

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `list_profiles()` | — | `list[str]` ordenada (sem diferenciar maiúsculas) |
| `save(name, config, version=PROFILE_VERSION)` | nome + dict | nome salvo |
| `load(name)` | nome | dict config |
| `load_document(name)` | nome | `{"name", "version", "config"}` |
| `delete(name)` | nome | nome excluído |
| `rename(old, new)` | nomes | novo nome |
| `export_to(name, dest)` | nome + Path | Path |
| `export_config(name, config, dest)` | nome + dict + Path | Path (formato v2) |
| `import_from(src, name=None)` | Path + nome opcional | nome salvo |
| `resolve_import_name(src, name=None)` | Path + nome opcional | nome que será usado |
| `exists(name)` | nome | `bool` |
| `validate_new_name(name)` (classmethod) | nome | nome limpo (ou `ClickrError`) |
| `root` / `ensure_dir()` | — | diretório / cria o diretório |
