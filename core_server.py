# -*- coding: utf-8 -*-
"""
DEFENSE-CORE — Servidor FAKE interno (100% SIMULADO)
=====================================================
Este é o "servidor fictício" que o painel AntiPiracy Defense Lab controla.

Ele simula, de ponta a ponta, a infraestrutura de um sistema de extração
(DRM core, streams, licenças DRM, validação de tokens, provedores).

IMPORTANTE:
  - NÃO extrai chaves Widevine reais.
  - NÃO captura tokens reais.
  - NÃO retransmite conteúdo protegido.
  - TUDO aqui é dado fabricado/sintético, gerado localmente, para DEMONSTRAÇÃO
    e para que a equipe de engenharia do cliente entenda ONDE COLOCAR AS TRAVAS.

Porta: 8484 (a mesma "displayed_port" exibida no painel).
"""

import base64
import datetime
import hashlib
import json
import os
import random
import re
import time

from flask import Flask, jsonify, request, Response, send_from_directory, abort

app = Flask(__name__)

SERVICE_NAME = "DEFENSE-CORE"
MODE = "SIMULACAO-100%-SINTETICA"

# ---------------------------------------------------------------------------
# PERSISTÊNCIA (provedores + contas de teste sobrevivem a reinícios)
# ---------------------------------------------------------------------------

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "core_state.json")


