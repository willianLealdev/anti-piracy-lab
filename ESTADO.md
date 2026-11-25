# AntiPiracy Defense Lab — Estado do Projeto

## Visão
Laboratório DEFENSIVO 100% sintético. Painel (app.py, porta 5050) + servidor fake DEFENSE-CORE (core_server.py, porta 8484). Nada de extração real, chave real ou token real.

## Regra de ouro (limpo/zerado)
- Sistema inicia ZERADO. Sem seeds, sem fallbacks, sem simulador em background.
- Dados só surgem de eventos reais (cadastro de provedor/conta no painel, login, conexão ao servidor de teste).
- `streams/manifest.json` = `[]` (vazio). Streams fake só são gerados rodando `python gerar_streams.py` explicitamente.

## Arquitetura
- Banco: arquivos JSON (data/core_state.json, data/panel_state.json, data/captures.json). NÃO usa SQLite.
- Core local: http://127.0.0.1:8484 (variáveis HOST, PORT, PUBLIC_URL)
- Painel local: http://localhost:5050 (variáveis CORE_URL, HOST, PORT)
- Multi-servidor: core_server.py aceita PROVIDER_FILTER (ex.: "pluto,soultv").
- Rotação: POST /api/rotate (core) gira token + KID:KEY juntos (revision).

## Deploy VPS
- Repo GitHub: willianLealdev/anti-piracy-lab (branch main)
- VPS do cliente: EasyPanel 173.249.14.170, projeto "servidor_tv_sky"
- Dockerfile + docker-compose.yml na raiz do repo. Build no EasyPanel: caminho "/", arquivo docker-compose.yml
- Core na 8484, painel na 5050. Domínio EasyPanel aponta pro serviço "core".

## Comandos
- Subir core local: $env:PORT='8484'; $env:HOST='127.0.0.1'; python -B core_server.py
- Subir painel local: $env:PORT='5050'; $env:HOST='0.0.0.0'; $env:CORE_URL='http://127.0.0.1:8484'; python -B app.py
- (Windows tem PORT=3000 global; SEMPRE sobrescrever com $env:PORT=...)

## Estado atual (2026-11-25)
- Tudo zerado: provedores 0, contas 0, streams 0, tokens 0, captures 0, VPS 0, YouTube 0, detecções 0.
- Painel e core rodando zerados.
- Falta: reimplantar a VPS com o código novo para zerar o core online (ainda tem dados antigos).

## Módulos
Dashboard, Vault de Tokens, Contas & Login, MINHAS VPS, Canais & DRM, Vault de Capturas, Canais YouTube, Gerador de CFG, Deploy & Logs, Auto-Flow, Rotação de Tokens, Streams Simulados, Detecções, Mapa de Travas.
