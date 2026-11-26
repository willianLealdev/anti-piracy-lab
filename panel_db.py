# -*- coding: utf-8 -*-
"""
Banco local do PAINEL (SQLite).

Os provedores cadastrados pelo operador ficam AQUI (no painel), e nao no
DEFENSE-CORE da VPS. O core e apenas o ambiente de simulacao de demonstracao.
"""
import datetime
import os
import sqlite3
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "panel.db")


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                drm TEXT DEFAULT 'Sem DRM',
                channels TEXT DEFAULT '0',
                description TEXT DEFAULT '',
                server TEXT DEFAULT '',
                protocol TEXT DEFAULT 'xtream',
                created_at TEXT
            )
            """
        )
        n = c.execute("SELECT COUNT(*) AS n FROM providers").fetchone()["n"]
        if n == 0:
            _seed(c)


def _seed(c):
    now = datetime.datetime.now().isoformat(timespec="seconds")
    # protocol:
    #   pluto  -> API oficial publica (nao pede login)
    #   xtream -> painel Xtream Codes (o operador digita o endereco)
    #   core   -> DEFENSE-CORE simulado (o operador digita o endereco da VPS)
    defaults = [
        {
            "id": "pluto", "name": "Pluto TV (API oficial)", "drm": "Sem DRM (FAST)", "channels": "187",
            "description": "Canais FAST gratuitos. API publica https://api.pluto.tv - nao pede login.",
            "server": "https://api.pluto.tv", "protocol": "pluto",
        },
        {
            "id": "soultv", "name": "Soul TV Brasil (FAST)", "drm": "Sem DRM (FAST)", "channels": "76",
            "description": "Canais FAST nacionais reais. Site publico https://soultv.com.br - nao pede login.",
            "server": "https://soultv.com.br", "protocol": "soultv",
        },
        {
            "id": "xtream", "name": "Xtream Codes (generico)", "drm": "A definir", "channels": "0",
            "description": "Painel IPTV Xtream Codes real do cliente. Digite IP/dominio no campo Servidor do login.",
            "server": "", "protocol": "xtream",
        },
        {
            "id": "defense-core", "name": "DEFENSE-CORE (simulado)", "drm": "Simulado", "channels": "0",
            "description": "Servidor de simulacao. Digite o endereco do DEFENSE-CORE na VPS no campo Servidor.",
            "server": "", "protocol": "core",
        },
        # --- Provedores SIMULADOS (dados sinteticos, para demonstracao) ---
        {
            "id": "globoplay", "name": "GloboPlay Completo", "drm": "Widevine L3", "channels": "180",
            "description": "125 Globos Regionais + 9 Premiere HD + 4 SporTV (1,2,3,4K) + 6 Telecine + Combate + GloboNews + Multishow + GNT + Viva + Gloob + FAST + BBB.",
            "server": "", "protocol": "core",
        },
        {
            "id": "astra", "name": "Astra TV (Cesbo)", "drm": "Sem DRM", "channels": "90",
            "description": "Abertos (SBT, Record, Band, RedeTV), Telecine, SporTV, Filmes, Infantis, Noticias, Religiosos e Variedades.",
            "server": "", "protocol": "core",
        },
        {
            "id": "skyplus", "name": "Sky+ (DirectvGO)", "drm": "Widevine L3", "channels": "86",
            "description": "Canais ao vivo com DRM Widevine L3. Captura automatica de KID:KEY no Chrome. Multi-audio PT/EN.",
            "server": "", "protocol": "core",
        },
        {
            "id": "primevideo", "name": "Prime Video (Amazon)", "drm": "Widevine L3 / ClearKey", "channels": "45",
            "description": "CazeTV (1,2,3), ge TV, CNN Brasil, Bloomberg e pacotes extras/Channels da conta. FHD e HD.",
            "server": "", "protocol": "core",
        },
        {
            "id": "soultv", "name": "Soul TV Brasil", "drm": "Sem DRM", "channels": "77",
            "description": "Canais FAST e regionais brasileiros: Minas Gerais, Filmes/Series, Esportes, Cultura, Musica e Variedades.",
            "server": "", "protocol": "core",
        },
        {
            "id": "youtube", "name": "YouTube Live", "drm": "Sem DRM", "channels": "15",
            "description": "CazeTV, Canal GOAT, SBT News 24h, Jovem Pan News, Record News, DBZ, Bluey, Boomerang, MMA 24/7.",
            "server": "", "protocol": "core",
        },
        {
            "id": "recordplus", "name": "Record+ / PlayPlus", "drm": "Sem DRM", "channels": "10",
            "description": "Record SP, RJ, MG, Brasilia, BA, Record News, Curitiba, Fortaleza, Vitoria e Campinas - HLS diretos.",
            "server": "", "protocol": "core",
        },
        {
            "id": "bandplay", "name": "BandPlay Oficial", "drm": "Sem DRM", "channels": "29",
            "description": "18 Band Regionais + BandNews TV, BandSports, Terra Viva + 11 Radios oficiais sem DRM.",
            "server": "", "protocol": "core",
        },
        {
            "id": "hbomax", "name": "HBO Max", "drm": "Widevine L3", "channels": "40",
            "description": "HBO, Max Originals, DC, Cartoon Network.",
            "server": "", "protocol": "core",
        },
        {
            "id": "disneyplus", "name": "Disney+", "drm": "Widevine L3", "channels": "35",
            "description": "ESPN, Disney Channel, National Geographic, Star.",
            "server": "", "protocol": "core",
        },
        {
            "id": "paramountplus", "name": "Paramount+", "drm": "Widevine L3", "channels": "30",
            "description": "CBS, Nickelodeon, MTV, Paramount Pictures.",
            "server": "", "protocol": "core",
        },
        {
            "id": "clarotv", "name": "Claro TV+", "drm": "Widevine L3", "channels": "120",
            "description": "Globos Regionais, SporTV (1,2,3), Premiere, Telecine, Discovery, History, Fox, ESPN, Infantis + variedades.",
            "server": "", "protocol": "core",
        },
        # --- FAST adicionais (simulados: APIs reais exigem token/device) ---
        {
            "id": "samsungtvplus", "name": "Samsung TV Plus (simulado)", "drm": "Sem DRM (FAST)", "channels": "100",
            "description": "FAST internacional simulado: noticias, entretenimento, filmes e musica.",
            "server": "", "protocol": "core",
        },
        {
            "id": "roku", "name": "Roku Channel (simulado)", "drm": "Sem DRM (FAST)", "channels": "80",
            "description": "FAST simulado: filmes e series gratuitos com anuncios.",
            "server": "", "protocol": "core",
        },
        {
            "id": "plex", "name": "Plex Live TV (simulado)", "drm": "Sem DRM (FAST)", "channels": "60",
            "description": "FAST simulado: canais ao vivo e on-demand.",
            "server": "", "protocol": "core",
        },
        {
            "id": "redbulltv", "name": "Red Bull TV (simulado)", "drm": "Sem DRM (FAST)", "channels": "20",
            "description": "FAST simulado: esportes radicais e eventos ao vivo.",
            "server": "", "protocol": "core",
        },
    ]
    for p in defaults:
        c.execute(
            "INSERT OR IGNORE INTO providers (id, name, drm, channels, description, server, protocol, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (p["id"], p["name"], p["drm"], p["channels"], p["description"], p["server"], p["protocol"], now),
        )


def list_providers():
    with _conn() as c:
        rows = c.execute("SELECT * FROM providers ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_provider(pid):
    with _conn() as c:
        row = c.execute("SELECT * FROM providers WHERE id=? OR name=?", (pid, pid)).fetchone()
    return dict(row) if row else None


def create_provider(data):
    pid = (data.get("id") or "").strip() or ("p-" + uuid.uuid4().hex[:10])
    now = datetime.datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO providers (id, name, drm, channels, description, server, protocol, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                pid,
                (data.get("name") or "").strip() or pid,
                (data.get("drm") or "Sem DRM").strip(),
                str(data.get("channels") or "0"),
                (data.get("description") or "").strip(),
                (data.get("server") or "").strip(),
                (data.get("protocol") or "xtream").strip(),
                now,
            ),
        )
    return {"ok": True, "id": pid}


def update_provider(pid, data):
    with _conn() as c:
        cur = c.execute("SELECT * FROM providers WHERE id=?", (pid,))
        row = cur.fetchone()
        if not row:
            return {"ok": False, "error": "Provedor nao encontrado."}
        c.execute(
            "UPDATE providers SET name=?, drm=?, channels=?, description=?, server=?, protocol=? WHERE id=?",
            (
                (data.get("name") or row["name"]).strip(),
                (data.get("drm") or row["drm"]).strip(),
                str(data.get("channels") if data.get("channels") is not None else row["channels"]),
                (data.get("description") or row["description"]).strip(),
                (data.get("server") or row["server"] or "").strip(),
                (data.get("protocol") or row["protocol"] or "xtream").strip(),
                pid,
            ),
        )
    return {"ok": True, "id": pid}


def delete_provider(pid):
    with _conn() as c:
        c.execute("DELETE FROM providers WHERE id=?", (pid,))
    return {"ok": True}
