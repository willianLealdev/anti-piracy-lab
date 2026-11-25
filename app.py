# -*- coding: utf-8 -*-
"""
AntiPiracy Defense Lab
=======================
Plataforma DEFENSIVA de demonstração.

Simula um sistema de "extrator" (com dados 100% SINTÉTICOS e fabricados)
para que a equipe de engenharia do cliente visualize, módulo a módulo:
  1) o que o atacante enxerga (anatomia),
  2) qual o indicador de comprometimento,
  3) ONDE colocar a trava defensiva.

IMPORTANTE: este sistema NÃO extrai chaves DRM, NÃO captura tokens reais,
NÃO gera CFGs funcionais e NÃO retransmite conteúdo protegido.
Tudo aqui é simulação com dados fabricados, para DETECÇÃO e DEFESA.
"""

import datetime
import hashlib
import json
import os
import random
import threading
import time
import uuid

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

CORE_URL = os.environ.get("CORE_URL", "http://127.0.0.1:8484")


def core_status():
    """Verifica se o servidor fake interno (DEFENSE-CORE) está no ar."""
    try:
        r = requests.get(f"{CORE_URL}/health", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "Offline", "service_name": "DEFENSE-CORE", "mode": "DESCONECTADO"}


# ---------------------------------------------------------------------------
# MULTI-SERVIDOR: roteia cada provedor para o seu próprio "servidor de provedor".
#
# A ideia é permitir topologias reais de demonstração:
#   - VPS 1 = DEFENSE-CORE "DRM"  (PROVIDER_FILTER=skyplus,globoplay,...)
#   - VPS 2 = DEFENSE-CORE "FAST" (PROVIDER_FILTER=pluto,soultv,...)
#   - VPS 3 = DEFENSE-CORE "YouTube"
#
# O painel consulta a lista de provedores no CORE_URL principal (o "registro")
# e, para operações de um provedor específico (login, captura), usa o campo
# "server" daquele provedor — que você define ao cadastrar/editar.
# ---------------------------------------------------------------------------
_PROVIDERS_CACHE = {"ts": 0.0, "data": []}


def _get_providers():
    """Lista viva de provedores (cache de 10s). Fonte: CORE_URL principal."""
    now = time.time()
    if now - _PROVIDERS_CACHE["ts"] < 10 and _PROVIDERS_CACHE["data"]:
        return _PROVIDERS_CACHE["data"]
    try:
        r = requests.get(f"{CORE_URL}/api/providers", timeout=3)
        if r.status_code == 200:
            data = r.json().get("providers", [])
            if data:
                _PROVIDERS_CACHE["data"] = data
                _PROVIDERS_CACHE["ts"] = now
    except Exception:
        pass
    return _PROVIDERS_CACHE["data"] or PROVIDERS


def core_for_provider(provider_name):
    """Retorna a URL do servidor onde o provedor 'vive' (multi-servidor)."""
    if not provider_name:
        return CORE_URL
    for p in _get_providers():
        if p.get("name") == provider_name or p.get("id") == provider_name:
            return p.get("server") or CORE_URL
    return CORE_URL


def _post_json(base_url, path, data, timeout=5):
    """POST com fallback: tenta o servidor do provedor e, se offline, o principal."""
    targets = [base_url]
    if base_url != CORE_URL:
        targets.append(CORE_URL)
    last = None
    for t in targets:
        try:
            r = requests.post(f"{t}{path}", json=data, timeout=timeout)
            return r
        except Exception as e:
            last = e
    raise (last or Exception("DEFENSE-CORE offline"))


# ---------------------------------------------------------------------------
# GERADORES SINTÉTICOS
# ---------------------------------------------------------------------------

def _hash(v):
    return hashlib.sha256(v.encode()).hexdigest()[:16]


def _mask_email(email):
    parts = email.split("@")
    if len(parts) != 2:
        return "***@***"
    local = parts[0]
    dom = parts[1]
    if len(local) <= 3:
        return "***@" + dom
    return local[:2] + "***" + "@" + dom


def _mask_ip(ip):
    parts = ip.split(".")
    return ".".join(parts[:2] + ["***", "***"])


# ---------------------------------------------------------------------------
# MAPEAMENTO: canais catalogados -> streams REAIS reproduzíveis (HLS ffmpeg)
# ---------------------------------------------------------------------------
# Os streams realmente reproduzíveis ficam em streams/*/index.m3u8 (HLS gerado
# por ffmpeg). Os botões de download M3U precisam apontar para esses arquivos,
# nunca para o gerador sintético /stream/<nome>.ts (que não toca no VLC).
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
    """Mapeia um canal catalogado para um stream REAL reproduzível."""
    key = (name + " " + provider).lower()
    for kw, sid in _STREAM_POOL.items():
        if kw in key:
            return sid
    idx = sum(ord(c) for c in key) % len(_STREAM_FALLBACKS)
    return _STREAM_FALLBACKS[idx]


def _real_stream_url(name, provider=""):
    sid = _real_stream_id(name, provider)
    return f"{CORE_URL}/streams/{sid}/index.m3u8"


# ---------------------------------------------------------------------------
# DADOS SINTÉTICOS ESTÁTICOS
# ---------------------------------------------------------------------------

DRM_CORE = {
    "status": "Ativo",
    "service_name": "DEFENSE-LAB",
    "displayed_port": 8484,
    "ram_disk_status": "OK",
    "security_level": "Widevine L3 (simulado)",
}

PROVIDERS = [
    {
        "id": "globoplay",
        "name": "GloboPlay Completo",
        "total_channels": 180,
        "description": "125 Globos Regionais + 9 Premiere HD + 4 SporTV (1,2,3,4K) + 6 Telecine + Combate + GloboNews + Multishow + GNT + Viva + Gloob + FAST + BBB.",
        "drm": "Widevine L3",
        "color": "green",
    },
    {
        "id": "astra",
        "name": "Astra TV (Cesbo)",
        "total_channels": 90,
        "description": "Abertos (SBT, Record, Band, RedeTV), Telecine, SporTV, Filmes, Infantis, Noticias, Religiosos e Variedades.",
        "drm": "Sem DRM",
        "color": "blue",
    },
    {
        "id": "skyplus",
        "name": "Sky+ (DirectvGO)",
        "total_channels": 86,
        "description": "Canais ao vivo com DRM Widevine L3. Captura automatica de chaves KID:KEY no Chrome. Multi-audio PT/EN.",
        "drm": "Widevine L3",
        "color": "gold",
    },
    {
        "id": "primevideo",
        "name": "Prime Video (Amazon)",
        "total_channels": "Ilimitado",
        "description": "CazeTV (1,2,3), ge TV, CNN Brasil, Bloomberg + canais de pacotes extras/Channels da conta. Widevine L3 / ClearKey em FHD e HD.",
        "drm": "Widevine L3 / ClearKey",
        "color": "cyan",
    },
    {
        "id": "pluto",
        "name": "Pluto TV Brasil",
        "total_channels": 187,
        "description": "Canais FAST gratuitos sem DRM: Filmes, Series tematicas, Nickelodeon & Infantis, Animes (Naruto, Yu-Gi-Oh!), Realities (MasterChef) e Noticias.",
        "drm": "Sem DRM",
        "color": "amber",
    },
    {
        "id": "soultv",
        "name": "Soul TV Brasil",
        "total_channels": 77,
        "description": "Canais FAST e regionais brasileiros: Minas Gerais, Filmes/Series, Esportes, Cultura, Musica e Variedades.",
        "drm": "Sem DRM",
        "color": "purple",
    },
    {
        "id": "youtube",
        "name": "YouTube Live",
        "total_channels": 15,
        "description": "CazeTV, Canal GOAT, SBT News 24h, Jovem Pan News, Record News, Dragon Ball Z, Bluey, Boomerang, MMA 24/7.",
        "drm": "Sem DRM",
        "color": "red",
    },
    {
        "id": "recordplus",
        "name": "Record+ / PlayPlus",
        "total_channels": 10,
        "description": "Record SP, Rio de Janeiro, Minas, Brasilia, Bahia, Record News, Curitiba, Fortaleza, Vitoria e Campinas - Streams HLS diretos.",
        "drm": "Sem DRM",
        "color": "teal",
    },
    {
        "id": "bandplay",
        "name": "BandPlay Oficial",
        "total_channels": 29,
        "description": "18 Band Regionais (SP, RJ, MG, RS, PR, DF, BA, BandNews TV, BandSports, Terra Viva) + 11 Radios oficiais sem DRM.",
        "drm": "Sem DRM",
        "color": "orange",
    },
    {
        "id": "hbomax",
        "name": "HBO Max",
        "total_channels": 40,
        "description": "Canais ao vivo HBO, Max Originals, DC, Cartoon Network. Widevine L3 (simulado).",
        "drm": "Widevine L3",
        "color": "violet",
    },
    {
        "id": "disneyplus",
        "name": "Disney+",
        "total_channels": 35,
        "description": "ESPN, Disney Channel, National Geographic, Star. Widevine L3 (simulado).",
        "drm": "Widevine L3",
        "color": "indigo",
    },
    {
        "id": "paramountplus",
        "name": "Paramount+",
        "total_channels": 30,
        "description": "CBS, Nickelodeon, MTV, Paramount Pictures. Widevine L3 (simulado).",
        "drm": "Widevine L3",
        "color": "blue",
    },
    {
        "id": "clarotv",
        "name": "Claro TV+",
        "total_channels": 120,
        "description": "Globos Regionais, SporTV (1,2,3), Premiere, Telecine, Discovery, History, Fox, ESPN, Infantis (Cartoon, Nick, Discovery Kids) + canais de variedades. Widevine L3 (simulado).",
        "drm": "Widevine L3",
        "color": "rose",
    },
]

