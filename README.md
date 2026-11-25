# AntiPiracy Defense Lab

Plataforma **defensiva** de demonstração para empresas de streaming e operadoras.

## O que é

Simula um sistema de "extrator" (com dados **100% sintéticos** e fabricados)
e um **motor de detecção** que identifica, em tempo real, os abusos de um
sistema de pirataria de IPTV:

- Compartilhamento de conta/token (mesma credencial em múltiplos IPs)
- Anomalia de sessão (geolocalização impossível)
- Redistribuição (user-agent de ferramenta: ffmpeg/curl/python)
- Credencial exposta em URL
- Múltiplas sessões simultâneas acima do limite
- Captura/exfiltração de token de sessão
- Rotação de token/link detectada e re-sincronizada

Tudo é fabricado (nomes, IPs, tokens, canais, chaves KID:KEY). **Nenhuma chave
DRM real é extraída, nenhum token real é capturado e nenhum conteúdo protegido
é retransmitido.**

## Arquitetura (2 processos)

| Processo | Porta | Papel |
|---|---|---|
| `core_server.py` | 8484 | DEFENSE-CORE: o "servidor fictício" (provedores, streams sintéticos, licenças DRM, contas de teste, rotação de tokens) |
| `app.py` | 5050 | Painel web (dashboard, detecção, auto-flow) — acessível na rede/VPS |

## Como rodar (local)

```powershell
cd C:\Users\Owner\Desktop\PAINEL\projetos\anti-piracy-lab
python -m pip install -r requirements.txt

# Terminal 1 — servidor fictício
$env:PORT='8484'; python core_server.py

# Terminal 2 — painel
$env:PORT='5050'; python app.py
```

Abra: http://localhost:5050

> **Importante no Windows:** se houver a variável de ambiente `PORT` definida
> no sistema, force a porta correta com `$env:PORT='...'` antes de rodar.

## Módulos do painel

- **Dashboard** — sessões, abusos, alertas, IoFs, provedores e saúde dos tokens
- **Conexão & Login** — simulação completa de autenticação (contas demo com todos os cenários: OK, senha errada, expirada, bloqueada, limite de telas, geo anomalia)
- **Auto-Flow (piloto automático)** — após inserir usuário+senha, o sistema executa tudo sozinho: conecta → puxa playlist M3U → cataloga canais → detecta DRM KID:KEY → gera CFG → deploy na VPS (7 etapas com log ao vivo)
- **Rotação de Tokens** — simula o provedor "girando" tokens/links; o painel detecta sozinho e re-sincroniza (alerta RULE-008)
- **Vault de Tokens** — saúde/validade das credenciais simuladas + tokens capturados na demo
- **Canais & DRM** — catálogo sintético com CID, KID:KEY, Widevine L3, qualidade e áudio
- **Streams Simulados** — canais 100% sintéticos (padrões ffmpeg) reproduzíveis no VLC para provar o fluxo completo
- **Minhas VPS / Canais YouTube / Gerador de CFG / Deploy & Logs** — módulos do "extrator" (tudo fabricado)
- **Detecções** — alertas em tempo real + regras defensivas (RULE-001 a RULE-008)
- **Mapa de Travas** — para cada módulo do atacante, onde colocar a defesa

## Contas de teste (simuladas)

| Usuário | Senha | Provedor | Cenário |
|---|---|---|---|
| demo.valido | Sky2026@Ok | Sky+ (DirectvGO) | Login OK + captura de token |
| demo.senha | Globo2026@Ok | GloboPlay Completo | Digite senha errada |
| demo.expirado | Prime2026@Exp | Prime Video | Assinatura vencida |
| demo.bloqueado | HBO2026@Blk | HBO Max | Conta bloqueada |
| demo.telas | Claro2026@Dev | Claro TV+ | Limite de 2 telas atingido |
| demo.geo | Disney2026@Geo | Disney+ | Anomalia geográfica |

## Deploy na VPS (produção)

Tudo pronto em `deploy-vps/`:

- `deploy.sh` — instala e sobe com systemd + gunicorn + nginx
- `Dockerfile` + `docker-compose.yml` — alternativa em contêiner
- `nginx.conf` — proxy reverso
- `requirements-vps.txt` — dependências de produção

O painel escuta em `0.0.0.0` por padrão (acessível pela internet).
Para apontar ao DEFENSE-CORE na VPS, defina `CORE_URL`:

```bash
CORE_URL=http://IP_DA_VPS:8484
```

## Objetivo de negócio

Demonstrar para operadoras/provedores a **engenharia de detecção e bloqueio**
de pirataria: fluxo completo do ataque (simulado), indicadores de fraude (IoF),
modelo de ameaças e mapa de contramedidas — tudo legal e vendável, com dados
sintéticos e sem nenhuma extração real.
