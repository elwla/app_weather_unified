#!/bin/bash
echo "🚀 COMPILACIÓN ANDROID - ESTRUCTURA SDK CORREGIDA"
echo "⏰ Esto puede tomar 30-60 minutos..."

docker run --rm -it \
  -v "$(pwd)":/app \
  -w /app \
  ubuntu:20.04 bash -c "
    set -e
    
    echo '=== ACTUALIZANDO SISTEMA ==='
    apt-get update
    apt-get upgrade -y
    
    echo '=== INSTALANDO DEPENDENCIAS CON JAVA 11 ==='
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
    
    echo '=== CONFIGURANDO JAVA 11 COMO PREDETERMINADO ==='
    update-alternatives --set java /usr/lib/jvm/java-11-openjdk-amd64/bin/java
    update-alternatives --set javac /usr/lib/jvm/java-11-openjdk-amd64/bin/javac
    
    echo '=== CONFIGURANDO PYTHON ==='
    pip3 install --upgrade pip
    pip3 install \
      buildozer \
      flet \
      requests \
      cython
    
    echo '=== CONFIGURACIÓN INICIAL DE BUILDOSER ==='
    if [ ! -f \"buildozer.spec\" ]; then
        buildozer init
    fi
    
    echo '=== FORZANDO API 29 EN BUILDOSER.SPEC ==='
    # Configurar API level 29 para mayor compatibilidad
    sed -i 's/android.api = .*/android.api = 29/' buildozer.spec
    sed -i 's/android.minapi = .*/android.minapi = 21/' buildozer.spec
    
    echo '=== INSTALACIÓN COMPLETA DE ANDROID SDK ==='
    export ANDROID_HOME=\$HOME/.buildozer/android/platform/android-sdk
    mkdir -p \$ANDROID_HOME
    
    # Descargar command line tools manualmente
    cd \$ANDROID_HOME
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
    unzip -q commandlinetools-linux-9477386_latest.zip
    
    # La nueva estructura crea directamente la carpeta 'cmdline-tools'
    # Verificar qué se extrajo
    ls -la
    
    # Configurar PATH correctamente
    export PATH=\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools
    
    # Aceptar licencias automáticamente
    mkdir -p \$ANDROID_HOME/licenses
    echo -e '\n8933bad161af4178b1185d1a37fbf41ea5269c55' > \$ANDROID_HOME/licenses/android-sdk-license
    echo -e '\n84831b9409646a918e30573bab4c9c91346d8abd' > \$ANDROID_HOME/licenses/android-sdk-preview-license
    echo -e '\nd56f5187479451eabf01fb78af6dfcb131a6481e' > \$ANDROID_HOME/licenses/android-sdk-arm-dbt-license
    
    echo '=== INSTALANDO PLATAFORMAS ANDROID ==='
    # Instalar platform-tools y plataforma Android 29
    yes | sdkmanager 'platform-tools' 'platforms;android-29' 'build-tools;34.0.0'
    
    echo '=== VERIFICANDO INSTALACIÓN ==='
    sdkmanager --list | grep -E '(platforms|build-tools)' | head -10
    
    cd /app
    
    echo '=== LIMPIANDO CACHE ANTERIOR ==='
    rm -rf .buildozer 2>/dev/null || true
    
    echo '=== CONFIGURANDO VARIABLES DE ENTORNO PARA API 29 ==='
    export ANDROIDAPI=29
    export ANDROIDMINAPI=21
    
    echo '=== INICIANDO COMPILACIÓN ==='
    buildozer -v android debug
  "

# Verificar resultado
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo ""
    echo "🎉 ¡ÉXITO! APK generado:"
    ls -la bin/*.apk
    echo ""
    echo "📱 Para instalar en tu teléfono:"
    echo "   adb install bin/weatherapp-0.1-debug.apk"
else
    echo ""
    echo "❌ La compilación falló."
fi