#!/bin/bash
cd "$(dirname "$0")"
echo "===================================================="
echo "      INICIANDO KAI SYNDICATE - QUANT TERMINAL      "
echo "===================================================="

if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python 3 no está instalado."
    read -p "Presiona Enter para salir..."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[SETUP] Creando entorno virtual..."
    python3 -m venv venv
fi

echo "[SETUP] Activando entorno..."
source venv/bin/activate

echo "[SETUP] Instalando dependencias actualizadas..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "[SYSTEM] Lanzando panel institucional..."
export PYTHONPATH=.
streamlit run app/dashboard.py