def _slugify(name):
    """Transforma um nome em slug de subdomínio (ex.: 'GloboPlay Completo' -> 'globoplay')."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "servidor"


def _server_for(name):
    """Gera o link 'subdomínio' do servidor simulado para um provedor."""
    return f"http://{_slugify(name)}.defense-lab.net:8484"


def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
            # garante campos de servidor/subdomínio nos provedores
            st.setdefault("providers", [])
            st.setdefault("accounts", [])
            for p in st["providers"]:
                p.setdefault("subdomain", _slugify(p.get("name", p.get("id", "servidor"))))
                p.setdefault("server", _server_for(p.get("name", p.get("id", "servidor"))))
            return st
        except Exception:
            pass
    return {"providers": [], "accounts": []}


def _save_state(st):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


_STATE = _load_state()
PROVIDERS = _STATE["providers"]
DEMO_ACCOUNTS = _STATE["accounts"]

# ---------------------------------------------------------------------------
# MULTI-SERVIDOR: permite rodar várias instâncias do DEFENSE-CORE, cada uma
# simulando um "servidor de provedor" específico.
#
#   PROVIDER_FILTER="skyplus,globoplay"  -> serve apenas esses provedores
#   (vazio)                              -> serve todos (modo servidor único)
#
# Exemplo de topologia para o cliente:
#   VPS 1: PROVIDER_FILTER="skyplus,globoplay,hbomax,disneyplus,paramountplus,clarotv"  (DRM)
#   VPS 2: PROVIDER_FILTER="pluto,soultv,recordplus,bandplay,astra"                    (FAST)
#   VPS 3: PROVIDER_FILTER="youtube"                                                    (YouTube)
# ---------------------------------------------------------------------------
_PROVIDER_FILTER = os.environ.get("PROVIDER_FILTER", "").strip()
if _PROVIDER_FILTER:
    _wanted = {p.strip().lower() for p in _PROVIDER_FILTER.split(",") if p.strip()}
    _filtered = [p for p in PROVIDERS if p["id"].lower() in _wanted or p["name"].lower() in _wanted]
    if _filtered:
        PROVIDERS = _filtered
        _wanted_names = {p["name"] for p in PROVIDERS}
        DEMO_ACCOUNTS = [a for a in DEMO_ACCOUNTS if a.get("provider") in _wanted_names]


def _persist():
    _save_state({"providers": PROVIDERS, "accounts": DEMO_ACCOUNTS})


# ---------------------------------------------------------------------------
# Geradores sintéticos
# ---------------------------------------------------------------------------

def _h(v):
    return hashlib.sha256(v.encode()).hexdigest()[:16]


def _fake_ts_packet(pid, payload=None, counter=0):
    """Monta um pacote MPEG-TS de 188 bytes (sincronismo 0x47)."""
    pkt = bytearray(188)
    pkt[0] = 0x47
    pkt[1] = ((pid >> 8) & 0x1F) | 0x40
    pkt[2] = pid & 0xFF
    pkt[3] = 0x10 | (counter & 0x0F)
    if payload:
        data = payload[:180].encode() if isinstance(payload, str) else payload[:180]
        pkt[4:4 + len(data)] = data
    else:
        for i in range(4, 188):
            pkt[i] = (i * 7 + counter * 3) & 0xFF
    return bytes(pkt)


def _fake_stream_bytes(channel_id, n_packets=3):
    out = bytearray()
    out += _fake_ts_packet(0, b"DEFENSE-CORE-PAT-SIMULADO", 0)
    out += _fake_ts_packet(0x1000, b"PMT-SIMULADO-" + channel_id.encode()[:12], 1)
    for i in range(max(1, n_packets - 2)):
        out += _fake_ts_packet(0x100, b"STREAM-FAKE:" + channel_id.encode(), i)
    return bytes(out)


# ---------------------------------------------------------------------------
# Rotas do servidor fake
# ---------------------------------------------------------------------------

@app.route("/")
def root():
    return jsonify({
        "service": SERVICE_NAME,
        "mode": MODE,
        "status": "Ativo",
        "port": 8484,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "aviso": "Servidor FICTICIO. Nenhum dado real. Nenhuma extracao de DRM.",
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "Ativo",
        "service_name": SERVICE_NAME,
        "mode": MODE,
        "ram_disk_status": "OK",
        "displayed_port": 8484,
        "security_level": "Widevine L3 (SIMULADO - chave fabricada)",
        "uptime_sec": int(time.time() - _start),
    })


# ---------------------------------------------------------------------------
# STREAMS 100% SINTÉTICOS (gerados por ffmpeg em streams/)
# ---------------------------------------------------------------------------
STREAMS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streams")


def _load_manifest():
    try:
        with open(os.path.join(STREAMS_DIR, "manifest.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


@app.route("/streams/<path:path>")
def streams_static(path):
    full = os.path.abspath(os.path.join(STREAMS_DIR, path))
    base = os.path.abspath(STREAMS_DIR)
    if not full.startswith(base):
        abort(404)
    if not os.path.exists(full):
        abort(404)
    return send_from_directory(base, path)


@app.route("/api/streams")
def api_streams():
    manifest = _load_manifest()
    host = request.host
    for m in manifest:
        m["full_url"] = f"http://{host}{m['url']}"
    return jsonify({
        "streams": manifest,
        "total": len(manifest),
        "aviso": "Streams 100% sintéticos (padrões de teste ffmpeg). Nenhum conteúdo protegido.",
    })


@app.route("/stream/<channel_id>.ts")
def stream_ts(channel_id):
    return Response(
        _fake_stream_bytes(channel_id, n_packets=8),
        mimetype="video/mp2t",
        headers={
            "X-DEFENSE-CORE": "stream-simulado",
            "Content-Disposition": f'inline; filename="{channel_id}.ts"',
        },
    )


@app.route("/stream/<channel_id>.m3u8")
def stream_hls(channel_id):
    host = request.host
    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        f"#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=1280x720",
        f"http://{host}/stream/{channel_id}_720.ts",
        f"#EXT-X-STREAM-INF:BANDWIDTH=300000,RESOLUTION=640x360",
        f"http://{host}/stream/{channel_id}_360.ts",
    ]
    return Response("\n".join(lines), mimetype="application/vnd.apple.mpegurl")


@app.route("/license")
def license_():
    kid = _h("defense-core-kid")[:16].upper()
    key = base64.b64encode(_h("defense-core-key-fake").encode()).decode()
    return jsonify({
        "license_type": "SIMULADA",
        "kid": f"{kid}:{key}",
        "aviso": "Chave FABRICADA, gerada localmente. Nao abre conteudo protegido.",
        "expiration": (datetime.datetime.utcnow() + datetime.timedelta(hours=18)).isoformat(),
    })


# ---------------------------------------------------------------------------
# VAULT DE CAPTURAS (KID:KEY DRM simulada + links M3U de canais FAST)
# ---------------------------------------------------------------------------
# Persistido em data/captures.json. Tudo fabricado localmente.
CAPTURES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "captures.json")


def _load_captures():
    if os.path.exists(CAPTURES_FILE):
        try:
            with open(CAPTURES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_captures(items):
    os.makedirs(os.path.dirname(CAPTURES_FILE), exist_ok=True)
    with open(CAPTURES_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


CAPTURES = _load_captures()


def _kid_for_channel(channel_id, drm):
    """Gera uma KID:KEY fabricada para o canal (apenas se for DRM).
    A chave e o KID dependem da revisao do provedor (rotacionam juntos):
    quando o provedor gira os tokens, o par KID:KEY tambem muda.
    """
    if not drm or "Widevine" not in str(drm):
        return None
    rev = _TOKEN_STATE["revision"]
    kid = _h(f"kid:{channel_id}:{rev}")[:8].upper()
    key = _h(f"key:{channel_id}:{rev}")[:16].upper()
    return f"{kid}:{key}"


_STREAM_POOL = {
    "globo": "globo_rj_sim",
    "telecine": "telecine_sim",
    "sportv": "sportv_sim",
    "premiere": "sportv_sim",
    "pluto": "pluto_filmes_sim",
    "soul": "soul_mg_sim",
    "record": "record_sp_sim",
    "caze": "cazetv_sim",
    "sbt": "sbtnews_sim",
}
_STREAM_FALLBACKS = [
    "globo_rj_sim", "telecine_sim", "sportv_sim", "pluto_filmes_sim",
    "soul_mg_sim", "record_sp_sim", "cazetv_sim", "sbtnews_sim",
]


def _real_stream_id(name, provider=""):
    key = (name + " " + (provider or "")).lower()
    for kw, sid in _STREAM_POOL.items():
        if kw in key:
            return sid
    idx = sum(ord(c) for c in key) % len(_STREAM_FALLBACKS)
    return _STREAM_FALLBACKS[idx]


def _real_stream_url(name, provider="", host=None):
    sid = _real_stream_id(name, provider)
    host = host or "127.0.0.1:8484"
    return f"http://{host}/streams/{sid}/index.m3u8"


@app.route("/api/captures")
def api_captures():
    return jsonify({
        "captures": CAPTURES,
        "total": len(CAPTURES),
        "aviso": "Capturas 100% sinteticas (KID:KEY fabricadas e links de streams fake).",
    })


@app.route("/api/captures/clear", methods=["POST", "DELETE"])
def api_captures_clear():
    """Limpa todas as capturas do banco (KID:KEY e links M3U)."""
    global CAPTURES
    CAPTURES = []
    _save_captures(CAPTURES)
    return jsonify({"ok": True, "total": 0, "message": "Capturas limpas do servidor."})


@app.route("/api/channels/<channel_id>/capture", methods=["POST"])
def api_capture_channel(channel_id):
    """Simula a captura automática de um canal:
       - DRM (Widevine L3): gera e salva a KID:KEY no banco.
       - FAST/Sem DRM: captura o link M3U direto (reprodução ilimitada).
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name") or f"Canal {channel_id}"
    drm = data.get("drm", "Sem DRM")
    provider = data.get("provider", "Provedor (simulado)")

    host = request.host
    is_drm = "Widevine" in str(drm)

    real_url = _real_stream_url(name, provider, host)
    if is_drm:
        kid = _kid_for_channel(channel_id, drm)
        capture = {
            "id": _h(f"{channel_id}:{time.time()}")[:12],
            "type": "drm_key",
            "channel": name,
            "provider": provider,
            "drm": drm,
            "kid_key": kid,
            "stream_url": real_url,
            "captured_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "aviso": "KID:KEY FABRICADA. Nao abre conteudo protegido real.",
        }
    else:
        # FAST / sem DRM: o "pirata" simplesmente copia o link M3U e reproduz.
        capture = {
            "id": _h(f"{channel_id}:{time.time()}")[:12],
            "type": "fast_m3u",
            "channel": name,
            "provider": provider,
            "drm": drm,
            "kid_key": None,
            "stream_url": real_url,
            "m3u_link": real_url,
            "captured_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "aviso": "Link M3U de stream FAST (sintetico) copiado automaticamente.",
        }
    CAPTURES.insert(0, capture)
    if len(CAPTURES) > 500:
        CAPTURES[:] = CAPTURES[:500]
    _save_captures(CAPTURES)
    return jsonify({"ok": True, "capture": capture, "message": f"Canal '{name}' capturado (simulado)."})


