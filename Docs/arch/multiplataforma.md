# Multiplataforma — Clickr

## Escopo da 1ª entrega

Motor de clique, hotkey, tray, perfis, macro/script/agenda, UI pywebview e builds CI nos três SOs.

## Input

| SO | Backend |
|----|---------|
| Windows | Win32 `SendInput` |
| macOS / Linux | `pynput` |

## Dados do usuário

Ver `app.paths.user_data_dir()` e `Docs/arch/arquitetura-clickr.md`.

## Permissões e limitações

- **macOS Acessibilidade:** necessária para input sintético e (em muitos casos) leitura de UI via System Events.
- **macOS Gatekeeper:** binário sem notarização pode exigir abertura manual.
- **Linux X11:** caminho suportado; Wayland documentado como limitação.
- **Filtro Linux:** exige `xprop` quando o filtro está ativo com critérios.
- **X1/X2:** plenitude no Windows; demais SOs conforme pynput.

## Builds

Scripts na raiz + specs em `packaging/` (`Clickr.windows.spec`, `Clickr.macos.spec`, `Clickr.linux.spec`). CI: `.github/workflows/build.yml`.

Em tags `v*`, o job `release` publica os artefatos multi-OS com [`softprops/action-gh-release`](https://github.com/softprops/action-gh-release) (`permissions.contents: write`).

Fora de escopo desta entrega: notarização Apple, assinatura de código paga, cross-compile.
