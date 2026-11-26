# -*- coding: utf-8 -*-
"""
Adaptador Pluto TV (API oficial pública — canais FAST, gratuitos e SEM DRM).

Usa o endpoint público:
    GET https://api.pluto.tv/v2/channels?start=<DATA_ISO>&stop=<DATA_ISO>

A Pluto TV é um serviço FAST (Free Ad-supported Streaming Television):
o conteúdo é GRATUITO e a API é oficial/pública. Não há quebra de DRM,
não há captura de credenciais — apenas leitura da grade de canais e dos
links HLS públicos fornecidos pela própria Pluto.

Este módulo é usado para DEMONSTRAÇÃO/DOCUMENTAÇÃO: mostra ao cliente
como um catálogo FAST real (sem DRM) entrega o stream direto num link
HLS aberto — exatamente o vetor que precisa ser monitorado.
"""
import datetime
import re
import uuid
import requests
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

UA = {
    "User-Agent": "DefenseLab/1.0 (authorized research client)",
    "Accept": "application/json",
}

# Base oficial da API da Pluto TV
PLUTO_API = "https://api.pluto.tv/v2/channels"


def detect(base):
    """Reconhece se o endereço informado é a API oficial da Pluto TV."""
    base = (base or "").strip().lower().rstrip("/")
    return "pluto.tv" in base


def _normalize(base):
    base = (base or "").strip().rstrip("/")
    if base and "://" not in base:
        base = "https://" + base
    return base


def _fetch_channels():
    """Busca a grade de canais da Pluto TV (janela de 24h)."""
    now = datetime.datetime.utcnow()
    start = (now - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stop = (now + datetime.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = requests.get(
        PLUTO_API,
        params={"start": start, "stop": stop},
        headers=UA, timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _stream_url(ch):
    """Extrai o link HLS público (stitched) de um canal.

    A API devolve o link com parâmetros 'unknown'/vazios que o servidor
    da Pluto REJEITA (HTTP 400). Aqui reescrevemos a query string com
    valores válidos (deviceId real, região BR, coordenadas e timestamp),
    gerando um link que reproduz de verdade no VLC/navegador.
    """
    st = ch.get("stitched") or {}
    urls = st.get("urls") or []
    raw = ""
    for u in urls:
        if (u.get("type") or "").lower() == "hls":
            raw = u.get("url") or ""
            break
    if not raw and urls:
        raw = urls[0].get("url") or ""
    return _fix_stream_url(raw)


def _fix_stream_url(raw):
    """Preenche os parâmetros obrigatórios da query da Pluto TV."""
    if not raw:
        return raw
    p = urlparse(raw)
    qs = dict(parse_qsl(p.query, keep_blank_values=True))
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    dev = str(uuid.uuid4())
    # Parâmetros que o stitcher exige preenchidos (senão responde 400)
    qs.update({
        "advertisingId": "",
        "appName": "web",
        "appVersion": "na",
        "architecture": "",
        "buildVersion": "",
        "clientTime": now,
        "deviceDNT": "0",
        "deviceId": dev,
        "deviceLat": "-23.5505",   # São Paulo (BR)
        "deviceLon": "-46.6333",
        "deviceMake": "Chrome",
        "deviceModel": "web",
        "deviceType": "web",
        "deviceVersion": "130.0",
        "includeExtendedEvents": "false",
        "marketingRegion": "BR",
        "sid": dev[:16],
        "userId": dev,
    })
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(qs), p.fragment))


def _logo(ch):
    return (ch.get("logo") or {}).get("path") or (ch.get("featuredImage") or {}).get("path") or ""


_RES_CACHE = {}


def detect_resolution(stream_url, timeout=6):
    """Detecta a resolução REAL do HLS adaptativo da Pluto.

    O master.m3u8 traz as variantes com BANDWIDTH (não RESOLUTION).
    A resolução exata fica no caminho dos segmentos (ex.: '1080pDRM').
    Mapeamos a maior banda para o rótulo correto (SD/HD/FHD/4K).
    """
    if not stream_url:
        return "HD"
    if stream_url in _RES_CACHE:
        return _RES_CACHE[stream_url]
    label = "HD"
    try:
        r = requests.get(stream_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        txt = r.text or ""
        bws = [int(m) for m in re.findall(r"BANDWIDTH=(\d+)", txt)]
        if bws:
            mx = max(bws)
            if mx >= 4500000:
                label = "4K"
            elif mx >= 2500000:
                label = "FHD"
            elif mx >= 1200000:
                label = "HD"
            else:
                label = "SD"
    except Exception:
        pass
    _RES_CACHE[stream_url] = label
    return label


def _quality(ch):
    # A Pluto entrega HLS adaptativo (resolução varia com a banda).
    # Retornamos "HD" como rótulo padrão (perfil típico da Pluto);
    # a resolução real é detectada sob demanda em detect_resolution().
    return "HD"


def map_channel(ch):
    """Converte um canal da Pluto para o formato do painel."""
    cid = ch.get("_id") or ch.get("slug") or "?"
    number = ch.get("number", "")
    return {
        "id": str(cid),
        "cid": f"CID-{str(number or cid)[:8]}",
        "name": ch.get("name") or "Canal Pluto",
        "category": ch.get("category") or "FAST",
        "quality": _quality(ch),
        "audio": "PT/EN",
        "provider": "Pluto TV (API oficial)",
        "drm": "Sem DRM (FAST)",
        "kid": None,
        "kid_key": None,
        "stream_url": _stream_url(ch),
        "m3u_link": _stream_url(ch),
        "logo": _logo(ch),
        "source": "pluto",
    }


def login(base, username=None, password=None):
    """'Login' na Pluto TV: não há credencial (é FAST gratuito).

    Devolve payload no formato do painel. username/password são ignorados
    (a Pluto não pede login), mantidos na assinatura por compatibilidade.
    """
    base = _normalize(base)
    try:
        channels = _fetch_channels()
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "core_offline",
                "message": "Tempo esgotado ao consultar a API da Pluto TV."}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "core_offline",
                "message": "Não foi possível conectar à API da Pluto TV."}
    except Exception as e:
        return {"ok": False, "error": "core_offline",
                "message": f"Erro ao consultar a Pluto TV: {e}"}

    return {
        "ok": True,
        "protocol": "pluto",
        "provider": "Pluto TV (API oficial)",
        "server": base,
        "username": username or "—",
        "session_token": None,
        "auth_method": "Sem autenticação — catálogo FAST público (gratuito, sem DRM)",
        "plan": "Gratuito (FAST)",
        "expires": "N/A",
        "expiry": "N/A",
        "devices": "ilimitado",
        "current_devices": 0,
        "max_devices": "∞",
        "channels_count": len(channels),
        "channels_available": f"{len(channels)} canais FAST",
        "playlist": None,
        "captured": False,
        "message": "Catálogo FAST público da Pluto TV carregado (sem credencial, sem DRM).",
    }


def channels():
    """Lista os canais da Pluto TV no formato do painel."""
    try:
        raw = _fetch_channels()
    except Exception:
        return []
    return [map_channel(c) for c in raw if isinstance(c, dict)]


def channel_by_id(cid):
    """Busca um canal específico da Pluto pelo id."""
    for c in channels():
        if str(c["id"]) == str(cid):
            return c
    return None
