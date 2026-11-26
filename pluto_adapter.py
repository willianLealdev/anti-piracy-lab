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
import requests

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
    """Extrai o link HLS público (stitched) de um canal."""
    st = ch.get("stitched") or {}
    urls = st.get("urls") or []
    for u in urls:
        if (u.get("type") or "").lower() == "hls":
            return u.get("url") or ""
    return (urls[0].get("url") or "") if urls else ""


def _logo(ch):
    return (ch.get("logo") or {}).get("path") or (ch.get("featuredImage") or {}).get("path") or ""


def _quality(ch):
    # A API não informa resolução nominal; a Pluto entrega HLS adaptativo.
    # Marcamos "HLS" (adaptativo) para não inventar SD/HD/FHD.
    return "HLS"


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