TOKEN_HEALTH = [
    {
        "provider": "Sky+ (DirectvGO)",
        "account": _mask_email("assinante.sky.001@provedor.com"),
        "status": "VALIDO",
        "remaining_time": "18h23min",
        "expiration": "2026-10-28 10:43:25",
        "abuse": "ALTO",
    },
    {
        "provider": "GloboPlay Completo",
        "account": _mask_email("assinante.globo.014@provedor.com"),
        "status": "VALIDO",
        "remaining_time": "--",
        "expiration": "Nao informada",
        "abuse": "MEDIO",
    },
    {
        "provider": "Prime Video (Amazon)",
        "account": _mask_email("assinante.prime.007@provedor.com"),
        "status": "VALIDO",
        "remaining_time": "2d 11h",
        "expiration": "2026-10-30 08:00:00",
        "abuse": "ALTO",
    },
    {
        "provider": "Pluto TV Brasil",
        "account": _mask_email("operador.pluto.002@provedor.com"),
        "status": "VALIDO",
        "remaining_time": "7d 02h",
        "expiration": "2026-11-04 15:00:00",
        "abuse": "BAIXO",
    },
    {
        "provider": "Record+ / PlayPlus",
        "account": _mask_email("revenda.record.003@provedor.com"),
        "status": "EXPIRANDO",
        "remaining_time": "41min",
        "expiration": "2026-10-28 01:12:00",
        "abuse": "BAIXO",
    },
    {
        "provider": "BandPlay Oficial",
        "account": _mask_email("operador.band.001@provedor.com"),
        "status": "VALIDO",
        "remaining_time": "5d 03h",
        "expiration": "2026-11-02 12:00:00",
        "abuse": "BAIXO",
    },
    {
        "provider": "HBO Max",
        "account": _mask_email("assinante.hbo.021@provedor.com"),
        "status": "VALIDO",
        "remaining_time": "9h 12min",
        "expiration": "2026-10-28 22:30:00",
        "abuse": "MEDIO",
    },
    {
        "provider": "Disney+",
        "account": _mask_email("assinante.disney.009@provedor.com"),
        "status": "VALIDO",
        "remaining_time": "1d 06h",
        "expiration": "2026-10-29 18:00:00",
        "abuse": "MEDIO",
    },
    {
        "provider": "Claro TV+",
        "account": _mask_email("assinante.claro.005@provedor.com"),
        "status": "VALIDO",
        "remaining_time": "3d 08h",
        "expiration": "2026-10-31 20:00:00",
        "abuse": "ALTO",
    },
]

# ---------------------------------------------------------------------------
# PERSISTÊNCIA (VPS + canais YouTube sobrevivem a reinícios)
# ---------------------------------------------------------------------------

PANEL_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "panel_state.json")

DEFAULT_VPS = [
    {
        "id": "vps-1",
        "name": "teste",
        "ip": "198.***.***.***",
        "real_ip": "198.51.100.10",
        "status": "active",
        "ssh_port": 22,
        "web_path": "/var/www/html/directv/",
        "token": "Teste",
    },
]

DEFAULT_YT = [
    {"id": "yt1", "name": "CazeTV Ao Vivo", "handle": "@CazeTV", "category": "Esportes", "live": "ONLINE", "broadcast": "Monaco x Lille"},
    {"id": "yt2", "name": "Canal GOAT", "handle": "@canalgoatbr", "category": "Esportes", "live": "OFFLINE", "broadcast": "Aguardando proxima transmissao ao vivo"},
    {"id": "yt3", "name": "SBT News 24h", "handle": "@sbtnews", "category": "Noticias", "live": "ONLINE", "broadcast": "RADAR NEWS"},
    {"id": "yt4", "name": "TNT Sports BR", "handle": "@tntsportsbr", "category": "Esportes", "live": "ONLINE", "broadcast": "Champions League"},
    {"id": "yt5", "name": "ESPN Brasil", "handle": "@espnbrasil", "category": "Esportes", "live": "OFFLINE", "broadcast": "Aguardando"},
    {"id": "yt6", "name": "ge", "handle": "@ge", "category": "Esportes", "live": "ONLINE", "broadcast": "Brasileirao Serie A"},
    {"id": "yt7", "name": "Band Jornalismo", "handle": "@bandjornalismo", "category": "Noticias", "live": "ONLINE", "broadcast": "Jornal da Band"},
    {"id": "yt8", "name": "Record News", "handle": "@recordnews", "category": "Noticias", "live": "ONLINE", "broadcast": "JR 24h"},
]


def _load_panel_state():
    if os.path.exists(PANEL_STATE_FILE):
        try:
            with open(PANEL_STATE_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
            return st.get("vps", list(DEFAULT_VPS)), st.get("youtube", list(DEFAULT_YT))
        except Exception:
            pass
    return list(DEFAULT_VPS), list(DEFAULT_YT)


def _save_panel_state(vps_list, yt_list):
    os.makedirs(os.path.dirname(PANEL_STATE_FILE), exist_ok=True)
    with open(PANEL_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"vps": vps_list, "youtube": yt_list}, f, ensure_ascii=False, indent=2)


CONNECTED_SERVERS, YOUTUBE_CHANNELS = _load_panel_state()

CATEGORIES = [
    "Todos", "Globos Regionais", "Premiere", "SporTV", "Telecine",
    "Filmes & Series", "Infantis", "Noticias", "Esportes", "Realities",
    "FAST", "Cultura", "Musica", "Variedades", "Abertos", "Animes",
    "Religiosos", "Radios",
]

