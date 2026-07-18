#!/usr/bin/env bash
# HealthNet - Installation auto (Linux / macOS)
# Compatible Django 1.6.5 + Python 3.11+

set -e

echo "=================================="
echo " HealthNet - Installation auto"
echo "=================================="

# 1. Check Python
echo "[1/4] Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "Erreur : python3 n'est pas installé."
    exit 1
fi
python3 --version

# 2. Install dependencies
echo "[2/4] Installation des dépendances (Django 1.6.5 + zombie-imp)..."
python3 -m pip install --user -r requirements.txt || pip install -r requirements.txt

# 3. Setup database
echo "[3/4] Configuration de la base de données..."
python3 manage.py syncdb --noinput || true

# 4. Run server
echo "[4/4] Lancement du serveur de développement..."
echo "Accédez au site : http://127.0.0.1:8000"
python3 manage.py runserver
