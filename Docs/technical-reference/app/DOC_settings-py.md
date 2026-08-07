# DOC — app/settings.py

## Objetivo

Carregar e gravar preferências do aplicativo (hoje: `locale` da UI) em `{user_data_dir()}/settings.json`.

## Dependências

- `app.paths.user_data_dir`
- `json`, `pathlib`

## Lógica central

- Locales válidos: `pt-BR`, `en-US`, `zh-CN`, `de-DE`, `es-ES`, `ru-RU`.
- `load()` devolve `{"locale": code|null}`; locale inválido ou arquivo ausente → `null`.
- `set_locale(code)` valida, grava JSON com indentação e devolve o payload persistido.
- Separado de `profiles/` (presets de clique).

## Assinaturas

| Método | Entrada | Saída |
|--------|---------|--------|
| `AppSettings(path=None)` | `Path` opcional | instância |
| `load() -> dict` | — | settings normalizados |
| `save(settings) -> dict` | dict parcial | payload gravado |
| `get_locale() -> str\|None` | — | código ou `None` |
| `set_locale(code) -> dict` | BCP-47 | payload gravado; `ValueError` se inválido |
