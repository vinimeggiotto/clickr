# Clickr

![Version](https://img.shields.io/badge/version-1.0.0-f59e0b?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0ea5e9?style=flat-square)
![Python](https://img.shields.io/badge/python-3.12-3776ab?style=flat-square&logo=python&logoColor=white)
![UI](https://img.shields.io/badge/UI-pywebview-1f2937?style=flat-square)
![i18n](https://img.shields.io/badge/i18n-6%20locales-10b981?style=flat-square)
![License](https://img.shields.io/badge/license-as%20is-6b7280?style=flat-square)

**Autoclicker desktop para Windows** — UI amber no estilo “device”, motor de input nativo (`SendInput`), hotkeys, perfis, macros, scripts e agenda.

**Versão 1.0.0**

---

## Aviso legal e uso responsável

- O Clickr envia cliques e teclas ao sistema operacional. Use apenas onde você tem autorização.
- Em jogos online e softwares com **anti-cheat**, autoclickers e macros costumam violar os termos de uso e podem resultar em banimento. O Clickr **não** contorna anti-cheat nem ofusca input.
- Você é responsável pelo uso. O autor não se responsabiliza por sanções, perda de conta ou danos decorrentes do uso inadequado.
- Janelas elevadas (executando como administrador) podem ignorar o input se o Clickr não estiver elevado.

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
| **Macro** | Gravar e reproduzir com SendInput |
| **Script** | DSL `click` / `move` / `wait` / `key` / `loop` |
| **Agenda** | Disparo em data/hora local |
| **Bandeja** | Fechar a janela oculta o app; **Sair** encerra de verdade |
| **Idiomas** | Português, English, Español, Deutsch, 中文, Русский |

---

## Requisitos

- Windows 10 ou 11
- Para rodar pelo código-fonte: Python 3.12 e dependências em `requirements.txt`
- O executável (`Clickr.exe`) não exige Python instalado

---

## Como usar

1. Abra o Clickr (`Clickr.exe` ou `python main.py`).
2. Na primeira vez, escolha o idioma (pode mudar depois no seletor do topo).
3. Configure o clique nas abas e use o botão pulse ou a hotkey (**F6** por padrão).
4. Para encerrar de verdade: ícone na bandeja → **Sair**.

| Ação | Como |
|------|------|
| Start / stop | Botão pulse ou hotkey (gravável na UI) |
| Intervalo | Campo ms + fader; CPS estimado abaixo |
| Ponto fixo | Modo ponto fixo ou aba **Point** → Capturar |
| Sequência | Aba **Point** → adicionar pontos |
| Perfis | Aba **Perfis** |
| Macro / Script / Agenda | Abas correspondentes (ocultáveis no modo compacto) |

Preferências e perfis ficam em `%APPDATA%\Clickr\`.

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

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Gerar o executável

```powershell
.\build_exe.ps1
```

Saída: `dist\Clickr.exe`.

---

## Estrutura

```text
app/        Controller, tray, bootstrap, settings
core/       Motor e SendInput
hotkeys/    Hotkey global
profiles/   Persistência de perfis
macros/     Gravação e reprodução
scripts/    DSL runner
scheduler/  Agenda
ui/         Interface (HTML/CSS/JS) e idiomas
assets/     Ícones e logos
Docs/       Documentação do projeto
```

---

## Licença

Software fornecido **“como está”**, sem garantia. Uso por sua conta e risco.