# Catálogo por provedor: contagem realista + nomes reais (sementes) + DRM.
# O gerador completa até a contagem usando as sementes + numeração.
_PROVIDER_CATALOG = {
    "GloboPlay": {
        "count": 180, "drm": "Widevine L3",
        "seeds": [
            ("Globo RJ", "Globos Regionais"), ("Globo SP", "Globos Regionais"),
            ("Globo MG", "Globos Regionais"), ("Globo DF", "Globos Regionais"),
            ("Globo BA", "Globos Regionais"), ("Globo PE", "Globos Regionais"),
            ("Globo CE", "Globos Regionais"), ("Globo RS", "Globos Regionais"),
            ("Globo PR", "Globos Regionais"), ("Globo AM", "Globos Regionais"),
            ("Premiere 1", "Premiere"), ("Premiere 2", "Premiere"), ("Premiere 3", "Premiere"),
            ("Premiere 4", "Premiere"), ("Premiere 5", "Premiere"), ("Premiere 6", "Premiere"),
            ("Premiere 7", "Premiere"), ("Premiere 8", "Premiere"), ("Premiere 9", "Premiere"),
            ("SporTV 1", "SporTV"), ("SporTV 2", "SporTV"), ("SporTV 3", "SporTV"), ("SporTV 4", "SporTV"),
            ("Telecine Action", "Telecine"), ("Telecine Premium", "Telecine"), ("Telecine Pipoca", "Telecine"),
            ("Telecine Touch", "Telecine"), ("Telecine Fun", "Telecine"), ("Telecine Cult", "Telecine"),
            ("Combate", "Esportes"), ("GloboNews", "Noticias"), ("Multishow", "Variedades"),
            ("GNT", "Variedades"), ("Viva", "Variedades"), ("Gloob", "Infantis"), ("BBB", "Realities"),
        ],
    },
    "Astra": {
        "count": 90, "drm": "Sem DRM",
        "seeds": [
            ("SBT", "Abertos"), ("Record TV", "Abertos"), ("Band", "Abertos"), ("RedeTV", "Abertos"),
            ("Telecine Action", "Telecine"), ("Telecine Premium", "Telecine"), ("Telecine Pipoca", "Telecine"),
            ("SporTV 1", "SporTV"), ("SporTV 2", "SporTV"), ("SporTV 3", "SporTV"),
            ("Cine Classico", "Filmes & Series"), ("Cine Aventura", "Filmes & Series"),
            ("Kids TV", "Infantis"), ("Desenhos", "Infantis"),
            ("News 24h", "Noticias"), ("Canal Rural", "Noticias"),
            ("TV Evangelizar", "Religiosos"), ("Rede Vida", "Religiosos"), ("Canção Nova", "Religiosos"),
            ("Variedades Mix", "Variedades"), ("Musica Popular", "Musica"),
        ],
    },
    "SkyPlus": {
        "count": 86, "drm": "Widevine L3",
        "seeds": [
            ("Telecine Action", "Telecine"), ("Studio Universal", "Filmes & Series"),
            ("SporTV 1", "SporTV"), ("SporTV 2", "SporTV"), ("SporTV 3", "SporTV"),
            ("Premiere 1", "Premiere"), ("Premiere 2", "Premiere"), ("Premiere 3", "Premiere"),
            ("HBO", "Filmes & Series"), ("HBO 2", "Filmes & Series"), ("HBO Family", "Filmes & Series"),
            ("ESPN", "Esportes"), ("ESPN 2", "Esportes"), ("Discovery", "Variedades"),
            ("Discovery Home", "Variedades"), ("TNT", "Filmes & Series"), ("Warner", "Filmes & Series"),
            ("AXN", "Filmes & Series"), ("Space", "Filmes & Series"),
            ("Universal", "Filmes & Series"), ("Sony", "Variedades"), ("FX", "Filmes & Series"),
        ],
    },
    "PrimeVideo": {
        "count": 45, "drm": "Widevine L3 / ClearKey",
        "seeds": [
            ("CazeTV 1", "Esportes"), ("CazeTV 2", "Esportes"), ("CazeTV 3", "Esportes"),
            ("ge TV", "Esportes"), ("CNN Brasil", "Noticias"), ("Bloomberg", "Noticias"),
            ("Prime Originals", "Filmes & Series"), ("Paramount Channel", "Filmes & Series"),
            ("MGM+", "Filmes & Series"), ("Starz", "Filmes & Series"),
        ],
    },
    "PlutoTV": {
        "count": 187, "drm": "Sem DRM",
        "seeds": [
            ("Pluto Filmes Acao", "Filmes & Series"), ("Pluto Filmes Terror", "Filmes & Series"),
            ("Pluto Filmes Comedia", "Filmes & Series"), ("Pluto Series", "Filmes & Series"),
            ("Nick Jr Club", "Infantis"), ("Bob Esponja", "Infantis"), ("Nickelodeon", "Infantis"),
            ("Naruto", "Animes"), ("Yu-Gi-Oh!", "Animes"), ("Anime All Day", "Animes"),
            ("MasterChef", "Realities"), ("Realities 24h", "Realities"),
            ("Pluto News", "Noticias"), ("Cine Sucessos", "Filmes & Series"),
        ],
    },
    "SoulTV": {
        "count": 77, "drm": "Sem DRM",
        "seeds": [
            ("Soul TV MG", "Cultura"), ("Soul TV Minas", "Cultura"),
            ("Soul Filmes", "Filmes & Series"), ("Soul Series", "Filmes & Series"),
            ("Soul Esportes", "Esportes"), ("Soul Cultura", "Cultura"),
            ("Soul Musica", "Musica"), ("Soul Variedades", "Variedades"),
            ("Soul Kids", "Infantis"),
        ],
    },
    "YouTube": {
        "count": 15, "drm": "Sem DRM",
        "seeds": [
            ("CazeTV Ao Vivo", "Esportes"), ("Canal GOAT", "Esportes"), ("SBT News 24h", "Noticias"),
            ("Jovem Pan News", "Noticias"), ("Record News", "Noticias"), ("Dragon Ball Z", "Animes"),
            ("Bluey", "Infantis"), ("Boomerang", "Infantis"), ("MMA 24/7", "Esportes"),
        ],
    },
    "RecordPlus": {
        "count": 10, "drm": "Sem DRM",
        "seeds": [
            ("Record SP", "Abertos"), ("Record Rio", "Abertos"), ("Record Minas", "Abertos"),
            ("Record Brasilia", "Abertos"), ("Record Bahia", "Abertos"), ("Record News", "Noticias"),
            ("Record Curitiba", "Abertos"), ("Record Fortaleza", "Abertos"),
            ("Record Vitoria", "Abertos"), ("Record Campinas", "Abertos"),
        ],
    },
    "BandPlay": {
        "count": 29, "drm": "Sem DRM",
        "seeds": [
            ("Band SP", "Abertos"), ("Band RJ", "Abertos"), ("Band Minas", "Abertos"),
            ("Band RS", "Abertos"), ("Band PR", "Abertos"), ("Band DF", "Abertos"), ("Band BA", "Abertos"),
            ("BandNews TV", "Noticias"), ("BandSports", "Esportes"), ("Terra Viva", "Noticias"),
            ("Radio Band FM", "Radios"), ("Radio BandNews FM", "Radios"), ("Radio Bradesco Esportes", "Radios"),
        ],
    },
    "HBOMax": {
        "count": 40, "drm": "Widevine L3",
        "seeds": [
            ("HBO", "Filmes & Series"), ("HBO 2", "Filmes & Series"), ("HBO Family", "Filmes & Series"),
            ("Max Originals", "Filmes & Series"), ("DC", "Filmes & Series"),
            ("Cartoon Network", "Infantis"), ("Adult Swim", "Variedades"),
        ],
    },
    "DisneyPlus": {
        "count": 35, "drm": "Widevine L3",
        "seeds": [
            ("ESPN", "Esportes"), ("ESPN 2", "Esportes"), ("Disney Channel", "Infantis"),
            ("National Geographic", "Variedades"), ("Star", "Filmes & Series"),
            ("Marvel", "Filmes & Series"), ("Pixar", "Infantis"),
        ],
    },
    "ParamountPlus": {
        "count": 30, "drm": "Widevine L3",
        "seeds": [
            ("CBS", "Variedades"), ("Nickelodeon", "Infantis"), ("MTV", "Musica"),
            ("Paramount Pictures", "Filmes & Series"), ("Comedy Central", "Variedades"),
            ("Smithsonian", "Variedades"),
        ],
    },
    "ClaroTV": {
        "count": 120, "drm": "Widevine L3",
        "seeds": [
            ("Globo RJ", "Globos Regionais"), ("Globo SP", "Globos Regionais"),
            ("Globo MG", "Globos Regionais"), ("Globo DF", "Globos Regionais"),
            ("SporTV 1", "SporTV"), ("SporTV 2", "SporTV"), ("SporTV 3", "SporTV"),
            ("Premiere 1", "Premiere"), ("Premiere 2", "Premiere"), ("Premiere 3", "Premiere"),
            ("Telecine Action", "Telecine"), ("Telecine Premium", "Telecine"),
            ("Telecine Pipoca", "Telecine"), ("Telecine Touch", "Telecine"),
            ("Discovery Channel", "Variedades"), ("Discovery Home", "Variedades"),
            ("History", "Variedades"), ("Fox Channel", "Filmes & Series"),
            ("Fox Sports", "Esportes"), ("ESPN", "Esportes"), ("ESPN 2", "Esportes"),
            ("TNT", "Filmes & Series"), ("Warner", "Filmes & Series"),
            ("AXN", "Filmes & Series"), ("Space", "Filmes & Series"),
            ("Universal", "Filmes & Series"), ("Sony", "Variedades"),
            ("Cartoon Network", "Infantis"), ("Nickelodeon", "Infantis"),
            ("Discovery Kids", "Infantis"), ("Gloob", "Infantis"),
            ("Multishow", "Variedades"), ("GNT", "Variedades"), ("Viva", "Variedades"),
            ("GloboNews", "Noticias"), ("Record News", "Noticias"),
        ],
    },
}

# Mapa id -> nome de exibição
_PROVIDER_NAMES = {p["id"]: p["name"] for p in PROVIDERS}
_PROVIDER_DRM = {p["id"]: p.get("drm", "Sem DRM") for p in PROVIDERS}


def _variants_for(pid, name):
    """Variantes realistas por provedor/canal."""
    if pid == "globoplay" and name.startswith("SporTV 4"):
        return ["4K_PT", "HD_PT"]
    if pid == "globoplay" and name.startswith("Premiere"):
        return ["FHD_PT", "HD_PT"]
    if pid in ("globoplay", "skyplus", "primevideo", "hbomax", "disneyplus", "paramountplus", "clarotv"):
        return ["HD_PT", "SD_PT", "HD_EN", "SD_EN"]
    return ["HD_PT", "SD_PT"]


def _gen_channels():
    chans = []
    cid = 1000
    for pid, cfg in _PROVIDER_CATALOG.items():
        prov_name = _PROVIDER_NAMES.get(pid, pid)
        drm = cfg["drm"]
        seeds = cfg["seeds"]
        target = cfg["count"]
        produced = 0
        i = 0
        while produced < target:
            if i < len(seeds):
                base_name, cat = seeds[i]
            else:
                base_name, cat = seeds[(i - len(seeds)) % len(seeds)]
                base_name = f"{base_name} {((i - len(seeds)) // len(seeds)) + 2}"
            for v in _variants_for(pid, base_name):
                quality = v.split("_")[0]
                audio = v.split("_")[1] if "_" in v else "PT"
                chans.append({
                    "id": cid,
                    "logo": f"/static/logo.svg?c={cid}",
                    "name": base_name,
                    "cid": f"CID-{_hash(base_name + v)[:8].upper()}",
                    "category": cat,
                    "quality": quality,
                    "audio": audio,
                    "provider": prov_name,
                    "drm": drm,
                    "kid": f"{_hash(base_name + v + 'kid')[:8].upper()}:{_hash(base_name + v + 'key')[:12].upper()}",
                })
                cid += 1
                produced += 1
                if produced >= target:
                    break
            i += 1
    return chans


CHANNELS = _gen_channels()

# (YOUTUBE_CHANNELS agora é carregado do arquivo de persistência panel_state.json)

CFG_FILES = [
    {"filename": "recordplus_teste.cfg", "size": "132KB", "provider": "RecordPlus", "client": "teste", "quality": "--", "audio": "--", "ts": "2026-10-26 10:51:52"},
    {"filename": "globo_teste_HD.cfg", "size": "124KB", "provider": "GloboPlay", "client": "teste", "quality": "HD", "audio": "PT", "ts": "2026-10-26 10:51:52"},
    {"filename": "globo_teste_FHD.cfg", "size": "126KB", "provider": "GloboPlay", "client": "teste", "quality": "FHD", "audio": "PT", "ts": "2026-10-26 10:51:52"},
    {"filename": "sky_teste_SD_EN.cfg", "size": "702KB", "provider": "SkyPlus", "client": "teste", "quality": "SD", "audio": "EN", "ts": "2026-10-26 10:51:52"},
    {"filename": "sky_teste_SD_PT.cfg", "size": "699KB", "provider": "SkyPlus", "client": "teste", "quality": "SD", "audio": "PT", "ts": "2026-10-26 10:51:52"},
]

