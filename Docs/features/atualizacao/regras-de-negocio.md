# Feature: Aviso de nova versão

## Objetivo

Avisar, de forma opcional, quando existir uma versão mais nova publicada nas Releases do projeto no GitHub.

## Comportamento

1. **Desligado por padrão.** Só consulta a rede se o usuário ligar **Avisar quando houver versão nova** (aba Run, preferência `check_updates`).
2. Com a opção ligada, a consulta acontece ao abrir o app e no momento em que a opção é ligada. `check_updates_now()` força uma consulta independentemente da opção.
3. A consulta é um GET anônimo à API pública de releases (`/repos/vinimeggiotto/clickr/releases/latest`), com timeout de 6 s, em thread separada. Nenhum dado do usuário ou da máquina é enviado.
4. Compara a tag da release com a versão do arquivo `VERSION` (numericamente, parte a parte; sufixos após `-` são ignorados). Rascunhos e pré-releases não contam.
5. Havendo versão mais nova, o estado passa a trazer `update = { version, url }` e o rodapé mostra um selo com a versão.
6. Clicar no selo chama `open_update_page()`, que abre a página da release no navegador padrão.

## Regras

- O app **não** baixa nem instala nada: apenas avisa e abre a página.
- O link aberto é sempre da página de releases do próprio projeto; qualquer outra URL vinda da resposta é trocada pela página geral de releases.
- Falha de rede ou resposta inesperada é registrada no log e não gera erro na UI.
- Uma consulta por vez (chamadas durante uma consulta em andamento são ignoradas).
