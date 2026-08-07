# DOC — ui/i18n.js

## Objetivo

Runtime de internacionalização no frontend: carregar catálogos JSON, resolver chaves com fallback `pt-BR`, aplicar atributos `data-i18n*` no DOM e notificar mudanças de locale.

## Dependências

- Catálogos em `ui/locales/{code}.json`
- `fetch` (mesmo origin da UI)

## Lógica central

- `t(key, vars?)`: resolve string (ou valor) por caminho pontilhado; fallback só para catálogo `pt-BR`; interpola `{nome}`.
- `tList(key)`: devolve array (ex.: corpos do Guia).
- `applyDom(root?)`: atualiza `data-i18n`, `data-i18n-html`, `data-i18n-placeholder`, `data-i18n-title`, `data-i18n-aria`.
- `setLocale(code)`: carrega catálogo, define `document.documentElement.lang`, aplica DOM e dispara listeners.

## Assinaturas

| API | Papel |
|-----|--------|
| `ClickrI18n.t(key, vars?)` | tradução |
| `ClickrI18n.tList(key)` | lista traduzida |
| `ClickrI18n.applyDom(root?)` | reaplica DOM |
| `ClickrI18n.loadLocale(code)` / `setLocale(code)` | carrega / aplica |
| `ClickrI18n.getLocale()` | código ativo |
| `ClickrI18n.fillLocaleSelect(el)` | popula `<select>` |
| `ClickrI18n.onChange(fn)` | callback pós-troca |
| `ClickrI18n.SUPPORTED` / `LABELS` / `FALLBACK` | constantes |
