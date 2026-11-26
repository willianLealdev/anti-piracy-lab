# ESTADO — AntiPiracy Defense Lab

## ÚLTIMA ATUALIZAÇÃO (25/11/2026)
- Adaptador Xtream Codes testado contra painel REAL do cliente (fontez22.ddns.net, autorizado): 39 categorias + 1.617 canais ao vivo + 19.926 filmes + 10.380 séries.
- Corrigido: categorias vinham como ID numérico -> agora resolvidas por NOME (ex.: "⚽ REDE SPORTV").
- Corrigido: qualidade extraída do nome do canal (SD/HD/FHD/4K/HEVC).
- Corrigido: login Xtream otimizado (~2s; não conta mais VOD/séries na autenticação).
- Corrigido: botão "Capturar" funciona no Xtream (link direto /live/user/pass/id.ts + salva no Vault).
- Corrigido: "Baixar/Copiar link M3U" por canal gera M3U de UM canal só; botão "▶ Player" por canal.
- Arquitetura real do painel do cliente: fontez22.ddns.net (77.42.119.223) -> stream via 46.4.103.55 com token; get.php entrega links via goserv.online.

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

## Adaptador Xtream Codes (Plano B) — 2026-11-25
- `xtream_adapter.py`: cliente do protocolo /player_api.php (XUI.one, Xtream UI).
- O painel auto-detecta: tenta DEFENSE-CORE primeiro; se 404/HTML, tenta Xtream.
- Conecta SOMENTE em painéis IPTV autorizados (pentest com permissão).
- NÃO conecta em Sky/GloboPlay/Pluto (esses são apps próprios com DRM, não têm player_api.php).
- Fluxo: login -> /api/auth/login detecta Xtream -> /api/channels lista canais reais -> /api/channels/m3u redireciona pro get.php.
- Heurística de DRM: marcado "Indeterminado" (painel Xtream não expõe DRM); NÃO inventa KID:KEY.

## Limpeza de capturas (2026-11-25)
- Endpoint CLEAR no core: POST /api/captures/clear (zera data/captures.json na VPS).
- Proxy no painel: POST /api/captures/clear + botao 'Limpar capturas do servidor' no Vault de Capturas.
- Para zerar capturas antigas da VPS: redeployar o core (git push ja feito) e clicar no botao.

## Protocolo + secao educacional (2026-11-25)
- Backend auth_login agora retorna campo `protocol` = "DEFENSE-CORE (provedor simulado)" ou "Xtream Codes (painel IPTV)".
- Frontend: badge "🔌 Protocolo" no resultado do login (var --blue).
- Nova secao no menu lateral: "Educacional > 🧠 Como os piratas conectam" (sec-como, id sec-como).
  Explica conceitualmente os 3 caminhos: painel IPTV (Xtream), app com DRM (Widevine L3), FAST (sem DRM) + onde colocar a trava.
  NADA ofensivo executado (sem extracao real de DRM/token).

## Fix deploy: hairpin NAT Docker (2026-11-25)
- Painel dentro do container nao alcanca o proprio IP publico da VPS.
- Solucao: usar `http://core:8080` (rede interna) OU extra_hosts host-gateway no compose (git push feito).
- Compose na RAIZ do repo: core (8080) + painel (5050). Dominio EasyPanel deve apontar p/ servico `painel` porta 5050.


## Estado atual
- Login Xtream Codes agora retorna campos reais (canais/filmes/s?ries, playlist get.php, telas ativas/m?x, expira??o) e o painel recarrega canais automaticamente ap?s conectar. Auto-Flow usa dados reais do painel Xtream (n?o mais n?meros sint?ticos). Commit e9da3f6.

## Pluto TV (API oficial) - 2026-11-25
- Novo provedor: pluto_adapter.py usa GET https://api.pluto.tv/v2/channels (FAST, gratuito, sem DRM).
- Login: digitar https://api.pluto.tv no campo Servidor (sem usuario/senha). Retorna 467 canais reais com link HLS publico.
- Canais/captura/M3U integrados (pluto_session). Commit 312fed6.
