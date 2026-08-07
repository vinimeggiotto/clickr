# Clickr

Autoclicker desktop para **Windows 10/11**, com UI amber no estilo device e motor de input nativo (`SendInput`).

## Aviso legal e uso responsável

- O Clickr envia cliques e teclas ao sistema operacional. Use apenas onde você tem autorização.
- Em jogos online e softwares com **anti-cheat**, autoclickers e macros costumam violar os termos de uso e podem resultar em banimento. O Clickr **não** contorna anti-cheat nem ofusca input.
- Você é responsável pelo uso. O autor não se responsabiliza por sanções, perda de conta ou danos decorrentes do uso inadequado.
- Janelas elevadas (executando como administrador) podem ignorar o input se o Clickr não estiver elevado — não há relaunch automático como admin.

## Requisitos

- Windows 10/11
- Python **3.12** (desenvolvimento)
- Dependências em `requirements.txt`

## Executar em desenvolvimento

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Empacotar `Clickr.exe`

```powershell
.\build_exe.ps1
```

Ou manualmente:

```powershell
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm Clickr.spec
```

Saída: `dist\Clickr.exe`. A UI e o ícone são embutidos; em runtime o app resolve recursos via `sys._MEIPASS` (`app/paths.py`).

## Uso rápido

| Ação | Como |
|------|------|
| Start/stop | Botão pulse ou hotkey (padrão **F6**, gravável no keycap) |
| Intervalo | Campo ms + fader; CPS estimado abaixo |
| Botão / tipo | Segmented L/R/M/4/5, simples/duplo/hold |
| Ponto fixo | Modo PONTO FIXO ou aba **Point** → Capturar |
| Sequência | Aba Point → + ponto |
| Avançado | Aba **Adv**: filtro de janela, burst |
| Perfis | Salvar/carregar/import/export JSON |
| Macro | Aba **Macro**: gravar → reproduzir (SendInput) |
| Script | Aba **Script**: DSL `click` / `move` / `wait` / `key` / `loop` |
| Agenda | Aba **Agenda**: data/hora local → inicia o motor |
| Compacto | Toggle em **Run** — esconde Adv / Macro / Script / Agenda |
| Manual | Aba **Manual** — **Guia** (explica) ou **Assistente** (configura + salva perfil + opcional ativar) |
| Bandeja | Fechar a janela oculta; **Sair** encerra pelo tray |

### DSL de script (exemplo)

```
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

## Estrutura

- `core/` — motor e SendInput
- `app/` — controller, tray, bootstrap
- `macros/`, `scheduler/`, `scripts/` — Tier 3
- `ui/` — HTML/CSS/JS do device
- `Docs/` — arquitetura, features, design system, referência técnica

## Licença / responsabilidade

Software fornecido “como está”, sem garantia. Uso por sua conta e risco.
