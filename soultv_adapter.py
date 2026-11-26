# -*- coding: utf-8 -*-
"""
Adaptador Soul TV Brasil (plataforma FAST — canais gratuitos, sem DRM).

A Soul TV entrega, no próprio HTML do site, um JSON com a grade de canais
e o link HLS público (url_live_streaming) de cada um. É um catálogo FAST
real: conteúdo gratuito, sem login e sem DRM.

Uso: DEMONSTRAÇÃO/DOCUMENTAÇÃO. Mostra ao cliente como um catálogo FAST
nacional expõe o stream HLS aberto — vetor de monitoramento de
redistribuição (não há chave DRM a proteger, pois é gratuito).
"""
import re
import json
import requests

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

SOUL_SITE = "https://soultv.com.br"


def detect(base):
    base = (base or "").strip().lower().rstrip("/")
    return "soultv" in base


def _normalize(base):
    base = (base or "").strip().rstrip("/")
    if base and "://" not in base:
        base = "https://" + base
    return base


def _fetch_raw():
    r = requests.get(SOUL_SITE, headers=UA, timeout=20)
    r.raise_for_status()
    m = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if not m:
        raise RuntimeError("JSON de canais não encontrado no site da Soul TV")
    return json.loads(m.group(1))


def _quality(ch):
    h = ch.get("video_height") or ch.get("main_video_height") or 0
    if h >= 1080:
        return "FHD"
    if h >= 720:
        return "HD"
    return "SD"


def map_channel(ch):
    name = ch.get("name") or "Canal Soul TV"
    stream = ch.get("url_live_streaming") or ch.get("premium_url") or ""
    return {
        "id": str(ch.get("id") or name),
        "cid": f"CID-{ch.get('channel_number') or ch.get('id')}",
        "name": name,
        "category": "FAST",
        "quality": _quality(ch),
        "audio": "PT",
        "provider": "Soul TV Brasil (FAST)",
        "drm": "Sem DRM (FAST)",
        "kid": None,
        "kid_key": None,
        "stream_url": stream,
        "m3u_link": stream,
        "logo": ch.get("image2") or ch.get("background_image") or "",
        "source": "soultv",
    }


def login(base, username=None, password=None):
    base = _normalize(base)
    try:
        data = _fetch_raw()
        chs = data.get("channels") or []
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "core_offline",
                "message": "Tempo esgotado ao consultar a Soul TV."}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "core_offline",
                "message": "Não foi possível conectar ao site da Soul TV."}
    except Exception as e:
        return {"ok": False, "error": "core_offline",
                "message": f"Erro ao consultar a Soul TV: {e}"}

    return {
        "ok": True,
        "protocol": "soultv",
        "provider": "Soul TV Brasil (FAST)",
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
        "channels_count": len(chs),
        "channels_available": f"{len(chs)} canais FAST",
        "playlist": None,
        "captured": False,
        "message": "Catálogo FAST público da Soul TV carregado (sem credencial, sem DRM).",
    }


def channels():
    try:
        data = _fetch_raw()
    except Exception:
        return []
    return [map_channel(c) for c in (data.get("channels") or []) if isinstance(c, dict)]


def channel_by_id(cid):
    for c in channels():
        if str(c["id"]) == str(cid):
            return c
    return None
