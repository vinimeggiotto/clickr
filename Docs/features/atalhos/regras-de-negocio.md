# Feature: Atalhos globais

## Objetivo

Dar a cada ação principal um atalho global próprio (tecla ou combinação), gravável pela UI, e permitir que o atalho de iniciar/parar funcione no modo "segurar".

## Ações

| Ação | Rótulo na UI | Padrão | Efeito |
|------|--------------|--------|--------|
| `toggle` | Iniciar / parar | `F6` | Para a macro em reprodução ou o script, se houver; senão alterna o motor (ou segura, ver abaixo). Ignorado durante gravação de macro |
| `stop_all` | Parar tudo | — | Fecha a captura de ponto, para gravação e reprodução de macro, script e motor |
| `pick_point` | Capturar ponto no cursor | — | Grava a posição atual do cursor como ponto fixo |
| `macro_record` | Gravar / parar macro | — | Inicia a gravação (parando motor, macro e script) ou encerra a gravação em curso |

## Combinações

1. Formato: modificadores + **uma** tecla principal, separados por `+` (ex.: `F6`, `CTRL+ALT+F6`, `SHIFT+A`).
2. Modificadores: `CTRL`, `ALT`, `SHIFT`, `WIN` (lados esquerdo/direito e aliases como `CONTROL`, `ALTGR`, `CMD`, `SUPER`, `META` são reduzidos à família).
3. A tecla principal não pode ser um modificador. Teclas aceitas: F1–F24, letras, dígitos, teclas nomeadas (Space, Enter, Tab, Esc, setas, Home/End, Page Up/Down, Insert/Delete, Pause…), pontuação do layout US e teclado numérico (`NUM0`–`NUM9`, `NUM+` …).
4. O texto é normalizado para a forma canônica (maiúsculas, modificadores na ordem CTRL, ALT, SHIFT, WIN).

## Gravação pela UI

1. Clique no keycap da ação (aba **Atalhos**, ou o keycap do rodapé para iniciar/parar) → `record_hotkey(action)`; o estado passa a `recording_hotkey = true` e `recording_hotkey_action = <ação>`.
2. A próxima tecla não modificadora pressionada, junto com os modificadores segurados, vira o atalho.
3. `Esc` sozinho, ou clicar de novo no keycap, cancela (`cancel_record_hotkey`).
4. Enquanto a gravação está aberta, **todos** os atalhos ficam suspensos.
5. O botão × ao lado do atalho remove (`clear_hotkey(action)`); `set_hotkey(action, combo)` define por texto.

## Regras

1. O atalho de iniciar/parar não pode ficar vazio (`hotkey.toggleRequired`).
2. Dois atalhos não podem usar a mesma combinação (`hotkey.conflict`, com a ação que já a usa).
3. Combinação inválida → `hotkey.unsupported`; ação desconhecida → `hotkey.unknownAction`. Em qualquer erro o atalho anterior é mantido.
4. Os atalhos são preferências do aplicativo (`settings.json` → `hotkeys`), não fazem parte dos perfis. Ao abrir o app, combinações salvas inválidas ou repetidas são descartadas; o de iniciar/parar volta a `F6`.
5. Durante a captura de ponto (overlay aberto) só **Parar tudo** age.
6. Auto-repetição do teclado não dispara o atalho de novo: uma ação por pressionamento.
7. As ações rodam em thread própria, fora do hook de teclado.

## Plataformas

| SO | Mecanismo | Observação |
|----|-----------|------------|
| Windows | `RegisterHotKey` | A combinação é consumida pelo sistema e **não chega** ao programa em foco. Se o Windows recusar o registro (já usada por outro programa ou reservada), aquela ação passa a ser observada por um listener `pynput`, que não bloqueia a tecla |
| macOS / Linux | listener `pynput` | A tecla também chega ao programa em foco |

A gravação do atalho usa um listener `pynput` em todos os SOs.

## Modo de ativação (segurar para clicar)

- Preferência `activation`: `toggle` (ALTERNAR, padrão) ou `hold` (SEGURAR). Vale só para o atalho de iniciar/parar.
- **ALTERNAR:** uma pressão inicia, outra para.
- **SEGURAR:** o motor inicia ao pressionar e para quando a tecla principal do atalho é solta (o estado da tecla é consultado a cada ~10 ms). Se o motor já estiver rodando quando o atalho é pressionado, ele é parado.
- No modo SEGURAR o atalho continua parando macro/script em execução, como no modo ALTERNAR.
- O botão pulse da UI e a bandeja continuam alternando normalmente.

## Bridge

| Método | Papel |
|--------|--------|
| `record_hotkey(action="toggle")` / `cancel_record_hotkey()` | gravação pelo teclado |
| `set_hotkey(action, combo)` / `clear_hotkey(action)` | define por texto / remove |
| `set_preferences({ activation })` | modo de ativação |

Estado: `get_state().settings.hotkeys` (mapa ação → combinação, vazio = sem atalho), `settings.activation`, `recording_hotkey`, `recording_hotkey_action`.

## UI

Aba **Atalhos**: uma linha por ação (keycap + × para remover, exceto iniciar/parar), dica de uso e o seletor ALTERNAR / SEGURAR com a explicação do modo escolhido.
