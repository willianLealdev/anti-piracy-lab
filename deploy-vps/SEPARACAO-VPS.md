# Separação de VPS — 1 provedor simulado por VPS

Para uma simulação **fiel ao mundo real**, cada VPS representa **um único provedor**
(ou um único "tipo": DRM, FAST ou YouTube). O core usa a variável
`PROVIDER_FILTER` para servir **apenas** aquele provedor e **apenas** as contas
dele (sem vazar credenciais de outros provedores).

## Como funciona

```
PROVIDER_FILTER=plutotv  ->  VPS serve SÓ o Pluto TV (FAST)
PROVIDER_FILTER=globoplay -> VPS serve SÓ o GloboPlay (DRM)
```

O filtro é feito em **tempo de inicialização** (lê a variável de ambiente).
O mesmo código (`core_server.py`) serve para qualquer VPS — o que muda é a
variável `PROVIDER_FILTER` + o `PUBLIC_URL` (IP/domínio daquela VPS).

## Tabela dos provedores (ID para usar no filtro)

| Provedor | ID (`PROVIDER_FILTER`) | Tipo | Canais |
|---|---|---|---|
| GloboPlay Completo | `globoplay` | DRM (Widevine L3) | 180 |
| Sky+ (DirectvGO) | `skyplus` | DRM (Widevine L3) | 86 |
| Prime Video (Amazon) | `primevideo` | DRM (Widevine L3) | Ilimitado |
| HBO Max | `hbomax` | DRM (Widevine L3) | 40 |
| Disney+ | `disneyplus` | DRM (Widevine L3) | 35 |
| Paramount+ | `paramountplus` | DRM (Widevine L3) | 30 |
| Claro TV+ | `clarotv` | DRM (Widevine L3) | 120 |
| Pluto TV Brasil | `plutotv` | FAST (Sem DRM) | 187 |
| Astra TV (Cesbo) | `astra` | FAST (Sem DRM) | 90 |
| Soul TV Brasil | `soultv` | FAST (Sem DRM) | 77 |
| BandPlay Oficial | `bandplay` | FAST (Sem DRM) | 29 |
| Record+ / PlayPlus | `recordplus` | FAST (Sem DRM) | 10 |
| YouTube Live | `youtube` | FAST (HLS perpétuo) | 15 |

> Pode agrupar mais de um no mesmo VPS separando por vírgula:
> `PROVIDER_FILTER=plutotv,soultv,recordplus,bandplay,astra`

## Topologia recomendada (5 VPS — como o cliente pediu)

| VPS | Representa | `PROVIDER_FILTER` | Conta de teste |
|---|---|---|---|
| VPS 1 | GloboPlay (DRM) | `globoplay` | `demo.valido` / `Sky2026@Ok` |
| VPS 2 | Pluto TV (FAST) | `plutotv` | `demo.pluto` / `Pluto2026@Ok` |
| VPS 3 | Prime Video (DRM) | `primevideo` | `demo.telas` / `Sky2026@Ok` |
| VPS 4 | Record+ (FAST) | `recordplus` | `demo.record` / `Record2026@Ok` |
| VPS 5 | Sky+ (DRM) | `skyplus` | `demo.bloqueado` / `Sky2026@Ok` |

## Passo a passo (EasyPanel)

1. Crie um **novo projeto** no EasyPanel (ex.: `vps_globoplay`).
2. Use o template `docker-compose.provedor.yml` (copie para a raiz como `docker-compose.yml`).
3. Troque **2 valores**:
   - `PROVIDER_FILTER` → o ID da tabela acima.
   - `PUBLIC_URL` → `http://IP-DA-VPS:8080`.
4. Faça o **Deploy**.
5. No painel local (ferramenta), digite no campo **Servidor**: `http://IP-DA-VPS:8080`.

## Importante

- **Nunca** exponha o painel (a "ferramenta do pirata") na internet.
  Só o **core** (o "provedor") precisa estar acessível. O painel roda local.
- Cada VPS tem seu próprio volume (`core_data`), então os dados não se misturam.
- Para testar **todos juntos** (modo servidor único), basta **não** definir
  `PROVIDER_FILTER` (vazio) — é o que está no `docker-compose.yml` da raiz.
