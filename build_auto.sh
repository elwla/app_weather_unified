#!/bin/bash
echo "🤖 COMPILADOR PASO A PASO"

echo "🔧 Paso 1: Creando archivos..."
cat > main.py << 'PYTHON'
import flet as ft
def main(page):
    page.title = "Weather App" 
    page.add(ft.Text("Hello World"))
ft.app(target=main)
PYTHON

cat > buildozer.spec << 'SPEC'
[app]
title = Weather App
package.name = weatherapp  
package.domain = org.test.weatherapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3, flet
android.permissions = INTERNET
android.api = 31
android.minapi = 21
orientation = portrait
[buildozer]
log_level = 2
warn_on_root = 0
SPEC

echo "🔧 Paso 2: Entrando al contenedor..."
docker run --rm -it \
  -v "$(pwd)":/app \
  -w /app \
  ubuntu:20.04 \
  bash