DEPLOY_LOGS = [
    {"ts": "10:43:20", "level": "INFO", "msg": "Iniciando captura (simulada) para GloboPlay_FHD..."},
    {"ts": "10:43:22", "level": "INFO", "msg": "Canais processados (sintetico): 39"},
    {"ts": "10:43:23", "level": "INFO", "msg": "Canais com DRM (sintetico): 12"},
    {"ts": "10:43:24", "level": "INFO", "msg": "Canais reportados com chaves (sintetico): 10"},
    {"ts": "10:43:26", "level": "INFO", "msg": "Gerando globo_cliente_vps_FHD.cfg (132KB)"},
    {"ts": "10:43:27", "level": "INFO", "msg": "Deploy SSH (simulado) em VPS 'teste'..."},
    {"ts": "10:43:28", "level": "INFO", "msg": "Todos os CFGs foram gerados com sucesso"},
    {"ts": "10:43:28", "level": "INFO", "msg": "Processo de captura finalizado. Finalizado com codigo 0"},
]

# ---------------------------------------------------------------------------
# ESTADO DO SIMULADOR (thread em background)
# ---------------------------------------------------------------------------

_rules = [
    {"id": "RULE-001", "name": "Compartilhamento de token (multi-IP)", "severity": "CRITICO", "desc": "Mesmo token autenticado em 3+ IPs simultaneos em janela curta."},
    {"id": "RULE-002", "name": "Anomalia de sessao (velocidade geografica)", "severity": "ALTO", "desc": "Sessao aparece em cidades distintas em intervalo impossivel."},
    {"id": "RULE-003", "name": "Redistribuicao (user-agent de ferramenta)", "severity": "CRITICO", "desc": "Cliente usando ffmpeg/curl/yt-dlp = indicio de re-streaming."},
    {"id": "RULE-004", "name": "Credencial exposta na URL", "severity": "ALTO", "desc": "Token/senha visivel em URL de playlist compartilhada."},
    {"id": "RULE-005", "name": "Excesso de sessoes por conta", "severity": "MEDIO", "desc": "Conta excede limite de telas simultaneas configurado."},
    {"id": "RULE-006", "name": "Brute force / tentativa de login", "severity": "ALTO", "desc": "Multiplas tentativas de login com senha incorreta em janela curta."},
    {"id": "RULE-007", "name": "Token capturado / exfiltrado", "severity": "CRITICO", "desc": "Token de sessao do assinante foi capturado e armazenado em vault (simulacao de ataque)."},
    {"id": "RULE-008", "name": "Rotacao de token/link", "severity": "ALTO", "desc": "Provedor trocou tokens/links e o painel re-sincronizou automaticamente (simulado)."},
]

_CITIES = ["Sao Paulo", "Rio de Janeiro", "Curitiba", "Belo Horizonte", "Manaus", "Lisboa", "Miami", "Frankfurt"]

_state = {
    "running": True,
    "sessions": [],
    "alerts": [],
    "detections": 0,
    "iofs": 0,
    # Vault dinâmico: tokens "capturados" pelo módulo DEFENSE durante a demo.
    # Cada login bem-sucedido gera um token real e o DEFENSE o captura aqui,
    # simulando o comportamento de um sistema pirata (sem nenhum dado real).
    "token_vault": [],
}

_alert_templates = [
    ("RULE-001", "Compartilhamento de token", "Token compartilhado entre 4 IPs em 3 min", "CRITICO"),
    ("RULE-003", "Redistribuicao", "user-agent ffmpeg detectado puxando stream HLS", "CRITICO"),
    ("RULE-002", "Anomalia de sessao", "Login em Sao Paulo e Miami em 6 min", "ALTO"),
    ("RULE-004", "Credencial exposta", "Senha visivel em URL de playlist M3U", "ALTO"),
    ("RULE-005", "Excesso de sessoes", "Conta com 7 telas simultaneas (limite 3)", "MEDIO"),
]


# ---------------------------------------------------------------------------
# AUTO-FLOW (PILOTO AUTOMÁTICO) — o sistema faz tudo sozinho após o login
# ---------------------------------------------------------------------------
# Simula o comportamento real de um sistema pirata: depois que o operador
# insere usuário+senha do provedor, o sistema AUTOMATICAMENTE:
#   conecta -> puxa playlist -> cataloga canais -> detecta DRM -> gera CFG -> deploy
# Tudo com dados sintéticos, para o cliente ver a sequência completa do ataque.
_autoflow = {
    "running": False,
    "provider": None,
    "username": None,
    "steps": [],
    "log": [],
    "finished": False,
}

_AUTOFLOW_STEPS = [
    ("connect", "Conectando ao provedor (autenticação)"),
    ("playlist", "Extraindo playlist M3U (get.php)"),
    ("catalog", "Catalogando canais (nome, qualidade, áudio)"),
    ("drm", "Detectando DRM e chaves KID:KEY"),
    ("cfg", "Gerando arquivos CFG por cliente"),
    ("deploy", "Deploy na VPS de distribuição"),
    ("done", "Fluxo concluído — tudo pronto"),
]


def _autoflow_run(provider, username):
    """Executa o fluxo automático em background (thread)."""
    _autoflow["running"] = True
    _autoflow["finished"] = False
    _autoflow["provider"] = provider
    _autoflow["username"] = username
    _autoflow["steps"] = []
    _autoflow["log"] = []

    def log(msg, level="INFO"):
        _autoflow["log"].insert(0, {
            "ts": datetime.datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "msg": msg,
        })
        if len(_autoflow["log"]) > 200:
            _autoflow["log"] = _autoflow["log"][:200]

    try:
        for i, (key, label) in enumerate(_AUTOFLOW_STEPS):
            if not _autoflow["running"]:
                break
            _autoflow["steps"].append({"key": key, "label": label, "status": "running"})
            log(f"[{i+1}/{len(_AUTOFLOW_STEPS)}] {label}...", "INFO")
            time.sleep(1.2)  # dá tempo de ver cada etapa (simulação)

            # ---- resultados sintéticos por etapa ----
            if key == "connect":
                log(f"Token de sessão emitido: {hashlib.sha256((username+str(time.time())).encode()).hexdigest()[:20]}", "OK")
            elif key == "playlist":
                log("Playlist recebida: 944 canais + 320 filmes + 890 séries (sintéticos)", "OK")
            elif key == "catalog":
                log("Canais catalogados com CID, qualidade (4K/FHD/HD/SD) e áudio PT/EN", "OK")
            elif key == "drm":
                log("12 canais DRM Widevine L3 mapeados — KID:KEY sintéticos gerados", "OK")
                _add_alert(
                    "RULE-007", "Token capturado / exfiltrado",
                    f"Auto-flow capturou tokens e chaves (simulado) para '{username}' no provedor {provider}.",
                    "CRITICO", account=username,
                )
            elif key == "cfg":
                log("CFGs gerados: globo_FHD.cfg, sky_HD_EN.cfg, recordplus.cfg (sintéticos)", "OK")
            elif key == "deploy":
                log("Deploy SSH (simulado) na VPS 'teste' — status: active", "OK")
            elif key == "done":
                log("Fluxo completo. Sistema operando em modo automático.", "OK")

            _autoflow["steps"][-1]["status"] = "done"

        _autoflow["finished"] = True
        _autoflow["running"] = False
    except Exception as e:
        log(f"Erro no auto-flow: {e}", "ERR")
        _autoflow["running"] = False
        _autoflow["finished"] = True


# ---------------------------------------------------------------------------
# MONITOR DE ROTAÇÃO DE TOKENS (re-sincronização automática)
# ---------------------------------------------------------------------------
# Fica observando o DEFENSE-CORE. Quando o provedor "gira" os tokens/links,
# o painel detecta a mudança, dispara alerta e RE-SINCRONIZA sozinho.
_token_sync = {
    "last_revision": 0,
    "revisions_detected": 0,
    "status": "monitorando",
    "last_change": None,
    "history": [],
}


