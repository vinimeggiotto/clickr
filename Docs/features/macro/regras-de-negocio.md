# Feature: Macro (gravar / reproduzir)

## Objetivo

Capturar uma sequência de eventos de mouse e teclado com timestamps, reproduzi-la pela fachada de input (com repetição e velocidade) e guardá-la em arquivo para reutilizar.

## Comportamento

1. **Gravar** inicia listeners `pynput` (mouse + teclado). Eventos: `mouse_move` (throttle ~16 ms), `mouse_down`/`mouse_up`, `mouse_scroll` (`dx`/`dy`), `key_down`/`key_up`.
2. Timestamps são relativos ao início da gravação (`perf_counter`).
3. Teclas são gravadas com nome estável (`key`) e, quando disponíveis, código virtual (`vk`, no Windows) e caractere (`char`). Isso permite reproduzir modificadores, pontuação e caracteres fora da tabela de nomes.
4. Cliques feitos sobre a própria janela do Clickr **não** entram na gravação.
5. **Parar gravação** fecha os listeners, limpa as pontas e mantém a lista em memória:
   - `key_up` / `mouse_up` sem o respectivo "down" anterior são descartados;
   - se existe atalho de **Gravar / parar macro**, os eventos das teclas desse atalho no fim da gravação são removidos (o atalho não entra na macro);
   - "down" sem "up" de outras teclas é mantido — o player solta tudo ao terminar.
6. **Reproduzir** despacha cada evento respeitando os tempos relativos divididos pela **velocidade**, e repete a lista **N vezes**.
   - Resolução da tecla: código gravado (Windows) → nome → caractere; se nenhuma servir, erro `macro.unsupportedKey`.
   - Entre repetições e ao terminar/ser interrompida, toda tecla ou botão ainda pressionado é solto.
7. Repetições: 1–100 000. Velocidade: 0,1×–10×. Ambos são preferências do app (valem entre sessões).
8. Atalho de iniciar/parar: ignorado durante a gravação; durante a reprodução **para** a macro.
9. Motor de autoclique e script são parados ao gravar/reproduzir (exclusão mútua no controller).
10. **Limpar** só é permitido com macro parada (senão `macro.busy`).
11. Reproduzir sem eventos → `macro.empty`.

## Salvar / carregar / excluir

- Arquivo: `{user_data_dir()}/macros/{nome}.json`, formato `{ "name", "version": 1, "events": [...] }`.
- Regras de nome iguais às dos perfis (letras/números de qualquer idioma, espaço, `_` `.` `-`, até 64 caracteres; nomes reservados do Windows recusados ao gravar).
- **Salvar** exige eventos (`macro.empty`) e gravação parada (`macro.busy`); grava de forma atômica e sobrescreve macro de mesmo nome.
- **Carregar** exige gravação e reprodução paradas; valida a estrutura (até 200 000 eventos, `kind` conhecido, `t` ≥ 0) — senão `macro.invalidFile`; inexistente → `macro.notFound`.
- **Excluir** remove o arquivo; a UI pede confirmação.
- O nome da última macro salva/carregada fica em `settings.macro.name`.

## Bridge

| Método | Papel |
|--------|--------|
| `macro_record_start` / `macro_record_stop` | gravação |
| `macro_play(repeat?, speed?)` / `macro_stop` | reprodução (omitidos = últimos valores) |
| `macro_set_options(repeat?, speed?)` | grava repetições/velocidade |
| `macro_clear` | limpa eventos |
| `macro_save(name)` / `macro_load(name)` / `macro_delete(name)` | arquivo; devolvem `macros` (lista) no estado |
| `list_macros()` | nomes ordenados |

Estado em `get_state().macro`: `recording`, `playing`, `event_count`, `duration_ms`, `iteration`, `repeat`, `speed`, `name`.

## UI

Aba **Macro** (oculta no modo compacto): Gravar / Reproduzir / Parar / Limpar, campos de repetições e velocidade, nome + Salvar / Carregar / Excluir e lista de macros salvas (duplo clique carrega). Durante a reprodução com mais de uma repetição, a dica mostra a rodada atual.
