# i18n — seleção de idioma

## Objetivo

Permitir que o usuário escolha o idioma da interface do Clickr (6 locales), com persistência em preferências do app e troca em tempo real pelo dropdown do nameplate.

## Locales suportados

| Código (BCP-47) | Rótulo no seletor (autônimo + região) |
|-----------------|----------------------------------------|
| `pt-BR` | Português (Brasil) |
| `en-US` | English (United States) |
| `zh-CN` | 中文 (中国) |
| `de-DE` | Deutsch (Deutschland) |
| `es-ES` | Español (España) |
| `ru-RU` | Русский (Россия) |

## Persistência

- Arquivo: `%APPDATA%/Clickr/settings.json`
- Campo: `locale` (string BCP-47 ou ausente/`null`)
- **Não** misturado com presets de clique em `profiles/`

## Fluxo de boot

1. Splash (~1,1s mínimo + bridge pronta).
2. Se `settings.locale` estiver vazio → overlay `#localeGate` (escolha obrigatória; confirmação ao clicar).
3. Escolha → `set_locale` → aplica catálogo na UI → segue boot (Assistente na 1ª vez, etc.).
4. Se já houver locale → aplica e segue.

## Troca em runtime

- Dropdown `#localeSelect` no nameplate (canto superior direito).
- Ao mudar: persiste, reaplica `data-i18n` / strings dinâmicas, re-render Manual/Assistente, atualiza menu da bandeja.

## Escopo traduzido

- Splash, titlebar, nameplate, abas, painéis, toggles, placeholders, footer, status, modal da bandeja.
- Overlay de captura, janela de info, Guia, Assistente e textos `(i)`.
- Menu da bandeja (Mostrar / Ocultar / Sair) e toast de “ainda rodando”.

## Fallback de chave

Se uma chave faltar no locale ativo, o runtime usa apenas o valor do catálogo `pt-BR` (sem outros fallbacks de negócio).

## Fora de escopo

- README / Docs do repositório (permanecem em PT-BR).
- Símbolos técnicos universais (L/R/M, F6, CPS, ms) podem permanecer; labels ao redor são traduzidos.
