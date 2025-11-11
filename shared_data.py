import json
import os
from threading import Lock
from datetime import datetime

def is_android():
    """Detecta si estamos ejecutando en Android"""
    return hasattr(os, 'getenv') and 'ANDROID_ARGUMENT' in os.environ

class SharedWeatherData:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        self.data_file = self._get_data_path()
        self._ensure_data_directory()
        self.current_data = self._load_data()
    
    def _get_data_path(self):
        """Obtiene la ruta del archivo de datos compartidos"""
        try:
            if is_android():
                # En Android, intentar usar almacenamiento interno
                try:
                    from android.storage import app_storage_path
                    base_dir = app_storage_path()
                except ImportError:
                    # Fallback para Android sin imports
                    base_dir = "/data/data/org.test.weatherapp/files"
            else:
                # En desarrollo
                base_dir = "."
            
            data_dir = os.path.join(base_dir, "weather_widget_data")
            os.makedirs(data_dir, exist_ok=True)
            return os.path.join(data_dir, "current_weather.json")
            
        except Exception as e:
            print(f"⚠️ Error obteniendo ruta: {e}")
            # Fallback absoluto
            return "current_weather.json"
    
    def _ensure_data_directory(self):
        """Asegura que el directorio de datos existe"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        except Exception as e:
            print(f"⚠️ Error creando directorio: {e}")
    
    def _load_data(self):
        """Carga los datos existentes"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error cargando datos: {e}")
        
        # Datos por defecto
        return {
            "city": "Agregar ciudad",
            "temperature": 0,
            "description": "Sin datos",
            "last_update": datetime.now().isoformat(),
            "humidity": 0,
            "wind_speed": 0,
            "icon": "☀️"
        }
    
    def update_weather_data(self, city, temperature, description, humidity=0, wind_speed=0, icon="☀️"):
        """Actualiza los datos del clima para el widget"""
        with self._lock:
            self.current_data = {
                "city": city,
                "temperature": temperature,
                "description": description,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "icon": icon,
                "last_update": datetime.now().isoformat()
            }
            
            # Guardar en archivo
            try:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_data, f, ensure_ascii=False, indent=2)
                print(f"✅ Datos para widget guardados: {city} - {temperature}°")
            except Exception as e:
                print(f"❌ Error guardando datos widget: {e}")
    
    def get_weather_data(self):
        """Obtiene los datos actuales para el widget"""
        with self._lock:
            return self.current_data.copy()