@app.route("/token/validate")
def token_validate():
    token = request.args.get("token", "0000")
    return jsonify({
        "token": token[:6] + "***",
        "valid": True,
        "simulated": True,
        "provider": random.choice(["SkyPlus", "GloboPlay", "RecordPlus", "SoulTV"]),
        "expires_in_sec": random.randint(3600, 86400),
    })


# ---------------------------------------------------------------------------
# PROVEDORES — CRUD completo (cadastrar / editar / excluir)
# ---------------------------------------------------------------------------

@app.route("/api/providers")
def api_providers():
    return jsonify({
        "providers": PROVIDERS,
        "total": len(PROVIDERS),
        "aviso": "Provedores 100% simulados.",
    })


@app.route("/api/providers", methods=["POST"])
def api_provider_create():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Nome do provedor é obrigatório."}), 400
    slug = _slugify(name)
    # evita id duplicado
    base = slug
    i = 2
    while any(p["id"] == slug for p in PROVIDERS):
        slug = f"{base}-{i}"
        i += 1
    # Servidor: aceita domínio/IP digitado pelo operador; se vazio, gera subdomínio automático.
    server = (data.get("server") or data.get("host") or data.get("url") or "").strip()
    if not server:
        server = _server_for(name)
    prov = {
        "id": slug,
        "name": name,
        "total_channels": data.get("total_channels", 50),
        "drm": data.get("drm", "Sem DRM"),
        "desc": data.get("desc", "Provedor simulado cadastrado pelo operador."),
        "subdomain": slug,
        "server": server,
    }
    PROVIDERS.append(prov)
    _persist()
    return jsonify({"ok": True, "provider": prov,
                    "message": f"Provedor '{name}' cadastrado. Link do servidor: {prov['server']}"})


