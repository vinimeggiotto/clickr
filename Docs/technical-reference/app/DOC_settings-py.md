# DOC — app/settings.py

## Objetivo

Carregar e gravar as preferências do aplicativo — tudo o que não pertence a um perfil de clique — em `{user_data_dir()}/settings.json`.

## Dependências

- `app.paths.user_data_dir`
- `app.fsutil.atomic_write_json`
- `app.log`
- `json`, `copy`, `threading`, `pathlib`

## Lógica central

- `DEFAULT_SETTINGS` define as chaves conhecidas: `locale`, `hotkeys`, `activation`, `always_on_top`, `compact_mode`, `last_config`, `last_script`, `window_pos`, `manual_seen`, `tray_hint_shown`, `time_units`, `launch_at_login`, `check_updates`, `schedule`, `macro`.
- `_clean(key, value)` normaliza cada valor e devolve o padrão quando o tipo/conteúdo é inválido (locale fora da lista → `null`; atalhos em maiúsculas; `activation` ∈ `ACTIVATION_MODES`; `window_pos` = dois números; `time_units` ∈ `TIME_UNITS` por campo; `macro.repeat` 1–100 000, `macro.speed` 0,1–10, `macro.name` até 64; `last_script` até 100 000 caracteres).
- Leitura: arquivo ausente/ilegível → padrões (com aviso no log); chaves ausentes → padrão; chaves desconhecidas ficam em `_extra` e são **preservadas** ao gravar. Arquivos antigos (só `locale`) continuam válidos.
- Cópia em memória protegida por `RLock`; `load()` / `get()` devolvem cópias.
- `update(values)` grava na hora; `update(values, defer=True)` arma um único `Timer` de 0,5 s (`_SAVE_DEBOUNCE_S`) e agrupa as escritas seguintes; `flush()` grava o pendente.
- Escrita **atômica** via `atomic_write_json`; `OSError` é registrada no log e não propaga.
- Locales válidos: `pt-BR`, `en-US`, `zh-CN`, `de-DE`, `es-ES`, `ru-RU`.
- Separado de `profiles/` (presets de clique).

## Assinaturas

| Método / constante | Entrada | Saída |
|--------------------|---------|--------|
| `AppSettings(path=None)` | `Path` opcional | instância (já lê o arquivo) |
| `load() -> dict` | — | cópia de todas as chaves conhecidas |
| `get(key)` | nome da chave | cópia do valor |
| `pick(keys)` | tupla de chaves | cópia só das chaves pedidas (usado a cada montagem do estado da UI) |
| `update(values, defer=False) -> dict` | dict parcial | snapshot após aplicar |
| `save(settings) -> dict` | dict parcial | compatibilidade: equivale a `update` |
| `flush()` | — | grava pendências |
| `get_locale() -> str\|None` | — | código ou `None` |
| `set_locale(code) -> dict` | BCP-47 | snapshot; `ValueError` se inválido |
| `path` / `ensure_dir()` | — | caminho do arquivo / cria o diretório |
| `SUPPORTED_LOCALES`, `HOTKEY_ACTIONS`, `ACTIVATION_MODES`, `TIME_UNITS`, `TIME_UNIT_FIELDS`, `DEFAULT_SETTINGS`, `MAX_MACRO_REPEAT`, `MIN_MACRO_SPEED`, `MAX_MACRO_SPEED` | — | constantes |
