# Feature: Filtro de janela

## Objetivo

Só emitir clique (ou tecla) quando a janela em foco atender aos critérios configurados.

## Configuração (`window_filter`)

| Campo | Tipo | Papel |
|-------|------|--------|
| `enabled` | bool | Liga/desliga a regra |
| `process` | string | Nome do executável / app / WM_CLASS (ex.: `notepad`, `Safari`, `firefox`) |
| `title_contains` | string | Substring no título da janela (case-insensitive) |

## Comportamento

1. `enabled = false` → todas as ações permitidas.
2. `enabled = true` sem `process` nem `title_contains` → permitido (sem critério ativo).
3. Critérios não vazios são **AND**: processo (se informado) e título (se informado) devem casar.
4. `allows() == false` → o motor **pula** a ação (não é contingência; é a regra do filtro) e o estado passa a `blocked = "filter"`.
5. Identificação da janela em foreground:

| SO | Mecanismo |
|----|-----------|
| Windows | `GetForegroundWindow` + título + basename do exe |
| macOS | `osascript` / System Events (nome do app + título da janela) |
| Linux | `xprop` (`_NET_ACTIVE_WINDOW`, `WM_CLASS`, nome); `xdotool` opcional para título |

6. Fora do Windows a consulta abre subprocessos; o resultado é reaproveitado por 250 ms para não distorcer o ritmo dos cliques. No Windows a consulta é feita a cada ação.

## Usar janela atual

1. Botão **Usar janela atual** (aba Adv) chama `capture_foreground_window(3)`.
2. O backend aguarda o tempo pedido (0,5–30 s; a UI usa 3 s) para o usuário trocar para a janela desejada; o estado expõe `window_capture = { active, ends_at }` e o botão mostra a contagem.
3. Ao fim, lê processo e título da janela em foco (sem cache) e grava `window_filter = { enabled: true, process, title_contains }`.
4. Clicar de novo durante a espera cancela (`cancel_capture_foreground_window`).
5. Erros:
   - janela em foco é o próprio Clickr (detectável no Windows) → `filter.ownWindow`;
   - falha ao consultar o SO → `filter.unavailable`;
   - nenhuma janela encontrada → `filter.noWindow`.

## Regras

- Processo: comparação case-insensitive; no Windows aceita com ou sem sufixo `.exe`.
- Falha ao obter processo/título com filtro ativo e critério correspondente → não permite o clique.
- Ferramenta ausente no Linux (`xprop`) ou macOS (`osascript`) com filtro ativo e critérios → **erro explícito** (`OSError`), sem liberar o clique.
- Sem retry nem “clicar em outra janela”.
- `set_config({ window_filter: {...} })` aceita patch parcial: os campos omitidos mantêm o valor atual.
