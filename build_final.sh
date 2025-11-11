#!/bin/bash
echo "🏁 COMPILACIÓN FINAL - TODAS LAS DEPENDENCIAS INCLUIDAS"
echo "⏰ Esto puede tomar 20-40 minutos..."

docker run --rm -it \
  -v "$(pwd)":/app \
  -w /app \
  ubuntu:20.04 bash -c "
    set -e
    
    echo '1. 📦 INSTALANDO DEPENDENCIAS DEL SISTEMA...'
    apt-get update
    apt-get install -y \
      python3 \
      python3-pip \
      git \
      zip \
      unzip \
      openjdk-11-jdk \
      autoconf \
      automake \
      libtool \
      pkg-config \
      build-essential \
      zlib1g-dev \
      libffi-dev \
      libssl-dev \
      libsqlite3-dev \
      wget \
      curl \
      unzip
    
    echo '2. ⚙️ CONFIGURANDO JAVA...'
    update-alternatives --set java /usr/lib/jvm/java-11-openjdk-amd64/bin/java
    
    echo '3. 🐍 INSTALANDO PAQUETES PYTHON...'
    pip3 install buildozer flet requests cython
    
    echo '4. 🏗️ CONFIGURANDO BUILDOSER...'
    if [ ! -f \"buildozer.spec\" ]; then
        buildozer init
        sed -i 's/android.api = .*/android.api = 29/' buildozer.spec
        sed -i 's/android.minapi = .*/android.minapi = 21/' buildozer.spec
    fi
    
    echo '5. 🚀 INICIANDO COMPILACIÓN...'
    # Responder sí automáticamente y usar API 29
    echo 'y' | ANDROIDAPI=29 buildozer -v android debug
  "

if ls bin/*.apk 1> /dev/null 2>&1; then
    echo ""
    echo "🎉 ¡ÉXITO! APK generado:"
    ls -la bin/*.apk
    echo ""
    echo "📱 Para instalar: adb install bin/weatherapp-0.1-debug.apk"
else
    echo ""
    echo "❌ La compilación falló."
    echo "💡 Posibles soluciones:"
    echo "   - Verifica tu conexión a internet"
    echo "   - Asegúrate de tener suficiente espacio en disco"
    echo "   - Revisa que todos los archivos de tu app estén presentes"
fi
