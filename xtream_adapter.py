# -*- coding: utf-8 -*-
"""
Adaptador Xtream Codes (protocolo /player_api.php).

Permite que o painel conecte em painéis IPTV reais que falam o protocolo
Xtream Codes (XUI.one, Xtream UI, etc.) — usado SOMENTE em servidores
autorizados (pentest com permissão do dono).

Este módulo é um CLIENTE do protocolo: apenas faz requisições HTTP de
LEITURA (autenticação, listagem de canais, geração de playlist). Não
quebra DRM, não captura chaves, não baixa/retransmite conteúdo.

Protocolo suportado:
    GET {base}/player_api.php?username=X&password=Y
    GET {base}/player_api.php?username=X&password=Y&action=get_live_streams
    GET {base}/get.php?username=X&password=Y&type=m3u_plus&output=ts
    Streams: {base}/live/{user}/{pass}/{stream_id}.ts
"""
import requests


TIMEOUT = 8
UA = {"User-Agent": "DefenseLab/1.0 (authorized pentest client)"}


def _url(base, **params):
    base = (base or "").strip().rstrip("/")
    qs = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    return f"{base}/player_api.php?{qs}"


def detect(base):
    """Verifica se o servidor fala o protocolo Xtream (tem player_api.php).

    Retorna True/False. Não autentica; apenas confirma a presença do endpoint.
    """
    try:
        r = requests.get(
            _url(base, username="__probe__", password="__probe__"),
            headers=UA, timeout=6,
        )
        # Xtream responde JSON mesmo com credencial inválida (auth: 0).
        ct = (r.headers.get("content-type") or "").lower()
        if "json" in ct:
            return True
        try:
            r.json()
            return True
        except Exception:
            return False
    except Exception:
        return False


def login(base, username, password):
    """Autentica num painel Xtream e devolve um payload no formato do painel.

    Retorna dict com as mesmas chaves que o DEFENSE-CORE devolve no
    /api/auth/login, para o frontend não precisar mudar.
    """
    base = (base or "").strip().rstrip("/")
    if base and "://" not in base:
        base = "http://" + base
    try:
        r = requests.get(
            _url(base, username=username, password=password),
            headers=UA, timeout=TIMEOUT,
        )
        data = r.json()
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "core_offline",
                "message": "Tempo esgotado ao conectar no painel Xtream."}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "core_offline",
                "message": f"Não foi possível conectar ao servidor ({base})."}
    except Exception as e:
        return {"ok": False, "error": "core_offline",
                "message": f"Erro de conexão: {e}"}

    ui = data.get("user_info") or {}
    auth = int(ui.get("auth", 0))

    if auth != 1:
        status = str(ui.get("status", "")).lower()
        if "banned" in status or "disabled" in status:
            return {"ok": False, "error": "conta_bloqueada",
                    "message": "Conta bloqueada/revogada no painel."}
        return {"ok": False, "error": "senha_incorreta",
                "message": "Credenciais inválidas (auth != 1)."}

    # Data de expiração (timestamp unix) -> data legível
    exp = None
    try:
        exp = int(ui.get("exp_date") or 0)
    except Exception:
        exp = 0
    import datetime
    exp_date = None
    if exp and exp > 0:
        exp_date = datetime.datetime.utcfromtimestamp(exp).strftime("%Y-%m-%d")

    max_conn = ui.get("max_connections", "?")
    active = ui.get("active_cons", "0")

    # Token de sessão = hash determinístico da credencial (só para exibição
    # no Vault na demo; não é segredo real do servidor).
    import hashlib
    token = hashlib.sha256(f"{base}|{username}|{password}".encode()).hexdigest()

    # Conta os canais/filmes/séries reais do painel (para o login já
    # mostrar "Canais" preenchido, igual o pirata vê ao autenticar).
    live_count = vod_count = series_count = 0
    try:
        live = get_live_streams(base, username, password)
        live_count = len(live) if isinstance(live, list) else 0
    except Exception:
        live_count = 0
    try:
        vod_count = len(get_vod_streams(base, username, password) or [])
    except Exception:
        vod_count = 0
    try:
        series_count = len(get_series(base, username, password) or [])
    except Exception:
        series_count = 0

    playlist = m3u_url(base, username, password)

    return {
        "ok": True,
        "protocol": "xtream",
        "provider": "Painel Xtream Codes",
        "server": base,
        "username": username,
        "session_token": token,
        "plan": f"{max_conn} conexões",
        "expires": exp_date or "N/D",
        "expiry": exp_date or "N/D",
        "devices": f"{active}/{max_conn}",
        "current_devices": active,
        "max_devices": max_conn,
        "channels_count": live_count,
        "channels_available": f"{live_count} canais · {vod_count} filmes · {series_count} séries",
        "playlist": playlist,
        "captured": True,
        "captured_token_id": token[:12].upper(),
        "message": "Autenticado no painel Xtream Codes (protocolo player_api.php).",
    }


def get_live_streams(base, username, password):
    """Lista os canais ao vivo do painel Xtream."""
    base = (base or "").strip().rstrip("/")
    try:
        r = requests.get(
            _url(base, username=username, password=password,
                 action="get_live_streams"),
            headers=UA, timeout=TIMEOUT,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def get_vod_streams(base, username, password):
    """Lista filmes (VOD) do painel Xtream."""
    base = (base or "").strip().rstrip("/")
    try:
        r = requests.get(
            _url(base, username=username, password=password,
                 action="get_vod_streams"),
            headers=UA, timeout=TIMEOUT,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def get_series(base, username, password):
    """Lista séries do painel Xtream."""
    base = (base or "").strip().rstrip("/")
    try:
        r = requests.get(
            _url(base, username=username, password=password,
                 action="get_series"),
            headers=UA, timeout=TIMEOUT,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def m3u_url(base, username, password, output="ts"):
    """URL pública da playlist M3U (get.php) do painel."""
    base = (base or "").strip().rstrip("/")
    return (f"{base}/get.php?username={username}&password={password}"
            f"&type=m3u_plus&output={output}")


def stream_url(base, username, password, stream_id, ext="ts"):
    """URL de reprodução direta de um canal (live)."""
    base = (base or "").strip().rstrip("/")
    return f"{base}/live/{username}/{password}/{stream_id}.{ext}"


def map_channel(ch, username, password, base):
    """Converte um canal Xtream para o formato do painel (canais & DRM)."""
    sid = ch.get("stream_id", ch.get("num", "?"))
    name = ch.get("name") or f"Canal {sid}"
    # Heurística de DRM para a demo: se o painel permite m3u8 (HLS),
    # trata como "possível DRM" (Widevine/ClearKey); .ts direto = clear.
    # (No Xtream real o painel não expõe o DRM; marcamos como "indeterminado"
    # para não inventar chave.)
    return {
        "id": str(sid),
        "name": name,
        "category": ch.get("category_id") or "—",
        "quality": "HD" if str(sid).isdigit() and int(sid) % 2 == 0 else "SD",
        "audio": "PT",
        "provider": "Painel Xtream Codes",
        "drm": "Indeterminado",
        "kid_key": None,
        "stream_url": stream_url(base, username, password, sid),
        "m3u_link": stream_url(base, username, password, sid),
        "source": "xtream",
    }
