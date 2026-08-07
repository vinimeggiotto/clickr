# DOC — app/paths.py

## Objetivo

Resolver a raiz de recursos da UI/assets (dev e PyInstaller frozen) e o diretório de dados do usuário por SO.

## Dependências

- `sys` (`frozen`, `_MEIPASS`, `platform`)
- `os.environ` (`APPDATA`, `XDG_CONFIG_HOME`)

## Lógica central

- Se `sys.frozen` e `_MEIPASS` existem → raiz de recursos = `Path(sys._MEIPASS)`.
- Caso contrário → pasta pai de `app/` (raiz do repositório).
- `app_version()` lê a primeira linha de `VERSION` em `project_root()` (obrigatório; erro se ausente/vazio). Em build, o arquivo entra nos `datas` do PyInstaller.
- `user_data_dir()`:
  - Windows: `%APPDATA%/Clickr` (erro se `APPDATA` ausente)
  - macOS: `~/Library/Application Support/Clickr`
  - Linux: `$XDG_CONFIG_HOME/Clickr` ou `~/.config/Clickr`

## Assinaturas

| Função | Retorno |
|--------|---------|
| `project_root() -> Path` | raiz de recursos |
| `ui_dir() -> Path` | `.../ui` |
| `assets_dir() -> Path` | `.../assets` |
| `locales_dir() -> Path` | `.../ui/locales` |
| `app_version() -> str` | semver do arquivo `VERSION` |
| `user_data_dir() -> Path` | pasta de prefs/perfis do usuário |
