# Versão do aplicativo

## Fonte da verdade

Arquivo [`VERSION`](../../../VERSION) na raiz do repositório (uma linha, semver, ex.: `1.0.0`).

## Exibição

- Splash: `#splashVersion` (`v` + versão)
- Rodapé do device: `#appVersion`

A UI obtém o valor via `get_settings().version` (`app.paths.app_version()`). Se `VERSION` estiver ilegível, o erro é registrado no log e a versão vem vazia (os elementos ficam ocultos).

O mesmo valor é a "versão atual" usada na verificação opcional de atualização (ver [`atualizacao`](../atualizacao/regras-de-negocio.md)).

## Empacote

Os specs em `packaging/` incluem `VERSION` nos `datas` do PyInstaller para leitura em runtime (`sys._MEIPASS`).

## Release

Ao publicar tag `vX.Y.Z`, manter o conteúdo de `VERSION` alinhado (ex.: `1.0.0` para tag `v1.0.0`).
