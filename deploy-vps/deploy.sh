#!/usr/bin/env bash
# =============================================================================
# AntiPiracy Defense Lab — Deploy em VPS Linux (Ubuntu/Debian)
# =============================================================================
# SOBE os dois serviços com systemd + gunicorn, SEM Docker.
# Uso:  sudo bash deploy.sh
# =============================================================================
set -euo pipefail

APP_DIR="/opt/anti-piracy-lab"
PY="/opt/anti-piracy-lab/venv/bin"

echo "[1/6] Instalando pacotes do sistema..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx ufw

echo "[2/6] Copiando o projeto para ${APP_DIR}..."
mkdir -p "${APP_DIR}"
cp -r "$(dirname "$0")/../." "${APP_DIR}/" 2>/dev/null || true

echo "[3/6] Criando ambiente virtual e instalando dependências..."
python3 -m venv "${APP_DIR}/venv"
"${PY}/pip" install --upgrade pip
"${PY}/pip" install -r "${APP_DIR}/requirements-vps.txt" || \
    "${PY}/pip" install flask gunicorn requests

echo "[4/6] Criando serviços systemd..."

cat > /etc/systemd/system/defense-core.service <<'EOF'
[Unit]
Description=AntiPiracy Defense Lab - DEFENSE-CORE (servidor simulado)
After=network.target

[Service]
WorkingDirectory=/opt/anti-piracy-lab
Environment=HOST=0.0.0.0
Environment=PORT=8484
ExecStart=/opt/anti-piracy-lab/venv/bin/gunicorn --bind 0.0.0.0:8484 --workers 2 core_server:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/defense-painel.service <<'EOF'
[Unit]
Description=AntiPiracy Defense Lab - Painel (interface)
After=network.target defense-core.service

[Service]
WorkingDirectory=/opt/anti-piracy-lab
Environment=HOST=0.0.0.0
Environment=PORT=5050
Environment=CORE_URL=http://127.0.0.1:8484
ExecStart=/opt/anti-piracy-lab/venv/bin/gunicorn --bind 0.0.0.0:5050 --workers 3 --timeout 120 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "[5/6] Habilitando e iniciando os serviços..."
systemctl daemon-reload
systemctl enable defense-core defense-painel
systemctl restart defense-core defense-painel

echo "[6/6] Configurando firewall (22, 80, 443, 5050, 8484)..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5050/tcp
ufw allow 8484/tcp
ufw --force enable

echo ""
echo "=============================================================="
echo " DEPLOY CONCLUÍDO"
echo "=============================================================="
echo " Painel:      http://IP_DA_VPS:5050"
echo " Core (fake): http://IP_DA_VPS:8484/health"
echo ""
echo " Para colocar domínio + HTTPS, edite deploy-vps/nginx.conf"
echo " (troque SEU_DOMINIO) e rode:"
echo "   cp deploy-vps/nginx.conf /etc/nginx/sites-available/defense"
echo "   ln -s /etc/nginx/sites-available/defense /etc/nginx/sites-enabled/"
echo "   nginx -t && systemctl reload nginx"
echo "   certbot --nginx -d SEU_DOMINIO"
echo "=============================================================="
