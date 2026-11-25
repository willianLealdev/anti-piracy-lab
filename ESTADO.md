# AntiPiracy Defense Lab â€” Estado do Projeto

## VisÃ£o
LaboratÃ³rio DEFENSIVO 100% sintÃ©tico. Painel (app.py, porta 5050) + servidor fake DEFENSE-CORE (core_server.py, porta 8080). Nada de extraÃ§Ã£o real, chave real ou token real.

## Regra de ouro (limpo/zerado)
- Sistema inicia ZERADO. Sem seeds, sem fallbacks, sem simulador em background.
- Dados sÃ³ surgem de eventos reais (cadastro de provedor/conta no painel, login, conexÃ£o ao servidor de teste).
- `streams/manifest.json` = `[]` (vazio). Streams fake sÃ³ sÃ£o gerados rodando `python gerar_streams.py` explicitamente.

## Arquitetura
- Banco: arquivos JSON (data/core_state.json, data/panel_state.json, data/captures.json). NÃƒO usa SQLite.
- Core local: http://127.0.0.1:8080 (variÃ¡veis HOST, PORT, PUBLIC_URL)
- Painel local: http://localhost:5050 (variÃ¡veis CORE_URL, HOST, PORT)
- Multi-servidor: core_server.py aceita PROVIDER_FILTER (ex.: "pluto,soultv").
- RotaÃ§Ã£o: POST /api/rotate (core) gira token + KID:KEY juntos (revision).

## Deploy VPS
- Repo GitHub: willianLealdev/anti-piracy-lab (branch main)
- VPS do cliente: EasyPanel 173.249.14.170, projeto "servidor_tv_sky"
- Dockerfile + docker-compose.yml na raiz do repo. Build no EasyPanel: caminho "/", arquivo docker-compose.yml
- Core na 8080, painel na 5050. DomÃ­nio EasyPanel aponta pro serviÃ§o "core".

## Comandos
- Subir core local: $env:PORT='8080'; $env:HOST='127.0.0.1'; python -B core_server.py
- Subir painel local: $env:PORT='5050'; $env:HOST='0.0.0.0'; $env:CORE_URL='http://127.0.0.1:8080'; python -B app.py
- (Windows tem PORT=3000 global; SEMPRE sobrescrever com $env:PORT=...)

## Estado atual (2026-11-25)
- Tudo zerado: provedores 0, contas 0, streams 0, tokens 0, captures 0, VPS 0, YouTube 0, detecÃ§Ãµes 0.
- Painel e core rodando zerados.
- Falta: reimplantar a VPS com o cÃ³digo novo para zerar o core online (ainda tem dados antigos).

## MÃ³dulos
Dashboard, Vault de Tokens, Contas & Login, MINHAS VPS, Canais & DRM, Vault de Capturas, Canais YouTube, Gerador de CFG, Deploy & Logs, Auto-Flow, RotaÃ§Ã£o de Tokens, Streams Simulados, DetecÃ§Ãµes, Mapa de Travas.


## MODELO CORRETO (fixado em 25/11)
- **CORE (core_server.py, porta 8080) = o PROVEDOR simulado** -> deve ficar CHEIO (provedores/contas/canais/KID:KEY/streams). Roda na VPS.
- **PAINEL (app.py, porta 5050) = a ferramenta do pirata** -> deve nascer ZERADO, sem apontar pra servidor nenhum.
- Conexao ABERTA: o operador DIGITA o endereco do servidor + usuario + senha no login; so entao o painel conecta (rota /api/auth/login aceita campo "server"; ao dar ok, define CORE_URL global). Rota /api/disconnect volta ao zero.
- CORE_URL default = vazio (sem fallback localhost). Frontend: CORE = localStorage.coreUrl || "".
- Banco: JSON em data/core_state.json (core) + streams/manifest.json (core). Painel NAO persiste vault/alertas (memoria).

