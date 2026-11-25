# ESTADO — AntiPiracy Defense Lab

## Visão geral
- Sistema DEFENSIVO de demonstração (dados 100% sintéticos).
- NÃO extrai DRM real, NÃO captura token real, NÃO retransmite conteúdo protegido.
- Painel = "ferramenta do pirata" (abre ZERADO, sem apontamento; operador digita servidor+usuário+senha).
- Core (DEFENSE-CORE) = "provedor fake" (CHEIO: 13 provedores + 6 contas demo + 8 streams).

## Arquitetura
- `core_server.py` → servidor fake (provedor). Container 8080.
- `app.py` → painel. Porta 5050 local. `CORE_URL` = env vazio (CONEXÃO ABERTA).
- Banco = JSON (`data/core_state.json`, `data/panel_state.json`, `streams/manifest.json`).

## FILTRO POR PROVEDOR CONECTADO (correção 2026-11-25)
- Após login, `_state["connected_provider"]` filtra dashboard, contas, canais, capturas, streams, tokens.
- `/api/dashboard`: providers/accounts/token_health/channels = só do provedor conectado.
- `/api/auth/accounts` (GET): só contas do provedor conectado.
- `/api/channels`, `/api/captures`, `/api/streams`: filtrados pelo provedor conectado.
- Botão "Copiar link M3U" (Canais & DRM) copia `_lastPlaylist` (link real do core, ex.: `http://173.249.14.170:8080/get.php?...`), não o `localhost:5050`.

## Servidor-mãe (VPS EasyPanel)
- IP: 173.249.14.170, porta 8080 (servidor_tv_sky).
- Repo GitHub: willianLealdev/anti-piracy-lab (branch main). Dockerfile/docker-compose na RAIZ.
- Build EasyPanel: "/", arquivo docker-compose.yml. Core na 8080.

## Como subir local (WINDOWS)
- Sempre: `$env:PORT='5050'` (evitar conflito com PORT=3000 do Windows).
- Painel zerado: `$env:CORE_URL=''` e rodar `python app.py`.
- Core local (teste sem VPS): `$env:PORT='8484'; python core_server.py`.

## LIÇÃO (não esquecer)
- Ao reiniciar painel, matar órfãos: `Get-NetTCPConnection -LocalPort 5050 -State Listen`.
- Já houve processo órfão servindo dados fake em memória.

## Contas demo (no CORE da VPS) — senha EXCLUSIVA por provedor
- demo.valido / Sky2026@Ok → Sky+ (DirectvGO), 3 telas, OK
- demo.senha / Globo2026@Ok → GloboPlay Completo, 2 telas (testar senha errada)
- demo.expirado / Prime2026@Exp → Prime Video, expirada
- demo.bloqueado / HBO2026@Blk → HBO Max, bloqueada
- demo.telas / Claro2026@Dev → Claro TV+, limite 2/2
- demo.geo / Disney2026@Geo → Disney+, geo anomalia

## Endereços
- Painel local: http://127.0.0.1:5050 (zerado)
- Servidor-mãe: http://173.249.14.170:8080

## Limpeza de capturas (2026-11-25)
- Endpoint CLEAR no core: POST /api/captures/clear (zera data/captures.json na VPS).
- Proxy no painel: POST /api/captures/clear + botao 'Limpar capturas do servidor' no Vault de Capturas.
- Para zerar capturas antigas da VPS: redeployar o core (git push ja feito) e clicar no botao.
