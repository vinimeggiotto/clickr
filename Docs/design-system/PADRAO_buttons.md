# Padrão — Buttons

## Pulse (primário)

- Círculo ~76–84px no stage.
- Idle: radial escuro, ícone play amber.
- Ativo (`device.active`): fill amber, ícone stop, anel com animação `pulseRing`.
- Respeitar `prefers-reduced-motion` (anel estático).

## Segmented / tabs

- Container groove com padding 3px.
- Segmento ativo: gradiente `#3a2c19 → #2a2013`, texto `--amber`.
- Um valor ativo por grupo.
- Variante `.dense` para seletor de botão `L R M 4 5` (rótulos curtos).

## Action button

- Classe `.action-btn`: mesma linguagem do segmented ativo.
- Variante `.ghost`: fundo groove, texto dim (ações secundárias).
- Variante `.tiny`: padding reduzido para ações do editor de sequência.
- Uppercase, letter-spacing ~1.2px.

## Keycap (hotkey)

- Aparência de tecla física; clicável para gravar.
- Estado `.recording`: texto amber + pulso de sombra.

## Toggle

- Checkbox visualmente escondido + `.toggle-ui` (trilha 34×18).
- Ativo: knob amber deslocado à direita.

## Window controls (title bar)

- Classe `.win-btn`: 46×36, ícone fino, cor `--text-dim`.
- Hover genérico: fundo branco 6% + texto `--text`.
- Fechar (`.win-btn-close:hover`): fundo `--danger`, texto branco.
- Sem botão maximizar (janela tamanho fixo).
- À direita; arraste fica na região `.pywebview-drag-region` (não nos botões).
