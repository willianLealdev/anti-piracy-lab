# -*- coding: utf-8 -*-
"""
Gera STREAMS 100% SINTÉTICOS (reproduzíveis no VLC) para o DEFENSE-LAB.

Cada "canal" é um stream HLS gerado com padrões de teste do ffmpeg
(testsrc2, smptebars) + texto sobreposto com o nome do canal e a marca
"DEFENSE-LAB SIMULADO".

NENHUM conteúdo protegido. NENHUM vídeo de terceiros.
São barras de cor / padrões de teste, como um "set de filmagem".

Uso:
    python gerar_streams.py
"""

import os
import platform
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "streams")

# Fonte compatÃ­vel com Windows (local) e Linux (Docker/VPS)
if platform.system() == "Windows":
    FONT = "C:/Windows/Fonts/arialbd.ttf"
    if not os.path.exists(FONT):
        FONT = "C:/Windows/Fonts/arial.ttf"
else:
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(FONT):
        FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Canais simulados: (id, nome, resolucao WxH, tipo)
# tipo: drm | fast | youtube  -> usamos para categorizar a demonstração
CANALS = [
    ("globo_rj_sim", "Globo RJ (SIMULADO)", "1920x1080", "drm"),
    ("telecine_sim", "Telecine Action (SIMULADO)", "1920x1080", "drm"),
    ("sportv_sim", "SporTV 1 (SIMULADO)", "1280x720", "drm"),
    ("pluto_filmes_sim", "Pluto Filmes (SIMULADO)", "640x360", "fast"),
    ("soul_mg_sim", "Soul TV MG (SIMULADO)", "640x360", "fast"),
    ("record_sp_sim", "Record SP (SIMULADO)", "1280x720", "fast"),
    ("cazetv_sim", "CazeTV Ao Vivo (SIMULADO)", "1280x720", "youtube"),
    ("sbtnews_sim", "SBT News 24h (SIMULADO)", "1280x720", "youtube"),
]


def esc(texto):
    """Escapa o texto para o filtro drawtext (evita quebra de comando)."""
    return texto.replace(":", "\\:").replace("'", "").replace("(", "\\(").replace(")", "\\)")


# Caminho da fonte com ':' escapado para o filtro drawtext no Windows
FONT_ESC = FONT.replace(":", "\\:")


def gerar(canal_id, nome, resolucao):
    pasta = os.path.join(OUT, canal_id)
    os.makedirs(pasta, exist_ok=True)
    playlist = os.path.join(pasta, "index.m3u8")

    # Padrão de teste + tom de áudio + texto sobreposto
    draw = f"drawtext=fontfile='{FONT_ESC}':text='{esc(nome)}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=36:box=1:boxcolor=black@0.6:boxborderw=12"
    draw2 = f"drawtext=fontfile='{FONT_ESC}':text='DEFENSE-LAB STREAM 100%% SIMULADO':fontcolor=yellow:fontsize=22:x=(w-text_w)/2:y=h-72:box=1:boxcolor=black@0.6:boxborderw=10"

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"testsrc2=size={resolucao}:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
        "-t", "4",  # 4s de stream (suficiente para demo; o VLC da loop)
        "-vf", f"{draw},{draw2}",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
        "-c:a", "aac", "-b:a", "96k",
        "-f", "hls", "-hls_time", "3", "-hls_list_size", "0",
        "-hls_segment_filename", os.path.join(pasta, "seg_%03d.ts"),
        playlist,
    ]

    print(f"[gerar] {canal_id} ({resolucao}) -> {playlist}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[ERRO] {canal_id}: {r.stderr[-500:]}")
        return False
    return True


def main():
    os.makedirs(OUT, exist_ok=True)
    ok = 0
    for canal_id, nome, resolucao, tipo in CANALS:
        if gerar(canal_id, nome, resolucao):
            ok += 1
    print(f"\nConcluído: {ok}/{len(CANALS)} streams gerados em {OUT}")

    # Grava o manifesto dos canais (para o DEFENSE-CORE servir)
    import json
    manifest = []
    for canal_id, nome, resolucao, tipo in CANALS:
        manifest.append({
            "id": canal_id,
            "name": nome,
            "resolution": resolucao,
            "type": tipo,
            "url": f"/streams/{canal_id}/index.m3u8",
            "playable": True,
        })
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("Manifesto gravado em streams/manifest.json")


if __name__ == "__main__":
    sys.exit(main())
