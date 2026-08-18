#!/bin/bash
# Portal Puente MS — doble clic para iniciar (Mac)
cd "$(dirname "$0")"
echo "Iniciando el Portal Puente MS..."
python3 portal.py
read -p "Portal detenido. Presiona Enter para cerrar."