@app.route("/api/providers/<pid>", methods=["PUT"])
def api_provider_update(pid):
    data = request.get_json(silent=True) or {}
    prov = next((p for p in PROVIDERS if p["id"] == pid), None)
    if not prov:
        return jsonify({"ok": False, "error": "Provedor não encontrado."}), 404
    if data.get("name"):
        prov["name"] = data["name"].strip()
        prov["subdomain"] = _slugify(prov["name"])
        if not (data.get("server") or data.get("host") or data.get("url")):
            prov["server"] = _server_for(prov["name"])
    if data.get("server") or data.get("host") or data.get("url"):
        prov["server"] = (data.get("server") or data.get("host") or data.get("url")).strip()
    if "total_channels" in data:
        prov["total_channels"] = data["total_channels"]
    if data.get("drm"):
        prov["drm"] = data["drm"]
    if data.get("desc"):
        prov["desc"] = data["desc"]
    _persist()
    return jsonify({"ok": True, "provider": prov, "message": "Provedor atualizado."})


@app.route("/api/providers/<pid>", methods=["DELETE"])
def api_provider_delete(pid):
    global PROVIDERS
    before = len(PROVIDERS)
    PROVIDERS = [p for p in PROVIDERS if p["id"] != pid]
    if len(PROVIDERS) == before:
        return jsonify({"ok": False, "error": "Provedor não encontrado."}), 404
    _persist()
    return jsonify({"ok": True, "message": "Provedor excluído."})


