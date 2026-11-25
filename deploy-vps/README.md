# AntiPiracy Defense Lab — Guia de Deploy em VPS

Este guia explica como colocar o **servidor simulado** (100% sintético) numa
VPS online, para que a demonstração pareça um "provedor de fato na internet" —
como funciona na prática, igual à arquitetura de um painel de IPTV.

> ⚠️ **Transparência total:** nada aqui é real. Não há extração de DRM, não há
> token real, não há conteúdo protegido. É uma maquete com dados fabricados.

---

## Arquitetura (como fica na VPS)

```
Internet
   │
   ├── http://SEU_DOMINIO (painel)   → app.py       (porta 5050)
   │        └── conversa por HTTP com o CORE
   │
   └── http://core.SEU_DOMINIO (opcional) → core_server.py (porta 8484)
```

- **CORE (8484)** = o "servidor do provedor" simulado (contas, login, tokens, playlists).
- **PAINEL (5050)** = a interface dark mode que o cliente vê e onde o engenheiro dele navega.

Isso replica, com dados falsos, a mesma divisão "painel ↔ servidor de conteúdo"
que existe num sistema de IPTV real.

---

## Topologia multi-servidor (1 VPS por tipo de provedor)

Você pode rodar **várias instâncias** do DEFENSE-CORE, cada uma simulando um
"servidor de provedor" diferente — igual a um pirata faria espalhando os
servidores:

```
VPS 1 (DRM)      PROVIDER_FILTER="skyplus,globoplay,hbomax,disneyplus,paramountplus,clarotv"
VPS 2 (FAST)     PROVIDER_FILTER="pluto,soultv,recordplus,bandplay,astra"
VPS 3 (YouTube)  PROVIDER_FILTER="youtube"
```

Como funciona:
1. Cada VPS roda o mesmo `core_server.py` com `PROVIDER_FILTER` apontando só
   para os provedores daquela instância (a porta padrão é 8484).
2. No painel, você **cadastra/edita cada provedor** informando o campo
   "Servidor (domínio ou IP:porta)" com o endereço da VPS correspondente.
3. O painel então **roteia automaticamente** as operações de cada provedor
   (login, captura de canal, streams) para o servidor certo — e agrega tudo
   numa única tela.

Sem `PROVIDER_FILTER` (vazio), a instância serve **todos** os provedores
(modo servidor único, que é o padrão local).

---

## Opção A — Deploy com Docker (mais simples e recomendado)

```bash
# 1) Suba os arquivos do projeto para a VPS (ex.: via git ou scp)
# 2) Dentro da pasta anti-piracy-lab:
cd anti-piracy-lab
docker compose -f deploy-vps/docker-compose.yml up -d --build

# 3) Conferir
curl http://localhost:5050/api/ping
curl http://localhost:8484/health
```

O painel sobe em `http://IP_DA_VPS:5050` e o core em `http://IP_DA_VPS:8484`.

---

## Opção B — Deploy sem Docker (systemd + gunicorn)

```bash
cd anti-piracy-lab
sudo bash deploy-vps/deploy.sh
```

O script instala tudo (Python, nginx, firewall) e cria 2 serviços:
`defense-core` e `defense-painel`, que reiniciam sozinhos se caírem.

---

## Opção C — Domínio + HTTPS (para ficar mais profissional)

1. Aponte o DNS do seu domínio para o IP da VPS (registro A).
2. Edite `deploy-vps/nginx.conf` trocando `SEU_DOMINIO`.
3. Configure e ative:

```bash
cp deploy-vps/nginx.conf /etc/nginx/sites-available/defense
ln -s /etc/nginx/sites-available/defense /etc/nginx/sites-enabled/defense
nginx -t && systemctl reload nginx

# HTTPS gratuito
apt install -y certbot python3-certbot-nginx
certbot --nginx -d SEU_DOMINIO
```

Pronto: `https://SEU_DOMINIO` abre o painel com cadeado.

---

## O que o cliente poderá fazer online

1. Acessar o painel de qualquer lugar do mundo.
2. Digitar a **URL do servidor** (`core.SEU_DOMINIO` ou `http://IP:8484`).
3. Logar com as contas de teste (sintéticas) e ver:
   - login OK, senha errada, expirada, bloqueada, limite de telas, geo anomalia;
   - geração de token de sessão + **captura simulada** no Vault;
   - alertas de detecção em tempo real (RULE-001 a RULE-007).
4. A equipe de engenharia dele testa **de verdade** contra um "provedor online"
   — sem tocar em nada real.

---

## Variáveis de ambiente

| Variável   | Padrão               | Descrição                         |
|------------|----------------------|-----------------------------------|
| `HOST`     | `127.0.0.1`          | Interface (use `0.0.0.0` na VPS)  |
| `PORT`     | `5050` / `8484`      | Porta do serviço                  |
| `CORE_URL` | `http://127.0.0.1:8484` | Endereço do core que o painel usa |
| `PROVIDER_FILTER` | *(vazio)*    | IDs dos provedores que a instância serve (multi-servidor). Ex.: `skyplus,globoplay` |

---

## Credenciais de demonstração (100% fictícias)

| Usuário        | Senha          | Resultado                       |
|----------------|----------------|---------------------------------|
| `demo.valido`  | `Sky2026@Ok`   | ✅ Login OK + captura de token  |
| `demo.senha`   | `Globo2026@Ok` | ❌ Senha incorreta              |
| `demo.expirado`| `Prime2026@Exp`| ❌ Assinatura expirada          |
| `demo.bloqueado`| `HBO2026@Blk` | ❌ Conta bloqueada              |
| `demo.telas`   | `Claro2026@Dev`| ❌ Limite de telas (2/2)        |
| `demo.geo`     | `Disney2026@Geo`| ⚠️ Login OK + alerta geográfico |
