# Versão do aplicativo

## Fonte da verdade

Arquivo [`VERSION`](../../../VERSION) na raiz do repositório (uma linha, semver, ex.: `1.0.0`).

## Exibição

- Splash: `#splashVersion` (`v` + versão)
- Rodapé do device: `#appVersion`

A UI obtém o valor via `get_settings().version` (`app.paths.app_version()`).

## Empacote

Os specs em `packaging/` incluem `VERSION` nos `datas` do PyInstaller para leitura em runtime (`sys._MEIPASS`).

## Release

Ao publicar tag `vX.Y.Z`, manter o conteúdo de `VERSION` alinhado (ex.: `1.0.0` para tag `v1.0.0`).
