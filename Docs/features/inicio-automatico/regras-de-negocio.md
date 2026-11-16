# Feature: Iniciar com o sistema

## Objetivo

Abrir o Clickr automaticamente, minimizado na bandeja, quando o usuário entra na sessão do sistema operacional.

## Comportamento

1. Toggle **Iniciar com o sistema (na bandeja)** na aba Run → `set_preferences({ launch_at_login })`.
2. Ao ligar, o Clickr registra o próprio comando de execução com o argumento `--minimized`; ao desligar, remove o registro.

| SO | Registro (por usuário, sem privilégios de administrador) |
|----|-----------|
| Windows | Valor `Clickr` em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` |
| macOS | LaunchAgent `~/Library/LaunchAgents/com.clickr.app.plist` (`RunAtLoad`) |
| Linux | `$XDG_CONFIG_HOME/autostart/clickr.desktop` (ou `~/.config/autostart/`) |

3. O comando registrado é o executável empacotado, ou `python main.py` quando rodando pelo código-fonte.
4. Iniciado com `--minimized`, a janela principal é criada oculta e o app fica só na bandeja.
5. Se a bandeja não estiver disponível nesse início, a janela é mostrada (o app não pode ficar inalcançável).
6. A cada abertura, com a opção ligada, o registro é regravado para continuar apontando para o executável atual (caso o app tenha sido movido).

## Regras

- A preferência só é salva como ligada/desligada se o SO aceitar a alteração; em caso de falha, erro `autostart.failed` e o valor anterior permanece.
- Falha ao regravar o registro na abertura é apenas registrada no log.
- Uma segunda abertura (manual) com o app já rodando na bandeja traz a janela existente para frente (ver [`instancia-unica`](../instancia-unica/regras-de-negocio.md)).
