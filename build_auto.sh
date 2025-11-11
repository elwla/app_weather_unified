#!/bin/bash
echo "🤖 COMPILADOR CON UBUNTU 20.04"

# Crear main.py si no existe
[ ! -f "main.py" ] && cat > main.py << 'PYTHON'
import flet as ft
def main(page):
    page.title = "Weather App"
    page.add(ft.Text("Hello World"))
ft.app(target=main)
PYTHON

# Crear spec
cat > buildozer.spec << 'SPEC'
[app]
title = Weather App
package.name = weatherapp
package.domain = org.test.weatherapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3, flet, requests
android.permissions = INTERNET
android.api = 31
android.minapi = 21
orientation = portrait
[buildozer]
log_level = 2
warn_on_root = 0
SPEC

echo "🚀 Iniciando compilación con Ubuntu 20.04..."

docker run --rm -it \
  -v "$(pwd)":/app \
  -w /app \
  ubuntu:20.04 \
  bash -c "
    # Configurar entorno sin preguntas interactivas
    export DEBIAN_FRONTEND=noninteractive
    export TZ=UTC
    
    # PASO 1: Actualizar e instalar python3
    echo '🔧 Paso 1: Instalando Python3...'
    apt-get update
    apt-get install -y python3 python3-pip
    
    # PASO 2: Instalar dependencias básicas
    echo '🔧 Paso 2: Instalando dependencias básicas...'
    apt-get install -y git wget unzip zip openjdk-8-jdk
    
    # PASO 3: Instalar buildozer y dependencias
    echo '🐍 Paso 3: Instalando Buildozer...'
    pip3 install buildozer
    
    # PASO 4: Instalar dependencias de la app
    echo '🐍 Paso 4: Instalando Flet y Requests...'
    pip3 install flet requests
    
    # PASO 5: Compilar
    echo '🏗️ Paso 5: Compilando APK...'
    buildozer -v android debug
  "

if [ -f "bin/weatherapp-0.1-debug.apk" ]; then
    echo "🎉 ¡ÉXITO! APK generado:"
    ls -lh bin/weatherapp-0.1-debug.apk
else
    echo "❌ Falló la compilación"
fi