# ---------------------------------------------------------------------------
# ROTAÇÃO DE TOKENS / LINKS
# ---------------------------------------------------------------------------
_TOKEN_STATE = {
    "revision": 1,
    "last_rotate": None,
    "rotate_count": 0,
}


def _channel_token(channel_id):
    return "TK-" + _h(f"{channel_id}:{_TOKEN_STATE['revision']}")[:14]


@app.route("/api/live_tokens")
def live_tokens():
    manifest = _load_manifest()
    tokens = []
    for m in manifest:
        cid = m["name"]
        t = _channel_token(cid)
        # O manifest usa "type" (drm/fast); deriva o DRM real daqui.
        drm = "Widevine L3 (simulado)" if m.get("type") == "drm" else "Sem DRM (FAST)"
        tokens.append({
            "channel": cid,
            "token": t,
            "url": f"http://{request.host}{m['url']}?token={t}",
            "drm": drm,
            "kid_key": _kid_for_channel(cid, drm),
        })
    return jsonify({
        "revision": _TOKEN_STATE["revision"],
        "last_rotate": _TOKEN_STATE["last_rotate"],
        "rotate_count": _TOKEN_STATE["rotate_count"],
        "tokens": tokens,
        "aviso": "Tokens/links 100% sintéticos. Rotação simulada do provedor.",
    })


@app.route("/api/rotate", methods=["POST"])
def rotate_tokens():
    _TOKEN_STATE["revision"] += 1
    _TOKEN_STATE["rotate_count"] += 1
    _TOKEN_STATE["last_rotate"] = datetime.datetime.utcnow().isoformat()

    # Re-emite as KID:KEY das capturas DRM salvas: a antiga fica invalida
    # e a nova e gerada automaticamente (simula a rotacao de chave do provedor).
    rotated_keys = 0
    for cap in CAPTURES:
        if cap.get("type") == "drm_key":
            old_kid = cap.get("kid_key")
            new_kid = _kid_for_channel(cap.get("channel"), cap.get("drm"))
            cap["kid_key"] = new_kid
            cap["previous_key"] = old_kid
            cap["rotated_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            rotated_keys += 1
    if rotated_keys:
        _save_captures(CAPTURES)

    return jsonify({
        "ok": True,
        "revision": _TOKEN_STATE["revision"],
        "rotate_count": _TOKEN_STATE["rotate_count"],
        "rotated_keys": rotated_keys,
        "message": "Tokens, links e KID:KEY rotacionados pelo provedor (simulado). Chaves antigas agora invalidas.",
    })


@app.route("/api/cfg/template")
def cfg_template():
    return jsonify({
        "format": "XUI-CFG-SIMULADO",
        "fields": ["provider", "client", "quality", "audio", "channels"],
        "sample": {
            "provider": "SkyPlus (sintetico)",
            "client": "cliente-teste",
            "quality": "SD_PT",
            "channels": [
                {"name": "Telecine Action", "cid": "CID-FAKE-0001", "quality": "HD_PT", "drm": "Widevine L3 (simulado)"},
                {"name": "Studio Universal", "cid": "CID-FAKE-0002", "quality": "SD_PT", "drm": "Widevine L3 (simulado)"},
            ],
        },
    })


@app.route("/api/logs/sample")
def logs_sample():
    return jsonify({
        "logs": [
            {"ts": "10:43:20", "level": "INFO", "msg": "Iniciando captura (simulada) para GloboPlay_FHD..."},
            {"ts": "10:43:22", "level": "INFO", "msg": "Canais processados (sintetico): 39"},
            {"ts": "10:43:23", "level": "INFO", "msg": "Canais com DRM (sintetico): 12"},
            {"ts": "10:43:24", "level": "INFO", "msg": "Canais reportados com chaves (sintetico): 10"},
            {"ts": "10:43:26", "level": "INFO", "msg": "Gerando globo_cliente_vps_FHD.cfg (132KB)"},
            {"ts": "10:43:27", "level": "INFO", "msg": "Deploy SSH (simulado) em VPS 'teste'..."},
            {"ts": "10:43:28", "level": "INFO", "msg": "Todos os CFGs foram gerados com sucesso"},
            {"ts": "10:43:28", "level": "INFO", "msg": "Processo de captura finalizado. Finalizado com codigo 0"},
        ]
    })


# ---------------------------------------------------------------------------
# CONTAS DE TESTE — CRUD completo (cadastrar / editar / excluir)
# ---------------------------------------------------------------------------

@app.route("/api/auth/accounts")
def auth_accounts():
    return jsonify({
        "accounts": DEMO_ACCOUNTS,
        "aviso": "Contas 100% simuladas. Nenhuma credencial real. Nenhum provedor real.",
    })


@app.route("/api/auth/accounts", methods=["POST"])
def auth_account_create():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"ok": False, "error": "Usuário e senha são obrigatórios."}), 400
    if any(a["username"] == username for a in DEMO_ACCOUNTS):
        return jsonify({"ok": False, "error": f"Usuário '{username}' já existe."}), 409
    acc = {
        "username": username,
        "password": password,
        "provider": data.get("provider") or "Provedor (simulado)",
        "plan": data.get("plan") or "Plano Padrão",
        "expiry": data.get("expiry") or "2027-12-31",
        "max_devices": int(data.get("max_devices") or 3),
        "current_devices": 0,
        "status": data.get("status") or "active",
        "scenario": data.get("scenario") or "ok",
        "note": data.get("note") or "Conta cadastrada pelo operador (simulada).",
    }
    DEMO_ACCOUNTS.append(acc)
    _persist()
    return jsonify({"ok": True, "account": acc, "message": f"Conta '{username}' cadastrada."})


