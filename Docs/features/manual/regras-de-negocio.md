# Feature: Manual interativo + Assistente

## Objetivo

- **Guia:** explicar funcionalidades com navegação e “Experimentar” (só abre a aba).
- **Assistente:** wizard didático que configura o preset, salva perfil e opcionalmente inicia o motor.

## Comportamento — Guia

1. Modo **Guia** na aba Manual (toggle Guia / Assistente).
2. Passos com Anterior / Próximo; **Concluir** marca `clickr_manual_seen_v1` e volta para Clique.
3. **Experimentar** navega para a aba citada sem alterar config nem dar start.
4. Conteúdo do Guia/Assistente/INFO vem do catálogo i18n ativo (`ui/locales/{locale}.json`, chaves `manual.*`).

## Comportamento — Assistente

Passos (aplicam `set_config` ao avançar):

1. Boas-vindas  
2. Botão do mouse (L/R/M/4/5)  
3. Tipo (simples / duplo / hold)  
4. Intervalo + CPS  
5. Posição (cursor / ponto fixo + capturar)  
6. Limites opcionais (delay, jitter, max cliques, duração)  
7. Nome do perfil  
8. Final: **Só salvar** ou **Salvar e ativar** (+ dicas de onde editar depois)

- Salvar usa `save_profile`.
- Ativar chama `start` após salvar.
- Marca `clickr_wizard_done_v1` e `clickr_manual_seen_v1`.
- Primeira execução (nenhuma das flags): abre Manual no modo **Assistente**.

## Regras

- Guia não grava config nem inicia o motor.
- Assistente não configura Adv/Macro/Script/Agenda (apenas aponta no Guia).
- Explicações longas ficam no botão **(i)** → janela separada (`info.html`); texto do passo permanece curto.
- Sem dependências novas.
