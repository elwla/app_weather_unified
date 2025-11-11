#!/bin/bash
echo "🤖 Compilación Rápida - API Android 29"

cat > buildozer.spec << 'SPEC'
[app]
title = Weather App
package.name = weatherapp
package.domain = org.test.weatherapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy,flet,requests
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 29
android.minapi = 21
orientation = portrait
[buildozer]
log_level = 2
warn_on_root = 0
SPEC

echo "🚀 Compilando con Android 29 (más rápido)..."

docker run --rm -it \
  -v "$(pwd)":/app \
  -w /app \
  ubuntu:22.04 \
  bash -c "
    apt update && apt install -y python3-pip openjdk-11-jdk wget unzip &&
    pip3 install buildozer flet requests &&
    buildozer -v android debug
  "

[ -f "bin/weatherapp-0.1-debug.apk" ] && echo "🎉 ¡ÉXITO!" || echo "❌ Falló"