@app.route("/api/auth/accounts/<username>", methods=["PUT"])
def auth_account_update(username):
    data = request.get_json(silent=True) or {}
    acc = next((a for a in DEMO_ACCOUNTS if a["username"] == username), None)
    if not acc:
        return jsonify({"ok": False, "error": "Conta não encontrada."}), 404
    for field in ["password", "provider", "plan", "expiry", "note", "status", "scenario"]:
        if field in data and data[field] not in (None, ""):
            acc[field] = data[field]
    if "max_devices" in data and data["max_devices"]:
        acc["max_devices"] = int(data["max_devices"])
    _persist()
    return jsonify({"ok": True, "account": acc, "message": "Conta atualizada."})


@app.route("/api/auth/accounts/<username>", methods=["DELETE"])
def auth_account_delete(username):
    global DEMO_ACCOUNTS
    before = len(DEMO_ACCOUNTS)
    DEMO_ACCOUNTS = [a for a in DEMO_ACCOUNTS if a["username"] != username]
    if len(DEMO_ACCOUNTS) == before:
        return jsonify({"ok": False, "error": "Conta não encontrada."}), 404
    _persist()
    return jsonify({"ok": True, "message": f"Conta '{username}' excluída."})


# ---------------------------------------------------------------------------
# PLAYLIST M3U (get.php)
# ---------------------------------------------------------------------------

