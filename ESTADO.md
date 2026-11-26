# ESTADO DO PROJETO (anti-piracy-lab)

## O que é
AntiPiracy Defense Lab: painel dourado (app.py, porta 5050) + DEFENSE-CORE simulado (core_server.py, porta 8080/8484).
Plataforma DEFENSIVA de demonstração. Tudo sintético/simulado. NÃO extrai DRM real.

## Conexões suportadas (login aberto)
- **Pluto TV (API oficial)**: digitar `https://api.pluto.tv` no campo Servidor, sem usuário/senha. (pluto_adapter.py)
- **Xtream Codes (real)**: digitar IP/domínio do painel do cliente + usuário/senha. (xtream_adapter.py)
- **DEFENSE-CORE (simulado)**: digitar URL da VPS + usuário/senha (contas demo no core).

## Banco do painel
- Provedores ficam no SQLite local `data/panel.db` (panel_db.py). NÃO no core.
- 19 provedores semeados: Pluto real + Xtream genérico + DEFENSE-CORE + 13 simulados + 4 FAST simulados (Samsung/Roku/Plex/Red Bull).

## Deploy (VPS EasyPanel)
- Git: https://github.com/willianLealdev/anti-piracy-lab (branch main)
- docker-compose.yml: core (8080) + painel (5050). Projeto EasyPanel: servidor_tv_sky
- IP VPS: 173.249.14.170 · domínio: servidor-tv-sky-servidor-tv-sky.sbporu.easypanel.host
- Painel online: http://173.249.14.170:5050 · core: http://173.249.14.170:8080

## Contas demo (no core, para login simulado)
- demo.valido / Sky2026@Ok (Sky+)
- demo.senha / Globo2026@Ok (GloboPlay)
- demo.expirado / Prime2026@Exp (Prime Video)
- demo.bloqueado / HBO2026@Blk (HBO Max)
- demo.telas / Claro2026@Dev (Claro TV+)
- demo.geo / Disney2026@Geo (Disney+)

## Cliente (painel real p/ teste)
- fontez22.ddns.net · nicollyavelar8a2 / 39227922 (Xtream, max_connections 1)

## Comandos locais
- Subir painel: `cd anti-piracy-lab; python app.py` (porta 5050)
- Subir core local: `python core_server.py` (porta 8484/8080)

## Limites éticos
- Não construir extração Widevine L3 real, captura de tokens reais, gerador CFG funcional, retransmissão de conteúdo protegido.
- Testes só em servidores autorizados.
