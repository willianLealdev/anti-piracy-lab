# ESTADO DO PROJETO (anti-piracy-lab)

## O que é
AntiPiracy Defense Lab: painel dourado (app.py, porta 5050) + DEFENSE-CORE simulado (core_server.py, porta 8080).
Plataforma DEFENSIVA de demonstracao. Tudo sintetico/simulado no core. NAO extrai DRM real.

## Conexoes suportadas (login aberto)
- **Pluto TV (API oficial)** - FAST real: digitar `https://api.pluto.tv` no campo Servidor, sem usuario/senha. (pluto_adapter.py)
- **Soul TV Brasil (FAST)** - FAST real: digitar `https://soultv.com.br` no campo Servidor, sem usuario/senha. 76 canais. (soultv_adapter.py)
- **Xtream Codes (real)**: digitar IP/dominio do painel do cliente + usuario/senha. (xtream_adapter.py)
- **DEFENSE-CORE (simulado)**: digitar URL da VPS + usuario/senha (contas demo no core).

## Banco do painel
- Provedores ficam no SQLite local `data/panel.db` (panel_db.py). NAO no core.
- 15 provedores: 2 reais (Pluto, Soul TV) + 1 Xtream + 12 simulados (core).

## Deploy (VPS EasyPanel)
- Git: https://github.com/willianLealdev/anti-piracy-lab (branch main)
- docker-compose.yml: core (8080) + painel (5050). Projeto EasyPanel: servidor_tv_sky
- IP VPS: 173.249.14.170 | dominio: servidor-tv-sky-servidor-tv-sky.sbporu.easypanel.host
- Painel online: http://173.249.14.170:5050 | core: http://173.249.14.170:8080

## Contas demo (no core, para login simulado)
- demo.valido / Sky2026@Ok (Sky+)
- demo.senha / Globo2026@Ok (GloboPlay)
- demo.expirado / Prime2026@Exp (Prime Video)
- demo.bloqueado / HBO2026@Blk (HBO Max)
- demo.telas / Claro2026@Dev (Claro TV+)
- demo.geo / Disney2026@Geo (Disney+)

## Cliente (painel real p/ teste)
- fontez22.ddns.net | nicollyavelar8a2 / 39227922 (Xtream, max_connections 1)

## Player / Streams (CORRIGIDO)
- Player da tela usa hls.js (CDN jsdelivr) para reproduzir HLS .m3u8 no Chrome/Edge.
- Link Pluto corrigido: pluto_adapter.py `_fix_stream_url` preenche parametros (deviceId, BR, lat/lon, clientTime) — sem isso a Pluto devolve 400.
- Pluto TV retorna 467 canais reais (FAST, sem DRM).
- Endpoints /api/auth/accounts e /api/live_tokens retornam 200 vazio quando core offline (sem 503).

## Comandos locais
- Subir painel: `cd anti-piracy-lab; python app.py` (porta 5050)
- Subir core local: `python core_server.py` (porta 8080)

## Limites eticos
- NAO construir extracao Widevine L3 real, captura de tokens reais, gerador CFG funcional, retransmissao de conteudo protegido.
- Testes so em servidores autorizados.

## Ultimas correcoes (27/11)
- Login PERSISTE no banco (panel.db > tabela session): sobrevive a refresh e restart. Endpoint GET /api/session + frontend restoreSession().
- Player HLS corrigido: proxy agora reescreve URI de EXT-X-KEY (AES-128) e EXT-X-MEDIA (legendas) -> canais criptografados da Pluto reproduzem. (era o bug do 're' nao importado = 500).
- Qualidade mostra HD/FHD (nao mais 'HLS'); deteccao real de resolucao no master.m3u8.
- Categorias Pluto corretas (nao numeradas).
- Git: commits 647ba43 e 230d5d2 no main.
