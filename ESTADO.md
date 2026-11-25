# AntiPiracy Defense Lab — Estado do Projeto

> Fonte de verdade. Consulte SEMPRE este arquivo antes de responder/alterar.
> Atualize ao final de cada mudança.

## Visão geral
Sistema de demonstração DEFENSIVA (laboratório) que simula o fluxo de um "EXTRATOR-V10" pirata,
mas 100% sintético. Objetivo: mostrar ao cliente (operadoras/Google) ONDE COLOCAR AS TRAVAS defensivas.

## Ética / Limites (NÃO negociável)
- NUNCA construir quebra real de DRM (Widevine), captura de token real, gerador de CFG funcional p/ pirataria.
- TUDO é simulado: KID:KEY hex decorativas, tokens fabricados, canais fake (HLS via ffmpeg).
- Acesso só a servidores próprios/autorizados do cliente.

## Estrutura de pastas
- `anti-piracy-lab/` → projeto do laboratório
  - `app.py` → PAINEL (Flask) porta 5050
  - `core_server.py` → DEFENSE-CORE (servidor fake dos provedores) porta 8484
  - `templates/` → HTML do painel
  - `data/` → bancos JSON (accounts, captures, detections, servers, tokens...)
  - `streams/` → streams HLS reais gerados por ffmpeg (reproduzem no VLC)
  - `deploy-vps/` → Docker, nginx, systemd, README p/ VPS
  - `ESTADO.md` → este arquivo
- `meu-site/` → projeto ANTERIOR (StreamGuard: scanner de portas IPTV). Separado.

## Como subir local (Windows)
- Painel: `$env:PORT='5050'; python app.py` (na pasta anti-piracy-lab)
- Core: `$env:PORT='8484'; python core_server.py`
- CUIDADO: Windows tem env PORT=3000 fixa; sempre definir PORT antes.
- Multi-servidor: `$env:PROVIDER_FILTER="pluto,soultv,..."` no core.

## Arquitetura atual
- PAINEL (5050) → faz proxy p/ DEFENSE-CORE (8484) via `CORE_URL` (env).
- 13 provedores simulados (100% fake): GloboPlay 180, Astra 90, Sky+ 86, Prime 45,
  Pluto 187, Soul TV 77, YouTube 15, Record+ 10, BandPlay 29, HBO Max 40, Disney+ 35,
  Paramount+ 30, Claro TV+ 120 = 944 canais.
- Tipos: `drm` (Widevine L3 sim) e `fast` (sem DRM). Campo no manifest = `type`.
- Multi-servidor: painel roteia por provedor (campo "Servidor (domínio/IP:porta)") via `core_for_provider`.
- `PROVIDER_FILTER` no core = quais provedores aquela instância serve.
- `/api/servers` = topologia multi-servidor.
- CONEXÃO ABERTA: na aba Contas & Login há campo "Servidor (endereço direto)".
  Se preenchido, o login conecta SÓ naquele endereço (sem fallback) — permite apontar
  para qualquer DEFENSE-CORE clonado (VPS em outro país). Se vazio, usa o servidor do
  provedor selecionado. Testado: 8484 ok, 8485 ok, IP inválido → 503 core_offline.
- `PUBLIC_URL` (env no core) = endereço público da VPS p/ gerar links (playlist/get.php)
  apontando para o lugar certo. Sem ela, usa subdomínio fake local.

## Módulos funcionais (todos testados)
- Dashboard Operacional (lê do banco real, tema dark dourado)
- Contas & Login (CRUD provedor+conta, login com respostas: OK/errada/expirada/bloqueada/limite/geo)
- Auto-Flow (7 etapas automáticas)
- Vault de Tokens (+ "Trocar conta")
- Canais & DRM (Baixar M3U, Copiar link, captura KID:KEY)
- Vault de Capturas (DRM KID:KEY + FAST link M3U)
- Streams Simulados (VLC, download, player) — streams REAIS HLS em `streams/`
- Minhas VPS (CRUD, Deploy, Baixar lista XUI)
- Canais YouTube (Testar, XUI Link, CRUD, lives)
- Gerador de CFG (arquivos simulados + download)
- Deploy & Logs
- Rotação de Tokens (token + KID:KEY mudam juntos, RULE-008)
- Detecções (motor defensivo RULE-001..008 + IoCs)
- Mapa de Travas (o que atacante vê / IoC / onde travar)

## Contas de teste (fabricadas)
demo.valido, demo.senha, demo.expirado, demo.bloqueado, demo.telas, demo.geo.
Login OK usa: demo.valido / senha qualquer (ex: Sky2026@Ok).

## Regras de detecção
RULE-001 conta bloqueada · RULE-002 geo · RULE-003 captura FAST · RULE-005 limite telas ·
RULE-006 brute force · RULE-007 token/DRM capturado · RULE-008 rotação.

## Streams reais (reproduzíveis)
- Formato HLS: `/streams/{slug}_sim/index.m3u8` (H.264 1920x1080 + AAC, ~45s loop).
- Botões VLC baixam `.m3u` apontando p/ stream REAL (corrigido).
- NÃO usar `/stream/Nome.ts` (sintético, não toca).

## Pontos de atenção / bugs conhecidos corrigidos
- PowerShell não aceita heredoc → usar script .py temporário ou ler_arquivo.
- Terminal distorce acentos → ler com Python/ler_arquivo.
- PORT=3000 do Windows conflita → sempre definir PORT.
- vlc:// não abre no Windows → botão baixa .m3u.

## Deploy (ATUAL - EasyPanel)
- Dockerfile e docker-compose.yml ficam na RAIZ do repo (nao mais em deploy-vps/).
- Repo GitHub publico: willianLealdev/anti-piracy-lab (branch main).
- VPS do cliente: 173.249.14.170 (EasyPanel, projeto "servidor_tv_sky").
- Caminho de build no EasyPanel: / | arquivo: docker-compose.yml.
- Core porta 8484, painel porta 5050. PUBLIC_URL aponta p/ 173.249.14.170.
- Streams sinteticos NAO vao pro Git: gerados no servidor via ffmpeg
  (gerar_streams.py agora cross-platform; duracao 12s).
- Volumes: core_data, core_streams, panel_data (persistencia).

## Próximos passos (aguardando)
- Cliente vai enviar credenciais da VPS/EasyPanel.
- Subir: deploy-vps/README.md (Docker/nginx/systemd).
  - Cada VPS/clone: `PUBLIC_URL=http://IP_DA_VPS:8484` + `PROVIDER_FILTER=...` no core.
  - Painel: `CORE_URL=http://IP_DA_VPS_MASTER:8484`.
- Documentar tudo p/ entregar ao cliente.
- Shodan: só existe SHODAN_API_KEY nos segredos (não usado ainda).
