# Feature: Instância única

## Objetivo

Impedir dois Clickr rodando ao mesmo tempo para o mesmo usuário (dois motores, atalhos duplicados, gravações concorrentes no mesmo `settings.json`).

## Comportamento

1. Ao abrir, o app tenta adquirir uma trava:

| SO | Trava |
|----|-------|
| Windows | Mutex nomeado `Local\Clickr.SingleInstance.v1` |
| macOS / Linux | `flock` exclusivo em `{user_data_dir()}/clickr.lock` |

2. Se a trava já pertence a outro processo, a nova instância grava o arquivo `{user_data_dir()}/show.request` e **encerra** sem criar janela.
3. A instância principal verifica esse arquivo a cada 0,5 s; ao encontrá-lo, apaga-o e mostra/restaura a própria janela.
4. A trava é liberada quando o app encerra.

## Regras

- Se a trava não puder ser criada (diretório de dados indisponível, falha ao criar o mutex ou abrir o arquivo), o app **abre normalmente** — a proteção nunca impede o uso.
- Um pedido de exibição antigo, deixado antes de a instância principal começar a observar, é descartado.
- Vale também para o início automático com `--minimized`: abrir o Clickr manualmente depois traz a janela da instância que já está na bandeja.
