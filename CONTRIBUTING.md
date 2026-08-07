# Contribuindo com o Clickr

Obrigado pelo interesse em contribuir. Ao participar, você concorda com o [Código de Conduta](CODE_OF_CONDUCT.md) e com a [licença](LICENSE) do projeto (**PolyForm Noncommercial 1.0.0** — uso não comercial).

## Antes de começar

- Leia o [README](README.md), em especial o **aviso legal e uso responsável**.
- O Clickr não contorna anti-cheat nem ofusca input. Não abra PRs com esse objetivo.
- Dúvidas ou ideias: abra uma **issue** (use o template adequado).

## Fluxo (fork → PR)

A branch `main` é protegida: **não** faça push direto nela.

1. Faça um **fork** do repositório.
2. Clone o seu fork e crie uma branch a partir de `main`:
   ```powershell
   git clone https://github.com/SEU_USUARIO/clickr.git
   cd clickr
   git checkout -b minha-mudanca
   ```
3. Faça as alterações, teste localmente e faça commit.
4. Envie a branch e abra um **Pull Request** para `main` do repositório original (`vinimeggiotto/clickr`).
5. Aguarde o CI (**Build** em Windows / macOS / Linux) e a revisão do maintainer.

## Ambiente de desenvolvimento

Requisitos: Python **3.12**, Windows / macOS / Linux conforme a plataforma em que for testar.

```powershell
python -m pip install -r requirements.txt
python main.py
```

Builds locais (no SO correspondente):

| SO | Comando | Saída |
|----|---------|--------|
| Windows | `.\build_exe.ps1` | `dist\Clickr.exe` |
| macOS | `./build_macos.sh` | `dist/Clickr.app` |
| Linux | `./build_linux.sh` | `dist/Clickr` |

## Versão e documentação

- A versão do app vem do arquivo [`VERSION`](VERSION) (splash e rodapé).
- Se a mudança alterar comportamento de produto, atualize a doc em `Docs/` quando fizer sentido.
- Releases oficiais são feitas pelo maintainer via tag `v*` (não é necessário na maioria dos PRs).

## Escopo de PRs

Prefira PRs focados (um assunto por PR). Evite refatorações amplas sem combinado prévio na issue.

## Licença das contribuições

Ao enviar um PR, você concorda que sua contribuição seja licenciada sob os mesmos termos do projeto ([`LICENSE`](LICENSE)).