@app.route("/get.php")
def get_playlist():
    username = request.args.get("username", "demo")
    password = request.args.get("password", "")
    output = request.args.get("output", "ts")
    manifest = _load_manifest()
    host = request.host

    lines = ["#EXTM3U"]
    for m in manifest:
        name = m["name"]
        url = f"http://{host}{m['url']}"
        lines.append(f"#EXTINF:-1,{name}")
        lines.append(url)

    return Response(
        "\n".join(lines),
        mimetype="audio/x-mpegurl",
        headers={
            "Content-Disposition": 'attachment; filename="playlist.m3u"',
            "X-DEFENSE-CORE": "playlist-simulada",
        },
    )


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    device_id = (data.get("device_id") or "").strip() or "DEV-" + hashlib.sha256(
        f"{username}{time.time()}".encode()
    ).hexdigest()[:8].upper()

    acc = next((a for a in DEMO_ACCOUNTS if a["username"] == username), None)

    if not acc:
        return jsonify({
            "ok": False,
            "error": "usuario_nao_encontrado",
            "message": f"Usuário '{username}' não encontrado no provedor.",
        })

    # CONTA EXCLUSIVA DO PROVEDOR: a credencial so vale no provedor dela.
    provider_requested = (data.get("provider") or "").strip()
    if provider_requested and acc.get("provider") != provider_requested:
        return jsonify({
            "ok": False,
            "error": "conta_de_outro_provedor",
            "message": (
                "A conta '" + username + "' pertence ao provedor '" + str(acc.get("provider")) + "', "
                "nao a '" + provider_requested + "'. Use a conta correta do provedor selecionado."
            ),
        })

    if password != acc["password"]:
        return jsonify({
            "ok": False,
            "error": "senha_incorreta",
            "message": "Senha incorreta. Verifique e tente novamente.",
        })

    if acc["status"] == "blocked":
        return jsonify({
            "ok": False,
            "error": "conta_bloqueada",
            "message": "Conta bloqueada/revogada pelo provedor (suspeita de compartilhamento).",
        })

    if acc["status"] == "expired":
        return jsonify({
            "ok": False,
            "error": "expirada",
            "message": f"Assinatura expirada em {acc['expiry']}. Renove para continuar.",
        })

    if acc["scenario"] == "limit_screens":
        return jsonify({
            "ok": False,
            "error": "limite_telas",
            "message": (
                f"Limite de telas simultâneas atingido "
                f"({acc['current_devices']}/{acc['max_devices']}). "
                "Desconecte um dispositivo para liberar."
            ),
        })

    session_token = hashlib.sha256(
        f"{username}{time.time()}{random.random()}".encode()
    ).hexdigest()[:24]

    # servidor do provedor (subdomínio) caso exista
    prov = next((p for p in PROVIDERS if p["name"] == acc["provider"]), None)
    # Endereço público do próprio servidor: se PUBLIC_URL estiver definido (cenário VPS),
    # os links gerados (playlist etc.) apontam para a VPS correta. Senão, mantém o
    # subdomínio fake de demonstração local.
    public_base = (os.environ.get("PUBLIC_URL") or "").strip().rstrip("/")
    server = public_base or (prov["server"] if prov and prov.get("server") else "http://127.0.0.1:8484")

    result = {
        "ok": True,
        "session_token": session_token,
        "provider": acc["provider"],
        "plan": acc["plan"],
        "expiry": acc["expiry"],
        "max_devices": acc["max_devices"],
        "current_devices": acc["current_devices"],
        "device_id": device_id,
        "channels_available": random.randint(80, 900),
        "server": server,
        "playlist": (
            f"{server}/get.php?username={username}"
            f"&password={password}&type=m3u_plus&output=ts"
        ),
    }

    if acc.get("scenario") == "geo_anomaly":
        result["warning"] = (
            "Anomalia geográfica detectada: sessão ativa em São Paulo e Miami "
            "simultaneamente (intervalo impossível)."
        )
        result["alert_rule"] = "RULE-002"

    return jsonify(result)


_start = time.time()

if __name__ == "__main__":
    print("=" * 60)
    _host = os.environ.get("HOST", "127.0.0.1")
    _port = int(os.environ.get("PORT", "8484"))
    print(f"DEFENSE-CORE (servidor FICTICIO) rodando em http://{_host}:{_port}")
    print("MODO:", MODE)
    print("Nenhuma extracao real. Nenhuma chave real. Nenhum token real.")
    print("=" * 60)
    app.run(host=_host, port=_port, debug=False)
