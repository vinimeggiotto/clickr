# Feature: Script DSL

## Objetivo

Executar uma mini-linguagem de ações (clique, movimento, arrasto, rolagem, espera, teclas, texto e loops limitados) pela fachada de input.

## Gramática (por linha)

| Comando | Forma | Efeito |
|---------|-------|--------|
| `click` | `click` \| `click BOTÃO` \| `click X Y` \| `click BOTÃO X Y` | clique (no cursor ou em XY) |
| `dclick` | mesmas formas de `click` | duplo clique |
| `move` | `move X Y` | move o cursor |
| `drag` | `drag X1 Y1 X2 Y2 [BOTÃO]` | pressiona em (X1,Y1), move em 12 passos (~180 ms) até (X2,Y2) e solta |
| `scroll` | `scroll N` | rola a roda N "cliques" (positivo = para cima, negativo = para baixo) |
| `wait` | `wait MS` \| `wait MIN-MAX` | espera fixa ou aleatória (inteiro uniforme entre MIN e MAX) |
| `key` | `key NOME` \| `key CTRL+C` | pressiona a tecla ou a combinação (pressiona na ordem, solta na ordem inversa) |
| `type` | `type "texto"` | digita o texto (aspas simples ou duplas opcionais; `\n`, `\t`, `\"`, `\'` aceitos; até 2000 caracteres) |
| `loop` | `loop N` … `end` | repete o bloco N vezes |

Comentários: linhas `# ...` ou vazias. Comandos não diferenciam maiúsculas/minúsculas.

## Limites

- Máx. 500 linhas
- Loop: N entre 1 e 1000
- Profundidade de loop ≤ 2
- Botões: `left`, `right`, `middle`, `x1`, `x2` (padrão `left`)
- `wait` não aceita valor negativo; em `MIN-MAX` invertido os valores são trocados

## Comportamento

1. Motor e macro (reprodução e gravação) são parados ao chamar `script_run`; o texto é guardado como `last_script`.
2. Parse falha → erro em `last_error` com código `script.*` e o **número da linha**; a thread não inicia.
3. Execução em thread dedicada; `script_stop`, o atalho de iniciar/parar ou **Parar tudo** interrompem.
4. O estado informa a linha em execução (`script.line`); erro durante a execução também leva o número da linha.
5. Ao terminar ou ser interrompido, botão/teclas que tenham ficado pressionados (arrasto, combinação) são soltos.
6. O texto do editor é salvo para a próxima sessão (`save_script`, com atraso) e restaurado no boot.

## Códigos de erro

`script.empty`, `script.tooLong`, `script.unknownCommand`, `script.usage`, `script.badNumber`, `script.badButton`, `script.badKey`, `script.negativeWait`, `script.loopRange`, `script.loopDepth`, `script.endWithoutLoop`, `script.loopNoEnd` — traduzidos pela UI (`errors.script.*`).

## Bridge

`script_run(source)` / `script_stop()` / `save_script(source)`. Estado: `get_state().script` → `running`, `line`.

## UI

Aba **Script** (oculta no modo compacto): textarea, botão **comandos** que abre a referência rápida da DSL, Executar / Parar e indicação da linha em execução.
