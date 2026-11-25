# Roteiro de Demonstração — AntiPiracy Defense Lab

> **Objetivo:** conduzir a equipe de engenharia do cliente por um fluxo completo
> de ataque **simulado** (dados 100% sintéticos) e, a cada etapa, mostrar onde a
> defesa entra. Tudo roda num servidor de teste controlado — nenhuma chave real,
> nenhum token real, nenhum conteúdo protegido.
>
> **Duração sugerida:** 20 a 30 minutos.
> **Público:** engenharia de segurança, produto e antifraude do provedor.

---

## Antes de começar (o contexto de 1 minuto)

Diga ao cliente:

> "O pirata não quebra criptografia — isso é matematicamente inviável. Ele **rouba
> o crachá (token)** e **pega a chave que ficou mal guardada na memória (DRM L3)**.
> Vamos mostrar isso acontecendo, etapa por etapa, e onde cada trava defensiva
> entra. Tudo aqui é simulado, com dados fictícios."

---

## ETAPA 1 — A credencial roubada

**O que mostrar:** a aba **"Conexão & Login"**.

**História:** o ataque começa com um usuário + senha que vazou (comprado em
lista, phished, ou o próprio assinante compartilhou).

**Ação no painel:** use a conta de teste `demo.valido` / `Sky2026@Ok`.

**Ponto de defesa (fale aqui):**
> "Nenhuma senha, por mais forte, sobrevive ao roubo. Por isso a segurança não
> pode depender só dela — precisa de **sinais de uso** (onde, quando, de qual
> aparelho)."

---

## ETAPA 2 — O login e a emissão do token

**O que mostrar:** o resultado do login bem-sucedido.

**História:** o provedor valida usuário + senha e emite um **token de sessão**
(o "crachá"). É esse token que o app usa para assistir.

**Ponto de defesa:**
> "O token é o que o pirata realmente quer. Se ele conseguir **reutilizar** esse
> crachá em outro lugar, ele entra sem precisar da senha de novo."

---

## ETAPA 3 — A captura do token (o momento do crime)

**O que mostrar:** o alerta **RULE-007 (Token capturado/exfiltrado)** + o token
aparecendo no **Vault de Tokens** com status 🎯 CAPTURADO.

**História:** é aqui que o sistema defensivo "age como o pirata" para provar o
ponto: no instante do login, ele lê o token de sessão e guarda. Isso demonstra
que **o token existe, é legível e pode ser clonado**.

**Ponto de defesa:**
> "Se a engenharia não amarra o token a um aparelho específico e não o expira
> rápido, ele vira chave-mestra. O Vault é a prova visual de que o token foi
> capturado — em produção, essa captura dispararia o bloqueio automático."

---

## ETAPA 4 — A reutilização do token (o crachá clonado)

**O que mostrar:** alerta **RULE-001** — mesmo token em múltiplos IPs.

**História:** o pirata pega o token roubado e apresenta ele de vários lugares
(ou revende pra mil pessoas usarem o mesmo crachá).

**Ponto de defesa:**
> "O provedor legítimo detecta o **mesmo token vindo de IPs diferentes** em
> janelas de tempo impossíveis e revoga na hora. Essa é a trava nº 1: **detecção
> de crachá clonado**."

---

## ETAPA 5 — A anomalia geográfica

**O que mostrar:** alerta **RULE-002** (geo impossível).

**História:** o mesmo token aparece em São Paulo e, 5 minutos depois, em outro
país. Física não permite — logo, é clonagem ou VPN.

**Ponto de defesa:**
> "Correlacionar **tempo + geolocalização** flagra o compartilhamento. É uma das
> travas mais baratas e mais eficazes."

---

## ETAPA 6 — O limite de telas

**O que mostrar:** alerta **RULE-005** (limite de telas excedido).

**História:** a conta `demo.telas` já está no limite (2/2). Quando uma 3ª tela
tenta entrar, o sistema detecta e pode derrubar a mais antiga (exatamente o que
você viu no servidor real do cliente).

**Ponto de defesa:**
> "Limite de telas por conta, com política de prioridade (derrubar a sessão mais
> antiga ou a de geolocalização suspeita)."

---

## ETAPA 7 — A redistribuição (o "mecânico" do pirata)

**O que mostrar:** alertas de **user-agent de ferramenta** (ffmpeg/curl/python)
— RULE-004/006.

**História:** o pirata não assiste como uma pessoa. Ele usa **scripts** (ffmpeg,
curl, python) para capturar e reempacotar o sinal em escala. O user-agent dele
entrega o crime.

**Ponto de defesa:**
> "Detectar **comportamento de máquina** (user-agent, padrão de requisições,
> ausência de interação humana) e cortar o fluxo em milissegundos."

---

## ETAPA 8 — Canais & DRM (a chave mal guardada)

**O que mostrar:** a aba **"Canais & DRM"** — a coluna `KID:KEY` ao lado de
`Widevine L3`.

**História:** o conteúdo chega "embrulhado" (criptografado) e a chave (`KEY`)
destrava. No **Widevine L3**, essa chave fica **na memória do software** — é de
lá que o pirata a extrai.

**Frase de ouro:**
> "O cofre é blindado, mas a chave ficou **em cima da mesa** (na memória). O
> pirata não arromba o cofre — ele **pega a chave da mesa**. As travas são:
> **(1)** subir de L3 para **L1** (chave no chip seguro), **(2)** amarrar a licença
> a um **certificado do aparelho**, **(3)** **rotacionar a chave** a cada poucos
> minutos, e **(4)** **marca d'água forense** para descobrir quem vazou."

---

## ETAPA 9 — O Mapa de Travas (a entrega de valor)

**O que mostrar:** a aba **"Mapa de Travas"**.

**História:** fecha a demonstração mostrando, para cada módulo do atacante, a
contramedida defensiva correspondente. É o resumo executivo que o cliente leva.

**Fechamento:**
> "O pirata é automatizado e industrial. A defesa também precisa ser. Esse painel
> é a planta da fábrica de detecção: cada alerta é uma regra que, em produção,
> dispara revogação de token, bloqueio de sessão e resposta a incidente em tempo
> real."

---

## Checklist de preparação (antes da reunião)

- [ ] Servidor de teste online (VPS com IP público)
- [ ] Painel acessível por HTTPS (domínio ou IP)
- [ ] Contas demo funcionando (login, expirada, bloqueada, telas, geo)
- [ ] Vault de Tokens populado (mostrar um token "capturado")
- [ ] Alertas pré-gerados (RULE-001 a RULE-007)
- [ ] Catálogo de canais sintéticos carregado
- [ ] Este roteiro impresso/aberto como "teleprompter"

---

## Observação de conformidade (leia em toda reunião)

> "Tudo o que será demonstrado usa **dados sintéticos**. Nenhuma chave DRM real
> foi extraída, nenhum token real foi capturado e nenhum conteúdo protegido foi
> retransmitido. O sistema simula o atacante **para provar onde as travas
> defensivas entram** — não para distribuir conteúdo."
