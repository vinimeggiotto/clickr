# Política de segurança

## Como reportar uma vulnerabilidade

**Não** abra issue pública para falhas de segurança.

Use o **Private vulnerability reporting** / **Security advisories** deste repositório no GitHub:

1. Aba **Security** do repo → **Report a vulnerability**  
   (ou: Settings do repo → Code security → Private vulnerability reporting, se ainda não estiver ativo — ação do maintainer)
2. Em alternativa, contate o owner [@vinimeggiotto](https://github.com/vinimeggiotto) por mensagem privada no GitHub.

Inclua: descrição, impacto, passos para reproduzir e versão afetada (tag de release ou conteúdo de `VERSION`).

## Versões suportadas

Em geral, apenas a **última release** publicada (`v*`) recebe correções de segurança.

## O que está no escopo

Problemas no código ou no empacote do Clickr que permitam, por exemplo, comprometimento da máquina do usuário, execução indesejada de código ou exposição indevida de dados locais do app.

## Fora de escopo

- Uso do Clickr em violação de termos de terceiros (jogos, anti-cheat, etc.)
- Banimentos ou sanções decorrentes do uso do software
- Pedidos de recurso para contornar proteções de terceiros
- Relatos genéricos sem impacto de segurança (use issues de bug)

## Divulgação

Após correção e release, o maintainer pode publicar um advisory no GitHub. Não divulgue detalhes exploráveis publicamente antes disso.
