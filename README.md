# Clickr

![Version](https://img.shields.io/badge/version-1.0.0-f59e0b?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-0ea5e9?style=flat-square)
![Python](https://img.shields.io/badge/python-3.12-3776ab?style=flat-square&logo=python&logoColor=white)
![UI](https://img.shields.io/badge/UI-pywebview-1f2937?style=flat-square)
![i18n](https://img.shields.io/badge/i18n-6%20locales-10b981?style=flat-square)
![Build](https://img.shields.io/github/actions/workflow/status/vinimeggiotto/clickr/build.yml?style=flat-square&label=build)
![License](https://img.shields.io/badge/license-as%20is-6b7280?style=flat-square)

**Autoclicker desktop multiplataforma** — UI amber no estilo “device”, motor de input nativo (SendInput no Windows; pynput no macOS/Linux), hotkeys, perfis, macros, scripts e agenda.

**Versão 1.0.0** · Repositório: [vinimeggiotto/clickr](https://github.com/vinimeggiotto/clickr)

---

## Aviso legal e uso responsável

- O Clickr envia cliques e teclas ao sistema operacional. Use apenas onde você tem autorização.
- Em jogos online e softwares com **anti-cheat**, autoclickers e macros costumam violar os termos de uso e podem resultar em banimento. O Clickr **não** contorna anti-cheat nem ofusca input.
- Você é responsável pelo uso. O autor não se responsabiliza por sanções, perda de conta ou danos decorrentes do uso inadequado.
- No Windows, janelas elevadas (administrador) podem ignorar o input se o Clickr não estiver elevado.

---

## Recursos

| Área | O que faz |
|------|-----------|
| **Clique** | Botão L/R/M/4/5 · simples / duplo / hold · intervalo em ms · CPS estimado |
| **Run** | Start/stop · hotkey global (padrão **F6**) · modo compacto · always-on-top |
| **Point** | Cursor ou ponto fixo · captura multi-monitor · sequência de pontos |
| **Perfis** | Salvar / carregar / importar / exportar JSON |
| **Manual** | **Guia** (explica) e **Assistente** (configura e salva perfil) |
| **Adv** | Filtro de janela, jitter, burst, limites |
| **Macro** | Gravar e reproduzir via fachada de input |
| **Script** | DSL `click` / `move` / `wait` / `key` / `loop` |
| **Agenda** | Disparo em data/hora local |
| **Bandeja** | Fechar a janela oculta o app; **Sair** encerra de verdade |
| **Idiomas** | Português, English, Español, Deutsch, 中文, Русский |

---

## Requisitos

| SO | Notas |
|----|--------|
| **Windows** 10/11 | Backend SendInput; executável `Clickr.exe` |
| **macOS** | Autorizar **Acessibilidade** (Ajustes → Privacidade). Binário sem notarização pode exigir “Abrir mesmo assim” no Gatekeeper |
| **Linux** | Sessão **X11** (Wayland: limitação conhecida). Runtime: GTK/WebKit (pywebview). Filtro de janela: `xprop` (e opcionalmente `xdotool`) |

- Código-fonte: **Python 3.12** + `requirements.txt`
- Artefatos de CI não exigem Python instalado no destino

---

## Como usar

1. Abra o Clickr (artefato da plataforma ou `python main.py`).
2. Na primeira vez, escolha o idioma (pode mudar depois no seletor do topo).
3. Configure o clique nas abas e use o botão pulse ou a hotkey (**F6** por padrão).
4. Para encerrar de verdade: ícone na bandeja → **Sair**.

Preferências e perfis:

| SO | Pasta |
|----|--------|
| Windows | `%APPDATA%\Clickr\` |
| macOS | `~/Library/Application Support/Clickr/` |
| Linux | `$XDG_CONFIG_HOME/Clickr/` ou `~/.config/Clickr/` |

### DSL de script (exemplo)

```text
move 100 200
click left
wait 100
key SPACE
loop 3
  click
  wait 50
end
```

Limites: até 500 linhas, loops 1–1000, profundidade de loop ≤ 2.

---

## Rodar pelo código-fonte

```bash
python -m pip install -r requirements.txt
python main.py
```

No Windows (PowerShell):

```powershell
python -m pip install -r requirements.txt
python main.py
```

---

## Gerar o executável / app

PyInstaller **não cross-compila**. Use o script do SO alvo (ou o CI).

| SO | Comando | Saída |
|----|---------|--------|
| Windows | `.\build_exe.ps1` | `dist\Clickr.exe` |
| macOS | `./build_macos.sh` | `dist/Clickr.app` |
| Linux | `./build_linux.sh` | `dist/Clickr` |

Specs: `packaging/Clickr.windows.spec`, `packaging/Clickr.macos.spec`, `packaging/Clickr.linux.spec`.

Os scripts regeneram o ícone (`scripts/generate_icon.py`) antes do PyInstaller.

### CI e releases

Workflow [`.github/workflows/build.yml`](.github/workflows/build.yml): matrix Windows / macOS / Linux.

- Push/PR: sobe artifacts por plataforma
- Tag `v*`: publica os três artefatos na GitHub Release

---

## Limitações conhecidas

- **macOS Gatekeeper / notarização:** não incluídos nesta entrega; pode ser necessário liberar o app manualmente.
- **Linux Wayland:** input sintético e filtro de janela focados em X11.
- **Botões X1/X2:** suporte completo no Windows; em macOS/Linux depende do pynput.
- Sem `xprop` no Linux, filtro de janela **com critérios** falha com erro explícito (não libera clique).

---

## Estrutura

```text
app/           Controller, tray, bootstrap, settings, paths
core/          Motor + fachada sendinput (win32 / pynput)
hotkeys/       Hotkey global
profiles/      Persistência de perfis
macros/        Gravação e reprodução
scripts/       DSL runner
scheduler/     Agenda
window_filter/ Filtro de janela por SO
ui/            Interface (HTML/CSS/JS) e idiomas
assets/        Ícones e logos
packaging/     Specs PyInstaller por SO
Docs/          Documentação do projeto
```

---

## Licença

Software fornecido **“como está”**, sem garantia. Uso por sua conta e risco.
