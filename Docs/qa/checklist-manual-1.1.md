# Checklist de validação manual — Clickr 1.1.0

Os testes automatizados (`python -m pytest -q` e `node tests/ui/smoke.cjs`) rodam com um
backend de input nulo e dublês de pywebview/pynput. Tudo o que depende do sistema
operacional real precisa ser conferido à mão. Marque cada item no SO correspondente.

Preparação: `python -m pip install -r requirements.txt` e `python main.py` (ou o binário
gerado). O log fica em `{pasta de dados}/clickr.log`.

## Windows

### Compatibilidade com a 1.0.x
- [ ] Copiar uma pasta `%APPDATA%\Clickr` usada na 1.0.1 (com `settings.json` e perfis) e abrir a 1.1.0: o idioma é mantido e nenhum erro aparece.
- [ ] Carregar um perfil salvo na 1.0.1: intervalo, botão, tipo, posição, burst, sequência e filtro voltam; o atalho e "sempre no topo" daquele perfil também são aplicados.
- [ ] O arquivo do perfil antigo não muda de conteúdo só por ter sido carregado.
- [ ] Salvar um perfil novo e reabrir o JSON: tem `"version": 2` e não contém `hotkey`.

### Motor
- [ ] Iniciar pelo botão central no modo cursor: o rodapé mostra "alvo sobre o Clickr" e os cliques começam ao tirar o mouse de cima da janela.
- [ ] Intervalos de 1, 5 e 10 ms: a taxa "real" exibida fica próxima da teórica e o sistema continua responsivo.
- [ ] Limite de cliques e duração máxima: o motor para sozinho e a UI volta para "parado".
- [ ] Hold com botão direito, trocar para esquerdo com o motor ligado e parar: nenhum botão fica preso.
- [ ] Ponto fixo com "Devolver o cursor": dá para usar o mouse normalmente enquanto clica.
- [ ] Variação de posição: os cliques se espalham em volta do ponto.
- [ ] Modo Tecla com `E`, `SPACE` e `CTRL+C` em um editor de texto; Hold de tecla solta ao parar.
- [ ] Janela elevada (administrador) como alvo com o Clickr não elevado: comportamento esperado é o input ser ignorado.

### Atalhos
- [ ] F6 padrão inicia e para; a tecla **não** chega ao programa em foco.
- [ ] Gravar `Ctrl+Alt+F6` na aba Atalhos; Esc cancela a captura; × remove.
- [ ] Atribuir a mesma combinação a duas ações mostra o erro de conflito.
- [ ] Uma combinação já usada por outro programa continua funcionando (reserva por listener) — conferir a linha "usando reserva" no log.
- [ ] "Parar tudo" interrompe autoclique, macro em reprodução, script e captura.
- [ ] "Capturar ponto no cursor" grava o X/Y sob o mouse.
- [ ] Modo Segurar: clica só enquanto a tecla está pressionada; soltar para na hora.
- [ ] Segurar a tecla no modo Alternar não fica ligando/desligando (sem auto-repetição).

### Captura de ponto e multi-monitor
- [ ] Overlay de captura é translúcido: dá para ver a tela por baixo. Se aparecer opaco, registrar a versão do pywebview/WebView2.
- [ ] Com dois monitores (inclusive um à esquerda do principal, coordenadas negativas) e escalas de DPI diferentes, o ponto capturado é clicado no lugar certo.
- [ ] Fechar o overlay com Alt+F4: o botão "Capturar ponto" volta ao normal e os atalhos seguem funcionando.
- [ ] "Capturar" na sequência adiciona o ponto direto na lista.

### Macro e script
- [ ] Gravar digitando texto com acentos, pontuação, Shift, Ctrl+C / Ctrl+V e Alt+Tab; reproduzir repete tudo.
- [ ] Parar a reprodução no meio de uma tecla pressionada: nada fica preso (testar com Shift).
- [ ] Gravar/parar pelo atalho: a combinação do atalho não aparece na reprodução.
- [ ] O clique no botão "Parar gravação" não entra na macro.
- [ ] Rolagem do mouse é gravada e reproduzida.
- [ ] Repetições 3× e velocidade 2×; salvar, fechar o app, reabrir e carregar a macro.
- [ ] Script com `drag`, `scroll`, `type "olá mundo ç"`, `key CTRL+A` e `wait 100-300`; erro de sintaxe mostra a linha.

### Janela, bandeja e ciclo de vida
- [ ] Fechar no X: vai para a bandeja; o aviso aparece só na primeira vez.
- [ ] Menu da bandeja: Iniciar/Parar funciona e o ícone ganha o ponto verde enquanto ativo.
- [ ] Abrir o Clickr uma segunda vez: não abre outra janela; a primeira aparece.
- [ ] Mover a janela, sair pela bandeja e reabrir: a posição e a última configuração voltam.
- [ ] "Iniciar com o sistema": cria o valor `Clickr` em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`; após logon o app sobe na bandeja. Desligar remove o valor.
- [ ] "Avisar quando houver versão nova" ligado e sem internet: nenhum erro; com internet e versão mais nova publicada, o selo aparece no rodapé e abre a página de releases.
- [ ] Filtro de janela → "Usar janela atual": preenche processo e título após 3 s.
- [ ] Agendamento único, diário e "a cada"; suspender o PC antes do horário e retomar depois: dispara ao voltar.
- [ ] Executável gerado por `build_exe.ps1` abre, mostra v1.1.0 e passa pelos itens acima marcados como essenciais.

## macOS
- [ ] Com Acessibilidade e Monitoramento de Entrada concedidos: cliques, teclas e atalhos funcionam.
- [ ] Ícone na barra de menus aparece (o pystray é iniciado na thread principal); Mostrar/Ocultar/Sair funcionam.
- [ ] Fechar a janela não gera erro mesmo sem suporte a notificação.
- [ ] Captura de ponto com mais de um display.
- [ ] "Iniciar com o sistema" cria `~/Library/LaunchAgents/com.clickr.app.plist`.

## Linux (X11)
- [ ] Cliques, teclas e atalhos em sessão X11.
- [ ] Bandeja com AppIndicator/GTK disponível; sem bandeja, fechar a janela encerra o app.
- [ ] Filtro de janela com `xprop` instalado; sem ele, o erro é exibido e o motor para.
- [ ] "Iniciar com o sistema" cria `~/.config/autostart/clickr.desktop`.
