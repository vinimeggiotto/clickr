# DOC — app/updates.py

## Objetivo

Verificar, sob demanda, se há release mais nova do Clickr no GitHub. Só é chamado quando o usuário liga a opção (ou pede a consulta).

## Dependências

- `urllib.request`, `json`, `re` (stdlib) — sem bibliotecas de terceiros

## Lógica central

- Requisição: GET anônimo a `https://api.github.com/repos/vinimeggiotto/clickr/releases/latest`, cabeçalhos `Accept` e `User-Agent` fixos, timeout de 6 s. Não envia dado do usuário nem da máquina.
- `parse_version`: extrai até 4 números do trecho antes do primeiro `-` (`v1.2.3` → `(1, 2, 3)`).
- `is_newer`: compara as tuplas completando com zeros; se alguma for vazia → `False`.
- `check_latest`: ignora `draft` e `prerelease`; devolve `{"version", "url"}` se a tag for mais nova que a versão atual, senão `None`. Erros de rede/resposta levantam `OSError` / `ValueError` (o controller registra e segue).
- `safe_release_url`: só aceita URL que comece pela página de releases do próprio projeto; qualquer outra vira a página geral de releases.
- `fetch` é injetável em `check_latest` (testes sem rede).

## Assinaturas

| Símbolo | Entrada | Saída |
|---------|---------|--------|
| `parse_version(text)` | str | `tuple[int, ...]` |
| `is_newer(candidate, current)` | strs | `bool` |
| `check_latest(current_version, fetch=_fetch_latest)` | versão atual | `{"version", "url"}` ou `None` |
| `safe_release_url(url)` | qualquer | str |
| `REPO`, `RELEASES_API`, `RELEASES_PAGE` | — | constantes |
