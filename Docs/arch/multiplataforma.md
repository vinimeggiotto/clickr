# Multiplataforma — Clickr

## Escopo da 1ª entrega

Motor de clique, hotkey, tray, perfis, macro/script/agenda, UI pywebview e builds CI nos três SOs.

## Input

| SO | Backend |
|----|---------|
| Windows | Win32 `SendInput` |
| macOS / Linux | `pynput` |
| Testes / sem display | backend nulo (`CLICKR_INPUT_BACKEND=null`) |

## Diferenças por SO (1.1)

| Recurso | Windows | macOS / Linux |
|---------|---------|----------------|
| Atalhos globais | `RegisterHotKey` (tecla não chega ao programa em foco); reserva pynput para combos recusados | listener `pynput` (tecla também chega ao programa em foco) |
| Não clicar na própria janela | qualquer janela do processo sob o ponto | retângulo da janela principal visível |
| Não enviar teclas à própria janela | sim (janela em foco do processo) | consulta indisponível |
| Filtro de janela | consulta a cada ação | resultado reaproveitado por 250 ms |
| Instância única | mutex nomeado | `flock` em `clickr.lock` |
| Iniciar com o sistema | Registro `HKCU\…\Run` | LaunchAgent (macOS) / `autostart/clickr.desktop` (Linux) |
| Bandeja | thread própria | macOS: thread principal (`run_detached`) |
| Macro: código da tecla gravado | `vk` + nome (+ caractere) | nome (+ caractere) |

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

O job `test` roda a suíte pytest em `ubuntu-latest` com o backend de input nulo.

Em tags `v*`, o job `release` (depende de `test` e `build`) publica os artefatos multi-OS com [`softprops/action-gh-release`](https://github.com/softprops/action-gh-release) (`permissions.contents: write`): `Clickr.exe`, `Clickr.app.zip`, `Clickr` e `SHA256SUMS` (hashes dos três arquivos).

Fora de escopo desta entrega: notarização Apple, assinatura de código paga, cross-compile.

## Proteção de `main`

Template documentado (não autoaplicado): [`protecao-branch-main.md`](protecao-branch-main.md) + [`github-ruleset-main.json`](github-ruleset-main.json).
