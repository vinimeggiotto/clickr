# Feature: Perfis (presets)

## Objetivo

Persistir e restaurar configurações do Clickr entre sessões, inclusive import/export JSON.

## Armazenamento

- Diretório: `{user_data_dir()}/profiles/{nome}.json` (Windows: `%APPDATA%/Clickr`; macOS: `~/Library/Application Support/Clickr`; Linux: `$XDG_CONFIG_HOME/Clickr` ou `~/.config/Clickr`)
- Formato: `{ "name": "...", "config": { ...ClickConfig } }`

## Comportamento

| Ação | Bridge | Efeito |
|------|--------|--------|
| Listar | `list_profiles` / embutido em `get_state` | Nomes ordenados |
| Salvar | `save_profile(name)` | Grava config atual (Tier 1+2) |
| Carregar | `load_profile(name)` | Aplica config + side-effects (hotkey, always-on-top) |
| Exportar | `export_profile(name)` | Diálogo Salvar → JSON |
| Importar | `import_profile(name?)` | Diálogo Abrir → salva em profiles e aplica |

## Regras

1. Nome: letras, números, espaço, `_` `.` `-`; 1–64 caracteres; deve começar com alfanumérico.
2. Carregar/importar inválido propaga erro em `last_error` — sem perfil “default” silencioso.
3. Export com nome de perfil existente grava o arquivo salvo; senão exporta a config atual com esse nome.
4. Import usa o nome informado, ou o `name` do JSON, ou o stem do arquivo.
