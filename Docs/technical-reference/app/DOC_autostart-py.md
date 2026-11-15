# DOC — app/autostart.py

## Objetivo

Registrar/remover o Clickr no início da sessão do usuário, por SO e sem privilégios de administrador.

## Dependências

- Windows: `winreg` (import tardio)
- macOS: `plistlib`
- `os`, `subprocess.list2cmdline`, `sys`, `pathlib`

## Lógica central

- `launch_command()`: build empacotado → `[sys.executable, "--minimized"]`; código-fonte → `[sys.executable, <repo>/main.py, "--minimized"]`.
- Windows: valor `Clickr` (`REG_SZ`) em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`; desligar apaga o valor (ausente não é erro).
- macOS: `~/Library/LaunchAgents/com.clickr.app.plist` com `Label`, `ProgramArguments`, `RunAtLoad`, `ProcessType = Interactive`.
- Linux: `$XDG_CONFIG_HOME/autostart/clickr.desktop` (ou `~/.config/autostart/`), com a linha `Exec` montada com as aspas do padrão `.desktop`.
- `is_enabled()` consulta a existência do registro/arquivo; `OSError` → `False`.
- `set_enabled()` levanta `OSError` se o SO recusar. `platform`, `home` e `command` são injetáveis (usados nos testes).

## Assinaturas

| Símbolo | Entrada | Saída |
|---------|---------|--------|
| `launch_command()` | — | `list[str]` |
| `is_enabled(platform=None, home=None)` | opcionais | `bool` |
| `set_enabled(enabled, platform=None, home=None, command=None)` | bool + opcionais | — (ou `OSError`) |
| `MINIMIZED_FLAG` | — | `"--minimized"` |
