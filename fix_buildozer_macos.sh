#!/bin/bash
echo "🔧 Solucionando problemas de Buildozer en macOS..."

# Limpiar cache de buildozer
rm -rf .buildozer

# Configurar variables de entorno para SSL
export PYTHONHTTPSVERIFY=0
export CURL_CA_BUNDLE=""
export SSL_CERT_FILE=""

# Actualizar pip y certificados
pip install --upgrade pip certifi

# Forzar la reinstalación de certificados
python -m pip install --force-reinstall certifi

# Ejecutar buildozer
echo "🚀 Ejecutando Buildozer..."
buildozer -v android debug
