# DOC — app/paths.py

## Objetivo

Resolver a raiz de recursos da UI/assets em desenvolvimento e em build PyInstaller frozen.

## Dependências

- `sys` (`frozen`, `_MEIPASS`)

## Lógica central

- Se `sys.frozen` e `_MEIPASS` existem → raiz = `Path(sys._MEIPASS)`.
- Caso contrário → pasta pai de `app/` (raiz do repositório).

## Assinaturas

| Função | Retorno |
|--------|---------|
| `project_root() -> Path` | raiz de recursos |
| `ui_dir() -> Path` | `.../ui` |
| `assets_dir() -> Path` | `.../assets` |
| `locales_dir() -> Path` | `.../ui/locales` |