def _token_sync_loop():
    global _token_sync
    while True:
        time.sleep(4)
        try:
            r = requests.get(f"{CORE_URL}/api/live_tokens", timeout=3)
            if r.status_code != 200:
                continue
            data = r.json()
            rev = data.get("revision", 0)
            if _token_sync["last_revision"] == 0:
                _token_sync["last_revision"] = rev
                continue
            if rev > _token_sync["last_revision"]:
                old = _token_sync["last_revision"]
                _token_sync["last_revision"] = rev
                _token_sync["revisions_detected"] += 1
                _token_sync["last_change"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                _token_sync["status"] = "rotacao_detectada"
                _token_sync["history"].insert(0, {
                    "from_rev": old,
                    "to_rev": rev,
                    "ts": _token_sync["last_change"],
                })
                if len(_token_sync["history"]) > 50:
                    _token_sync["history"] = _token_sync["history"][:50]
                _add_alert(
                    "RULE-008", "Rotacao de token/link/chave detectada",
                    f"Provedor rotacionou tokens, links e KID:KEY (revisao {old} -> {rev}). "
                    "O painel re-sincronizou automaticamente e re-emitiu as chaves DRM (simulado).",
                    "ALTO",
                )
                # volta a monitorar depois de registrar
                _token_sync["status"] = "monitorando"
        except Exception:
            pass


def _seed_sessions():
    if _state["sessions"]:
        return
    for i in range(30):
        _state["sessions"].append({
            "id": uuid.uuid4().hex[:8],
            "provider": random.choice([p["name"] for p in PROVIDERS]),
            "account": _mask_email(f"assinante.{random.randint(1,999):03d}@provedor.com"),
            "ip": f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "city": random.choice(_CITIES),
            "ua": random.choice(["VLC/3.0.18", "Lavf/60.16.100", "ffmpeg/6.1", "curl/8.5.0", "SmartTV", "iOS/17", "Android/14"]),
            "ts": datetime.datetime.utcnow().strftime("%H:%M:%S"),
        })


def _simulator_loop():
    _seed_sessions()
    counter = 0
    while True:
        time.sleep(2.5)
        if not _state["running"]:
            continue
        counter += 1
        # atualiza sessões
        if len(_state["sessions"]) < 60 and counter % 2 == 0:
            _state["sessions"].append({
                "id": uuid.uuid4().hex[:8],
                "provider": random.choice([p["name"] for p in PROVIDERS]),
                "account": _mask_email(f"assinante.{random.randint(1,999):03d}@provedor.com"),
                "ip": f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "city": random.choice(_CITIES),
                "ua": random.choice(["VLC/3.0.18", "Lavf/60.16.100", "ffmpeg/6.1", "curl/8.5.0", "SmartTV", "iOS/17", "Android/14"]),
                "ts": datetime.datetime.utcnow().strftime("%H:%M:%S"),
            })
        # gera alerta sintético
        if counter % 3 == 0 and len(_state["alerts"]) < 60:
            rule_id, rule_name, detail, sev = random.choice(_alert_templates)
            acct = _mask_email(f"conta.{random.randint(10,999)}@provedor.com")
            ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            city = random.choice(_CITIES)
            _state["alerts"].insert(0, {
                "id": uuid.uuid4().hex[:8],
                "rule": rule_id,
                "rule_name": rule_name,
                "severity": sev,
                "detail": detail,
                "account": acct,
                "ip": ip,
                "city": city,
                "ts": datetime.datetime.utcnow().strftime("%H:%M:%S"),
            })
            _state["detections"] += 1
            if sev in ("CRITICO", "ALTO"):
                _state["iofs"] += 1


threading.Thread(target=_simulator_loop, daemon=True).start()
threading.Thread(target=_token_sync_loop, daemon=True).start()

# ---------------------------------------------------------------------------
# ROTAS
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/dashboard")
def dashboard():
    # Fonte da verdade: DEFENSE-CORE (banco persistido de provedores/contas).
    # O painel conecta no servidor simulado, extrai e salva lá — e a tela
    # passa a refletir o que está no banco (não valores fixos).
    providers = []
    accounts = []
    core = core_status()
    try:
        r = requests.get(f"{CORE_URL}/api/providers", timeout=3)
        if r.status_code == 200:
            providers = r.json().get("providers", [])
    except Exception:
        pass
    try:
        r = requests.get(f"{CORE_URL}/api/auth/accounts", timeout=3)
        if r.status_code == 200:
            accounts = r.json().get("accounts", [])
    except Exception:
        pass

    # "Saúde & Validade dos Tokens" derivada das contas reais cadastradas no banco.
    token_health = []
    for a in accounts:
        st = a.get("status", "active")
        status = "VALIDO"
        rem = "Válido"
        if st == "expired":
            status = "EXPIRADO"
            rem = "Expirado"
        elif st == "blocked":
            status = "BLOQUEADO"
            rem = "Bloqueado"
        token_health.append({
            "provider": a.get("provider", "Provedor"),
            "account": _mask_email(a.get("username", "conta") + "@provedor.com"),
            "status": status,
            "remaining_time": rem,
            "expiration": a.get("expiry", "--"),
            "abuse": "BAIXO",
        })

    stats = {
        "sessions": len(_state["sessions"]),
        "detections": _state["detections"],
        "alerts": len(_state["alerts"]),
        "iofs": _state["iofs"],
        "providers": len(providers) or len(PROVIDERS),
        "accounts": len(accounts),
        "vps": len(CONNECTED_SERVERS),
        "youtube": len(YOUTUBE_CHANNELS),
        "channels": len(CHANNELS),
    }

    return jsonify({
        "drm_core": DRM_CORE,
        "core": core,
        "core_url": CORE_URL,
        "providers": providers or PROVIDERS,
        "accounts": accounts,
        "token_health": token_health or TOKEN_HEALTH,
        "connected_servers": CONNECTED_SERVERS,
        "youtube": YOUTUBE_CHANNELS,
        "stats": stats,
    })


@app.route("/api/ping")
def api_ping():
    """Healthcheck simples para a VPS / balanceador."""
    return jsonify({"ok": True, "service": "anti-piracy-painel", "core": core_status()})


@app.route("/api/core")
def api_core():
    """Status detalhado do servidor fake + endpoints de demonstração."""
    core = core_status()
    return jsonify({
        "core": core,
        "core_url": CORE_URL,
        "endpoints": {
            "health": f"{CORE_URL}/health",
            "stream_ts": f"{CORE_URL}/stream/canal-teste.ts",
            "stream_hls": f"{CORE_URL}/stream/canal-teste.m3u8",
            "licenca_drm_simulada": f"{CORE_URL}/license",
            "validar_token": f"{CORE_URL}/token/validate?token=fake123",
            "template_cfg": f"{CORE_URL}/api/cfg/template",
        },
        "aviso": "Todos os endpoints sao 100% simulados (dados fabricados localmente).",
    })


@app.route("/api/servers")
def api_servers():
    """Topologia multi-servidor: servidores de provedores conhecidos pelo painel."""
    servers = {}
    for p in _get_providers():
        url = (p.get("server") or CORE_URL).strip()
        servers.setdefault(url, {"url": url, "providers": [], "online": None})
        servers[url]["providers"].append(p["name"])
    result = []
    for url, info in servers.items():
        online = None
        try:
            r = requests.get(f"{url}/health", timeout=2)
            online = r.status_code == 200
        except Exception:
            online = False
        result.append({
            "url": url,
            "providers": info["providers"],
            "total_providers": len(info["providers"]),
            "online": online,
        })
    return jsonify({
        "servers": result,
        "total": len(result),
        "core_principal": CORE_URL,
        "aviso": "Cada servidor simula um ou mais provedores. Tudo sintético.",
    })


@app.route("/api/streams")
def api_streams_proxy():
    """Lista os streams sintéticos reproduzíveis (proxy para o DEFENSE-CORE)."""
    try:
        r = requests.get(f"{CORE_URL}/api/streams", timeout=3)
        return jsonify(r.json())
    except Exception:
        return jsonify({
            "streams": [],
            "error": "DEFENSE-CORE offline. Inicie o servidor interno.",
        }), 503


@app.route("/api/tokens")
def tokens():
    items = []
    for th in TOKEN_HEALTH:
        items.append({
            "provider": th["provider"],
            "account": th["account"],
            "status": th["status"],
            "remaining_time": th["remaining_time"],
            "expiration": th["expiration"],
            "abuse": th["abuse"],
            "distinct_ips": random.randint(1, 9),
            "token_id": _hash(th["provider"] + th["account"])[:12].upper(),
        })
    # Tokens capturados dinamicamente durante a demo (fluxo de captura real)
    for cap in _state["token_vault"]:
        items.insert(0, {
            "provider": cap["provider"],
            "account": cap["account"],
            "status": "CAPTURADO",
            "remaining_time": "--",
            "expiration": "--",
            "abuse": "CAPTURA",
            "distinct_ips": random.randint(1, 3),
            "token_id": cap["token_id"],
            "captured": True,
            "captured_at": cap["captured_at"],
        })
    return jsonify({"tokens": items})


@app.route("/api/vault")
def vault():
    """Cofre de tokens capturados durante a simulação."""
    return jsonify({
        "vault": _state["token_vault"],
        "total": len(_state["token_vault"]),
        "aviso": "Tokens 100% sintéticos, capturados em ambiente simulado. Nenhuma credencial real.",
    })


@app.route("/api/channels")
def channels():
    return jsonify({
        "total": len(CHANNELS),
        "categories": CATEGORIES,
        "channels": CHANNELS,
    })


@app.route("/api/alerts")
def alerts():
    return jsonify({
        "alerts": _state["alerts"],
        "rules": _rules,
    })


@app.route("/api/vps")
def vps():
    return jsonify({
        "servers": CONNECTED_SERVERS,
        "columns": ["VPS_Server", "VPS_IP", "SSH_Port", "Web_Path", "Client_Token", "Status", "Deploy_Actions"],
    })


@app.route("/api/cfg")
def cfg():
    return jsonify({
        "files": CFG_FILES,
        "providers": [p["name"] for p in PROVIDERS],
        "clients": ["Todos os clientes ativos", "teste"],
        "stats": {
            "GloboPlay_FHD": {"channels": 39, "drm_channels": 12, "with_keys": 10},
            "GloboPlay_HD": {"channels": 39, "drm_channels": 12, "with_keys": 10},
            "RecordPlus": {"channels": 38},
        },
    })


@app.route("/api/cfg/generate", methods=["POST"])
def cfg_generate():
    """Gera arquivos .cfg REAIS no disco, mas com conteúdo 100% fabricado."""
    data = request.get_json(silent=True) or {}
    provider = data.get("provider", "SkyPlus")
    client = data.get("client", "teste")
    quality = data.get("quality", "HD_PT")

    out_dir = os.path.join(os.path.dirname(__file__), "output", "cfgs")
    os.makedirs(out_dir, exist_ok=True)

    # Conteúdo fabricado (nunca credencial real, nunca chave real)
    header = (
        "# DEFENSE-LAB CFG (SIMULADO)\n"
        "# Este arquivo NAO funciona em nenhum painel real.\n"
        "# Dados 100% fabricados para demonstracao defensiva.\n"
        f"# provider={provider} | client={client} | quality={quality}\n"
        f"# gerado_em={datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )
    channels = []
    for ch in random.sample(CHANNELS, min(6, len(CHANNELS))):
        channels.append(
            f"#EXTINF:-1,{ch['name']} ({ch['quality']}) [SIMULADO]\n"
            f"{CORE_URL}/stream/{ch['name'].replace(' ', '-')}.ts\n"
        )

    fname = f"{provider.lower()}_{client}_{quality}.cfg".replace(" ", "_").replace("/", "_")
    fpath = os.path.join(out_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(channels) + "\n")

    size_kb = max(1, round(os.path.getsize(fpath) / 1024, 2))
    return jsonify({
        "ok": True,
        "filename": fname,
        "path": fpath,
        "size": f"{size_kb}KB",
        "channels": len(channels),
        "aviso": "Arquivo SIMULADO. Nao funciona em painel real.",
    })


@app.route("/api/cfg/download/<path:fname>")
def cfg_download(fname):
    """Faz download do arquivo CFG simulado gerado."""
    out_dir = os.path.join(os.path.dirname(__file__), "output", "cfgs")
    fpath = os.path.join(out_dir, os.path.basename(fname))
    if not os.path.exists(fpath):
        return jsonify({"error": "arquivo nao encontrado"}), 404
    from flask import send_file
    return send_file(fpath, as_attachment=True, download_name=os.path.basename(fname))


@app.route("/api/deploy")
def deploy():
    return jsonify({
        "logs": DEPLOY_LOGS,
        "os": "Windows",
        "directory": "C:\\Users\\Teste 2022\\Desktop\\PROJETOS EM CONSTRUCAO\\DEFENSE-LAB\\output\\cfgs\\",
        "core": core_status(),
    })


@app.route("/api/youtube")
def youtube():
    return jsonify({
        "channels": YOUTUBE_CHANNELS,
        "total": len(YOUTUBE_CHANNELS),
        "compat": ["XUI One", "Xtream UI", "VLC"],
    })


# ---------------------------------------------------------------------------
# CRUD de VPS (nova / editar / excluir / deploy / baixar lista XUI)
# ---------------------------------------------------------------------------

@app.route("/api/vps", methods=["POST"])
def vps_create():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Nome da VPS é obrigatório."}), 400
    srv = {
        "id": "vps-" + uuid.uuid4().hex[:8],
        "name": name,
        "ip": data.get("ip") or f"{random.randint(1,223)}.***.***.***",
        "real_ip": data.get("real_ip") or f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        "status": data.get("status") or "active",
        "ssh_port": int(data.get("ssh_port") or 22),
        "web_path": data.get("web_path") or "/var/www/html/directv/",
        "token": data.get("token") or "Teste",
    }
    CONNECTED_SERVERS.append(srv)
    _save_panel_state(CONNECTED_SERVERS, YOUTUBE_CHANNELS)
    _add_alert(
        "RULE-003", "Redistribuicao",
        f"Nova VPS '{name}' cadastrada para distribuicao (simulado).",
        "ALTO",
    )
    return jsonify({"ok": True, "server": srv, "message": f"VPS '{name}' cadastrada."})


@app.route("/api/vps/<vid>", methods=["PUT"])
def vps_update(vid):
    data = request.get_json(silent=True) or {}
    srv = next((s for s in CONNECTED_SERVERS if s["id"] == vid), None)
    if not srv:
        return jsonify({"ok": False, "error": "VPS não encontrada."}), 404
    for f in ["name", "ip", "real_ip", "status", "web_path", "token"]:
        if f in data and data[f] not in (None, ""):
            srv[f] = data[f]
    if "ssh_port" in data and data["ssh_port"]:
        srv["ssh_port"] = int(data["ssh_port"])
    _save_panel_state(CONNECTED_SERVERS, YOUTUBE_CHANNELS)
    return jsonify({"ok": True, "server": srv, "message": "VPS atualizada."})


@app.route("/api/vps/<vid>", methods=["DELETE"])
def vps_delete(vid):
    global CONNECTED_SERVERS
    before = len(CONNECTED_SERVERS)
    CONNECTED_SERVERS = [s for s in CONNECTED_SERVERS if s["id"] != vid]
    if len(CONNECTED_SERVERS) == before:
        return jsonify({"ok": False, "error": "VPS não encontrada."}), 404
    _save_panel_state(CONNECTED_SERVERS, YOUTUBE_CHANNELS)
    return jsonify({"ok": True, "message": "VPS excluída."})


@app.route("/api/vps/<vid>/deploy", methods=["POST"])
def vps_deploy(vid):
    srv = next((s for s in CONNECTED_SERVERS if s["id"] == vid), None)
    if not srv:
        return jsonify({"ok": False, "error": "VPS não encontrada."}), 404
    log = [
        {"ts": datetime.datetime.now().strftime("%H:%M:%S"), "level": "INFO",
         "msg": f"Conectando via SSH (simulado) em {srv['name']} ({srv['ip']}):{srv['ssh_port']}..."},
        {"ts": datetime.datetime.now().strftime("%H:%M:%S"), "level": "INFO",
         "msg": f"Instalando painel em {srv['web_path']} (simulado)..."},
        {"ts": datetime.datetime.now().strftime("%H:%M:%S"), "level": "INFO",
         "msg": "Deploy concluído. Status: active."},
    ]
    return jsonify({"ok": True, "server": srv["name"], "log": log, "message": "Deploy concluído (simulado)."})


@app.route("/api/vps/xui-list")
def vps_xui_list():
    """Gera a 'Lista XUI' (arquivo simulado) para download."""
    lines = ["# LISTA XUI (SIMULADA) - DEFENSE-LAB", "# Este arquivo nao funciona em painel real.", ""]
    for s in CONNECTED_SERVERS:
        lines.append(f"# VPS: {s['name']} | IP: {s['ip']} | SSH: {s['ssh_port']} | {s['web_path']}")
        lines.append(f"http://{s.get('real_ip', '198.51.100.10')}:{s['ssh_port']}/{s['web_path'].strip('/')}/")
        lines.append("")
    from flask import Response
    return Response(
        "\n".join(lines),
        mimetype="text/plain",
        headers={"Content-Disposition": 'attachment; filename="lista_xui_simulada.txt"'},
    )


# ---------------------------------------------------------------------------
# CRUD de Canais YouTube (testar / XUI link / pesquisar / novo / lives / M3U)
# ---------------------------------------------------------------------------

@app.route("/api/youtube", methods=["POST"])
def youtube_create():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Nome do canal é obrigatório."}), 400
    ch = {
        "id": "yt-" + uuid.uuid4().hex[:8],
        "name": name,
        "handle": data.get("handle") or ("@" + name.replace(" ", "").lower()),
        "category": data.get("category") or "Variedades",
        "live": data.get("live") or "OFFLINE",
        "broadcast": data.get("broadcast") or "Aguardando transmissao",
    }
    YOUTUBE_CHANNELS.append(ch)
    _save_panel_state(CONNECTED_SERVERS, YOUTUBE_CHANNELS)
    return jsonify({"ok": True, "channel": ch, "message": f"Canal '{name}' cadastrado."})


@app.route("/api/youtube/<cid>", methods=["DELETE"])
def youtube_delete(cid):
    global YOUTUBE_CHANNELS
    before = len(YOUTUBE_CHANNELS)
    YOUTUBE_CHANNELS = [c for c in YOUTUBE_CHANNELS if c["id"] != cid]
    if len(YOUTUBE_CHANNELS) == before:
        return jsonify({"ok": False, "error": "Canal não encontrado."}), 404
    _save_panel_state(CONNECTED_SERVERS, YOUTUBE_CHANNELS)
    return jsonify({"ok": True, "message": "Canal excluído."})


@app.route("/api/youtube/<cid>/test", methods=["POST"])
def youtube_test(cid):
    ch = next((c for c in YOUTUBE_CHANNELS if c["id"] == cid), None)
    if not ch:
        return jsonify({"ok": False, "error": "Canal não encontrado."}), 404
    status = "ONLINE" if ch.get("live") == "ONLINE" else "OFFLINE"
    return jsonify({
        "ok": True,
        "channel": ch["name"],
        "live": status,
        "stream_url": f"{CORE_URL}/stream/{ch['name'].replace(' ', '-')}.m3u8" if status == "ONLINE" else None,
        "message": f"Canal '{ch['name']}' testado: {status} (simulado).",
    })


@app.route("/api/youtube/<cid>/xui-link", methods=["POST"])
def youtube_xui_link(cid):
    ch = next((c for c in YOUTUBE_CHANNELS if c["id"] == cid), None)
    if not ch:
        return jsonify({"ok": False, "error": "Canal não encontrado."}), 404
    link = f"{CORE_URL}/stream/{ch['name'].replace(' ', '-')}.m3u8"
    return jsonify({"ok": True, "link": link, "message": "Link XUI gerado (simulado)."})


@app.route("/api/youtube/search")
def youtube_search():
    q = (request.args.get("q") or "").strip().lower()
    results = [c for c in YOUTUBE_CHANNELS if (not q) or q in c["name"].lower() or q in c["handle"].lower()]
    return jsonify({"ok": True, "results": results, "total": len(results)})


@app.route("/api/youtube/verify-lives", methods=["POST"])
def youtube_verify_lives():
    """Alterna/atualiza o status das lives (simulação)."""
    for c in YOUTUBE_CHANNELS:
        if c.get("category") == "Noticias":
            c["live"] = "ONLINE"
            c["broadcast"] = "Agora no ar (simulado)"
        elif c.get("live") == "ONLINE":
            c["live"] = "OFFLINE"
    _save_panel_state(CONNECTED_SERVERS, YOUTUBE_CHANNELS)
    return jsonify({"ok": True, "channels": YOUTUBE_CHANNELS, "message": "Lives verificadas (simulado)."})


@app.route("/api/youtube/m3u")
def youtube_m3u():
    """Gera a playlist M3U dos canais YouTube (simulada)."""
    lines = ["#EXTM3U", "# Playlist YouTube (SIMULADA) - DEFENSE-LAB", ""]
    for c in YOUTUBE_CHANNELS:
        lines.append(f"#EXTINF:-1,{c['name']} ({c['handle']})")
        lines.append(_real_stream_url(c['name'], "youtube"))
        lines.append("")
    from flask import Response
    return Response(
        "\n".join(lines),
        mimetype="audio/x-mpegurl",
        headers={"Content-Disposition": 'attachment; filename="youtube_simulado.m3u"'},
    )


@app.route("/api/channels/m3u")
def channels_m3u():
    """Gera a playlist M3U dos canais catalogados (filtros opcionais)."""
    q = (request.args.get("q") or "").lower()
    prov = request.args.get("provider") or ""
    qual = request.args.get("quality") or ""
    cat = request.args.get("category") or ""
    chans = CHANNELS
    if q:
        chans = [c for c in chans if q in c["name"].lower() or q in c["cid"].lower()]
    if prov:
        chans = [c for c in chans if c["provider"] == prov]
    if qual:
        chans = [c for c in chans if c["quality"] == qual]
    if cat:
        chans = [c for c in chans if c["category"] == cat]
    chans = chans[:200]
    lines = ["#EXTM3U", f"# Playlist Canais & DRM (SIMULADA) - {len(chans)} canais", ""]
    for c in chans:
        lines.append(f'#EXTINF:-1,{c["name"]} ({c["quality"]}) [{c["drm"]}]')
        lines.append(_real_stream_url(c["name"], c.get("provider", "")))
        lines.append("")
    from flask import Response
    return Response(
        "\n".join(lines),
        mimetype="audio/x-mpegurl",
        headers={"Content-Disposition": 'attachment; filename="canais_drm_simulado.m3u"'},
    )


@app.route("/api/vault/<token_id>/change", methods=["POST"])
def vault_change_account(token_id):
    """Troca a conta associada a um token capturado no Vault."""
    data = request.get_json(silent=True) or {}
    new_account = (data.get("account") or "").strip()
    if not new_account:
        return jsonify({"ok": False, "error": "Informe a nova conta."}), 400
    tok = next((t for t in _state["token_vault"] if t["token_id"] == token_id or t["token"] == token_id), None)
    if not tok:
        return jsonify({"ok": False, "error": "Token não encontrado no Vault."}), 404
    tok["account"] = new_account
    tok["changed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({"ok": True, "message": f"Conta do token trocada para '{new_account}'."})


@app.route("/api/trava_map")
def trava_map():
    modules = [
        {
            "module": "Dashboard / DRM Core",
            "attacker_view": "Ve tokens validos, contas ativas e servidores conectados em tempo real.",
            "ioc": "Concentracao de contas em um unico painel = credencial roubada centralizada.",
            "defense": "Token binding por dispositivo + limite de sessoes + rotacao curta de token (short-lived).",
            "severity": "CRITICO",
        },
        {
            "module": "Vault de Tokens",
            "attacker_view": "Armazena credenciais de assinantes e monitora validade.",
            "ioc": "Um token sendo usado em N IPs distintos.",
            "defense": "Detectar multi-IP por token e revogar automaticamente (regra RULE-001).",
            "severity": "CRITICO",
        },
        {
            "module": "Contas & Login",
            "attacker_view": "Gestao de contas capturadas.",
            "ioc": "Login de localizacoes distantes em janela curta.",
            "defense": "Analise de velocidade geografica + device fingerprint (RULE-002).",
            "severity": "ALTO",
        },
        {
            "module": "Canais & DRM (Widevine L3)",
            "attacker_view": "Catalogo com KID:KEY por canal.",
            "ioc": "Exposicao de KID/KEY em interface ou arquivo.",
            "defense": "Nunca persistir chaves no cliente; servir via licenca efemera; marcar com watermark.",
            "severity": "CRITICO",
        },
        {
            "module": "Minhas VPS / Deploy",
            "attacker_view": "Gerenciamento remoto de servidores de distribuicao.",
            "ioc": "Acesso SSH automatizado para deploy em massa.",
            "defense": "Restringir SSH por IP/VPN + chaves + audit log (RULE-003).",
            "severity": "ALTO",
        },
        {
            "module": "Gerador de CFG",
            "attacker_view": "Gera arquivos prontos para XUI com canais classificados.",
            "ioc": "Arquivos .cfg com credenciais embutidas circulando.",
            "defense": "Credenciais nunca embutidas em texto puro; usar referencia/rotacao.",
            "severity": "CRITICO",
        },
        {
            "module": "Canais YouTube / HLS perpetuo",
            "attacker_view": "Retransmissao de lives para IPTV.",
            "ioc": "User-agent ffmpeg/curl puxando HLS (re-streaming).",
            "defense": "Detectar user-agent de ferramenta + fingerprint de stream (RULE-003/005).",
            "severity": "ALTO",
        },
        {
            "module": "Deploy & Logs",
            "attacker_view": "Console de automacao em ambiente Windows.",
            "ioc": "Processos batch gerando CFGs em massa.",
            "defense": "Monitorar processos suspeitos + auditoria + EDR.",
            "severity": "MEDIO",
        },
    ]
    return jsonify({"modules": modules})


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """Dispara manualmente um evento de ataque sintético."""
    rule_id, rule_name, detail, sev = random.choice(_alert_templates)
    acct = _mask_email(f"conta.{random.randint(10,999)}@provedor.com")
    ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    city = random.choice(_CITIES)
    _state["alerts"].insert(0, {
        "id": uuid.uuid4().hex[:8],
        "rule": rule_id,
        "rule_name": rule_name,
        "severity": sev,
        "detail": detail,
        "account": acct,
        "ip": ip,
        "city": city,
        "ts": datetime.datetime.utcnow().strftime("%H:%M:%S"),
    })
    _state["detections"] += 1
    if sev in ("CRITICO", "ALTO"):
        _state["iofs"] += 1
    return jsonify({"ok": True, "alert": _state["alerts"][0]})


@app.route("/api/simulation/start", methods=["POST"])
def sim_start():
    _state["running"] = True
    return jsonify({"ok": True, "running": True})


@app.route("/api/simulation/stop", methods=["POST"])
def sim_stop():
    _state["running"] = False
    return jsonify({"ok": True, "running": False})


# ---------------------------------------------------------------------------
# AUTO-FLOW (piloto automático)
# ---------------------------------------------------------------------------

@app.route("/api/autoflow/start", methods=["POST"])
def autoflow_start():
    data = request.get_json(silent=True) or {}
    provider = data.get("provider") or "Provedor (simulado)"
    username = data.get("username") or "demo"
    if _autoflow["running"]:
        return jsonify({"ok": False, "message": "Auto-flow já em execução."}), 409
    threading.Thread(target=_autoflow_run, args=(provider, username), daemon=True).start()
    return jsonify({"ok": True, "message": "Auto-flow iniciado."})


@app.route("/api/autoflow/status")
def autoflow_status():
    return jsonify(_autoflow)


# ---------------------------------------------------------------------------
# ROTAÇÃO DE TOKENS / LINKS (proxy para o DEFENSE-CORE)
# ---------------------------------------------------------------------------

@app.route("/api/live_tokens")
def live_tokens_proxy():
    try:
        r = requests.get(f"{CORE_URL}/api/live_tokens", timeout=3)
        return jsonify(r.json())
    except Exception:
        return jsonify({
            "revision": 0, "tokens": [], "error": "DEFENSE-CORE offline.",
        }), 503


@app.route("/api/rotate", methods=["POST"])
def rotate_proxy():
    """Dispara a rotação de tokens/links no provedor simulado."""
    try:
        r = requests.post(f"{CORE_URL}/api/rotate", timeout=3)
        return jsonify(r.json())
    except Exception:
        return jsonify({"ok": False, "error": "DEFENSE-CORE offline."}), 503


@app.route("/api/token_sync")
def token_sync_status():
    return jsonify(_token_sync)


def _add_alert(rule_id, rule_name, detail, severity, account=None, ip=None, city=None):
    """Registra um alerta sintético no simulador."""
    account = account or _mask_email(f"conta.{random.randint(10,999)}@provedor.com")
    ip = ip or f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    city = city or random.choice(_CITIES)
    _state["alerts"].insert(0, {
        "id": uuid.uuid4().hex[:8],
        "rule": rule_id,
        "rule_name": rule_name,
        "severity": severity,
        "detail": detail,
        "account": account,
        "ip": ip,
        "city": city,
        "ts": datetime.datetime.utcnow().strftime("%H:%M:%S"),
    })
    _state["detections"] += 1
    if severity in ("CRITICO", "ALTO"):
        _state["iofs"] += 1


# ---------------------------------------------------------------------------
# AUTENTICAÇÃO SIMULADA (proxy para o DEFENSE-CORE)
# ---------------------------------------------------------------------------

@app.route("/api/auth/accounts")
def auth_accounts():
    """Lista as contas de teste simuladas do DEFENSE-CORE."""
    try:
        r = requests.get(f"{CORE_URL}/api/auth/accounts", timeout=3)
        return jsonify(r.json())
    except Exception:
        return jsonify({
            "accounts": [],
            "error": "DEFENSE-CORE offline. Inicie o servidor interno.",
        }), 503


@app.route("/api/auth/accounts", methods=["POST"])
def auth_accounts_create():
    """Cadastra uma nova conta de teste no DEFENSE-CORE."""
    data = request.get_json(silent=True) or {}
    try:
        r = requests.post(f"{CORE_URL}/api/auth/accounts", json=data, timeout=5)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({"ok": False, "error": "DEFENSE-CORE offline."}), 503


@app.route("/api/auth/accounts/<username>", methods=["PUT"])
def auth_accounts_update(username):
    data = request.get_json(silent=True) or {}
    try:
        r = requests.put(f"{CORE_URL}/api/auth/accounts/{username}", json=data, timeout=5)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({"ok": False, "error": "DEFENSE-CORE offline."}), 503


@app.route("/api/auth/accounts/<username>", methods=["DELETE"])
def auth_accounts_delete(username):
    try:
        r = requests.delete(f"{CORE_URL}/api/auth/accounts/{username}", timeout=5)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({"ok": False, "error": "DEFENSE-CORE offline."}), 503


@app.route("/api/providers")
def providers_list():
    """Lista provedores simulados do DEFENSE-CORE (fonte da verdade)."""
    try:
        r = requests.get(f"{CORE_URL}/api/providers", timeout=3)
        return jsonify(r.json())
    except Exception:
        return jsonify({"providers": PROVIDERS, "error": "DEFENSE-CORE offline (usando lista local)."})


@app.route("/api/providers", methods=["POST"])
def providers_create():
    data = request.get_json(silent=True) or {}
    try:
        r = requests.post(f"{CORE_URL}/api/providers", json=data, timeout=5)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({"ok": False, "error": "DEFENSE-CORE offline."}), 503


@app.route("/api/providers/<pid>", methods=["PUT"])
def providers_update(pid):
    data = request.get_json(silent=True) or {}
    try:
        r = requests.put(f"{CORE_URL}/api/providers/{pid}", json=data, timeout=5)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({"ok": False, "error": "DEFENSE-CORE offline."}), 503


@app.route("/api/providers/<pid>", methods=["DELETE"])
def providers_delete(pid):
    try:
        r = requests.delete(f"{CORE_URL}/api/providers/{pid}", timeout=5)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({"ok": False, "error": "DEFENSE-CORE offline."}), 503


@app.route("/api/captures")
def captures_list():
    """Lista as capturas (KID:KEY DRM simuladas + links M3U FAST) do banco."""
    try:
        r = requests.get(f"{CORE_URL}/api/captures", timeout=3)
        return jsonify(r.json())
    except Exception:
        return jsonify({"captures": [], "error": "DEFENSE-CORE offline."}), 503


@app.route("/api/channels/<channel_id>/capture", methods=["POST"])
def capture_channel(channel_id):
    """Captura um canal (DRM -> KID:KEY simulada | FAST -> link M3U) e registra alerta."""
    data = request.get_json(silent=True) or {}
    base = core_for_provider(data.get("provider"))
    try:
        r = _post_json(base, f"/api/channels/{channel_id}/capture", data)
        payload = r.json()
    except Exception:
        return jsonify({"ok": False, "error": "DEFENSE-CORE offline."}), 503

    if payload.get("ok") and payload.get("capture"):
        cap = payload["capture"]
        if cap.get("type") == "drm_key":
            _add_alert(
                "RULE-007", "Chave DRM (KID:KEY) capturada",
                f"Chave Widevine L3 (SIMULADA) do canal '{cap['channel']}' foi capturada "
                f"e salva no banco (provider {cap['provider']}).",
                "CRITICO",
            )
        else:
            _add_alert(
                "RULE-003", "Stream FAST capturado / re-streaming",
                f"Link M3U do canal FAST '{cap['channel']}' copiado automaticamente "
                f"(provider {cap['provider']}) - reprodução ilimitada simulada.",
                "ALTO",
            )
    return jsonify(payload)


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """Encaminha o login para o DEFENSE-CORE e integra alertas defensivos."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    # CONEXÃO ABERTA: se o operador digitar um endereço de servidor (URL/IP:porta)
    # na hora do login, usa ELE em vez do servidor cadastrado do provedor.
    # Isso permite apontar para qualquer DEFENSE-CORE clonado (VPS em outro país etc.).
    server_override = (data.get("server") or data.get("host") or data.get("url") or "").strip()
    base = server_override or core_for_provider(data.get("provider"))
    try:
        if server_override:
            # CONEXÃO ABERTA: sem fallback — conecta SÓ no endereço digitado,
            # para o operador ver o erro real do servidor (offline, DNS, porta...).
            r = requests.post(f"{server_override}/api/auth/login", json=data, timeout=6)
        else:
            r = _post_json(base, "/api/auth/login", data)
        payload = r.json()
        if server_override:
            payload["server"] = server_override
    except Exception:
        return jsonify({
            "ok": False,
            "error": "core_offline",
            "message": f"Não foi possível conectar ao servidor informado ({base}). Verifique o endereço e se o DEFENSE-CORE está no ar.",
        }), 503

    # Integração com o motor de detecção: gera alerta conforme o cenário
    if payload.get("error") == "senha_incorreta":
        _add_alert(
            "RULE-006", "Brute force / tentativa de login",
            f"Tentativa de login com senha incorreta para '{username or 'desconhecido'}'.",
            "ALTO",
        )
    elif payload.get("error") == "conta_bloqueada":
        _add_alert(
            "RULE-001", "Compartilhamento de token",
            f"Acesso negado: conta '{username}' bloqueada por compartilhamento.",
            "CRITICO",
        )
    elif payload.get("error") == "limite_telas":
        _add_alert(
            "RULE-005", "Excesso de sessoes por conta",
            f"Conta '{username}' tentou exceder o limite de telas simultaneas.",
            "MEDIO",
        )
    elif payload.get("warning"):
        _add_alert(
            "RULE-002", "Anomalia de sessao",
            payload.get("warning"),
            "ALTO",
        )

    # SIMULAÇÃO DE CAPTURA: quando o login é bem-sucedido, o módulo DEFENSE
    # (agindo como o "pirata") captura o token de sessão recém-emitido e o
    # guarda no Vault — mostrando ao cliente exatamente o vetor de ataque.
    if payload.get("ok") and payload.get("session_token"):
        token = payload["session_token"]
        # evita duplicar a captura do mesmo token
        if not any(t["token"] == token for t in _state["token_vault"]):
            captured = {
                "id": uuid.uuid4().hex[:8],
                "token": token,
                "token_id": token[:12].upper(),
                "provider": payload.get("provider", "Desconhecido"),
                "account": username,
                "device_id": payload.get("device_id", "DEV-????"),
                "captured_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "method": "Captura de sessao (simulada) apos login valido",
            }
            _state["token_vault"].insert(0, captured)
            _add_alert(
                "RULE-007", "Token capturado / exfiltrado",
                f"Token de sessao do usuario '{username}' capturado e armazenado no Vault "
                f"(provider {payload.get('provider', 'N/A')}).",
                "CRITICO",
                account=username,
            )
            payload["captured"] = True
            payload["captured_token_id"] = captured["token_id"]

    return jsonify(payload)


# ---------------------------------------------------------------------------
# ACESSO EXTERNO (VPS / internet)
# ---------------------------------------------------------------------------
# Por padrão o painel escuta em 0.0.0.0 para ficar acessível pela internet
# quando hospedado na VPS. Em máquina local, 0.0.0.0 também funciona (o acesso
# é via http://localhost:5050). Para restringir a localhost, defina HOST=127.0.0.1.
@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["X-DEFENSE-LAB"] = "anti-piracy-demo"
    return resp


@app.route("/api/config")
def api_config():
    """Mostra a configuração de rede (útil na VPS)."""
    return jsonify({
        "core_url": CORE_URL,
        "host": os.environ.get("HOST", "0.0.0.0"),
        "port": int(os.environ.get("PORT", "5050")),
        "acesso_externo": os.environ.get("HOST", "0.0.0.0") == "0.0.0.0",
        "aviso": "Painel liberado para acesso externo. Defina CORE_URL para apontar ao DEFENSE-CORE na VPS.",
    })


if __name__ == "__main__":
    _host = os.environ.get("HOST", "0.0.0.0")
    _port = int(os.environ.get("PORT", "5050"))
    print("=" * 60)
    print("AntiPiracy Defense Lab (painel)")
    print(f"Rodando em http://{_host}:{_port}")
    print(f"DEFENSE-CORE (servidor ficticio): {CORE_URL}")
    print("Acesso externo:", "SIM (0.0.0.0)" if _host == "0.0.0.0" else "NAO (localhost)")
    print("=" * 60)
    app.run(host=_host, port=_port, debug=False)
