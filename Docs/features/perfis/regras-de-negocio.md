# Feature: Perfis (presets)

## Objetivo

Persistir e restaurar configurações de clique do Clickr entre sessões, com renomear, excluir e import/export JSON.

## Armazenamento

- Diretório: `{user_data_dir()}/profiles/{nome}.json` (Windows: `%APPDATA%/Clickr`; macOS: `~/Library/Application Support/Clickr`; Linux: `$XDG_CONFIG_HOME/Clickr` ou `~/.config/Clickr`)
- Formato atual (versão 2): `{ "name": "...", "version": 2, "config": { ...ClickConfig } }`
- `config` guarda **só a configuração de clique** (intervalo, botão, tipo, posição, limites, burst, sequência, filtro de janela, `restore_cursor`, `position_jitter_px`, `action`, `key_name`). Atalhos, "sempre no topo" e modo compacto são preferências do aplicativo (`settings.json`).
- Gravação atômica (arquivo temporário + troca).

## Comportamento

| Ação | Bridge | Efeito |
|------|--------|--------|
| Listar | `list_profiles` / `get_settings().profiles` / campo `profiles` no retorno das ações de perfil | Nomes ordenados (sem diferenciar maiúsculas) |
| Salvar | `save_profile(name)` | Grava a config de clique atual no formato v2 (sobrescreve perfil de mesmo nome); devolve `saved_profile` |
| Carregar | `load_profile(name)` | Aplica o perfil no motor (ver compatibilidade abaixo) |
| Renomear | `rename_profile(old, new)` | Renomeia o arquivo preservando o conteúdo; devolve `renamed_profile` |
| Excluir | `delete_profile(name)` | Remove o arquivo; devolve `deleted_profile` |
| Exportar | `export_profile(name)` | Diálogo Salvar → JSON; devolve `exported_path` |
| Importar | `import_profile(name?)` | Diálogo Abrir → copia para a pasta de perfis e aplica; devolve `imported_profile` ou `import_conflict` |
| Confirmar importação | `import_profile_confirm()` | Conclui a importação pendente, sobrescrevendo o perfil existente |

## Regras

1. Nome: letras e números de qualquer idioma (unicode), espaço, `_` `.` `-`; 1–64 caracteres; deve começar com letra ou número. Caracteres `< > : " / \ | ? *` são recusados (`profile.invalidName`). Todo nome aceito pela 1.0.x continua aceito.
2. Ao **gravar** (salvar, renomear, importar, exportar), nomes reservados do Windows (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`, com ou sem extensão) são recusados (`profile.reservedName`). Ler ou excluir um arquivo que já exista com esse nome continua possível.
3. Carregar/importar inválido gera erro em `last_error` (`profile.notFound`, `profile.invalidFile`, `profile.fileNotFound`) — sem perfil “default” silencioso.
4. Carregar um perfil **v2** substitui a configuração de clique inteira: campos ausentes no arquivo voltam ao padrão.
5. Export com nome de perfil existente grava o arquivo salvo; senão exporta a config atual com esse nome (formato v2). Sem nome, usa `clickr-perfil`.
6. Import usa o nome informado, ou o `name` do JSON, ou o nome do arquivo (sem extensão).
7. **Importar não sobrescreve sem perguntar:** se já existe perfil com o nome resultante, nada é gravado; o estado volta com `import_conflict = <nome>`, a UI pede confirmação e só então chama `import_profile_confirm()`.
8. Renomear para um nome já usado por outro perfil → `profile.exists`. Mudar só maiúsculas/minúsculas do mesmo perfil é permitido.
9. Se o perfil renomeado for o alvo do agendamento ativo, o agendamento passa a apontar para o novo nome.
10. Excluir pede confirmação na UI.

## Compatibilidade com perfis da 1.0.x

A 1.0.x gravava perfis sem o campo `version` (formato **v1**). Esses arquivos continuam funcionando sem conversão:

| Situação | Regra |
|----------|-------|
| Reconhecimento | Arquivo sem `version` é v1 — com o envelope `{ "name", "config" }` **ou** só o dict de configuração "cru" (sem `config`). Com `version: 2` é v2. |
| Carga de v1 | Mesma mescla da 1.0.x: as chaves presentes no arquivo são aplicadas **sobre a configuração atual**; as chaves de clique que o arquivo não traz mantêm o valor atual. Chaves desconhecidas são ignoradas. |
| Campos novos (1.1) em v1 | `restore_cursor`, `position_jitter_px`, `action` e `key_name` não existiam na 1.0.x: ao carregar um v1 eles voltam ao padrão (sem restaurar cursor, 0 px, mouse, `SPACE`), reproduzindo o comportamento antigo. |
| Preferências em v1 | `hotkey`, `always_on_top` e `compact_mode` presentes no arquivo **continuam sendo aplicados** (o `hotkey` vira o atalho de iniciar/parar), como na 1.0.x. |
| Carga de v2 | **Nunca** altera preferências do aplicativo. Se um arquivo v2 trouxer `hotkey` / `always_on_top` / `compact_mode`, essas chaves são descartadas. |
| Reescrita | Arquivos legados **nunca são reescritos ao carregar**. Só mudam quando o usuário salva por cima (passa a v2). |
| Renomear v1 | O arquivo é copiado como está para o novo nome (continua v1, sem `version`); só o `name` do envelope, quando existe, é ajustado. |
| Importar / exportar v1 | A configuração é preservada integralmente, inclusive `hotkey` / `always_on_top` / `compact_mode`, e o arquivo continua v1 (sem `version`). É gravado no envelope `{ "name", "config" }` — um arquivo "cru" ganha o envelope. |

Se o `hotkey` de um perfil v1 for inválido ou já estiver em uso por outra ação, o restante do perfil é aplicado e o erro do atalho aparece em `last_error`.

## UI

Aba **Perfis**: nome, Salvar / Carregar, lista (duplo clique carrega; selecionar preenche o nome), **Renomear** (renomeia o perfil selecionado para o nome digitado), **Excluir**, Exportar / Importar.
