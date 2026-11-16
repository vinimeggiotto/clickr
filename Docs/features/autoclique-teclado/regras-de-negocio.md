# Feature: Autoclique de teclado

## Objetivo

Repetir uma tecla ou combinação de teclas no mesmo motor do autoclique, com os mesmos controles de intervalo, limites e filtro.

## Configuração

| Campo | Valores | Papel |
|-------|---------|--------|
| `action` | `mouse` (padrão) \| `key` | O que o motor repete |
| `key_name` | ex.: `SPACE` (padrão), `E`, `F5`, `CTRL+C` | Tecla ou combinação; partes separadas por `+` |

## Comportamento

1. Com `action = key`, cada tick pressiona as teclas de `key_name` na ordem escrita e as solta na ordem inversa (`CTRL+C` = Ctrl ↓, C ↓, C ↑, Ctrl ↑).
2. Tipo **simples**: uma pressão por tick (conta 1). **Duplo**: duas pressões seguidas (conta 2). **Hold**: pressiona ao iniciar, mantém e solta ao parar (conta 1).
3. Intervalo, jitter de tempo, burst, delay de início, limite de ações e duração máxima funcionam como no mouse.
4. Filtro de janela vale igual: sem casar, a tecla não é enviada.
5. Botão do mouse, modo de posição, ponto fixo, sequência, jitter de posição e restaurar cursor **não se aplicam**; `sequence_index` fica `null`.
6. **Proteção da própria janela:** no Windows, a tecla não é enviada enquanto a janela em foco for do Clickr (`blocked = "own_window"`). Em macOS/Linux essa verificação não está disponível.
7. Diferente de um atalho, aqui cada parte é uma tecla realmente pressionada — modificadores sozinhos (`SHIFT`) são válidos.

## Captura da tecla

- Botão **capturar** → `capture_action_key()`: a próxima tecla/combinação pressionada vira `key_name` e `action` passa a `key`. Usa o mesmo mecanismo de gravação dos atalhos (`recording_hotkey_action = "action_key"`); `Esc` sozinho cancela.
- Também é possível digitar o nome no campo.

## Regras

- `key_name` é normalizado para maiúsculas; vazio vira `SPACE`.
- Nome inválido em `set_config` → erro `key.unsupported` e a tecla anterior é mantida (o restante da alteração é aplicado).
- `action` desconhecida é normalizada para `mouse`.
- Perfis da 1.0.x não têm esses campos: ao carregá-los, a ação volta a `mouse`.

## UI

Aba **Clique**: seletor **MOUSE / TECLA**. Em TECLA aparece o campo da tecla com o botão capturar, e somem o seletor de botão do mouse e o modo de posição.
