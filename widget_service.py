import os
import time
import threading
from datetime import datetime
from shared_data import SharedWeatherData

class WidgetService:
    def __init__(self):
        self.shared_data = SharedWeatherData()
        self.is_running = False
        self.thread = None
        
    def start(self):
        """Inicia el servicio del widget"""
        if self.is_running:
            print("⚠️ Servicio de widget ya está ejecutándose")
            return
            
        self.is_running = True
        self._start_development_service()
    
    def _start_development_service(self):
        """Servicio para desarrollo (simulación)"""
        def development_loop():
            update_count = 0
            while self.is_running:
                try:
                    data = self.shared_data.get_weather_data()
                    update_count += 1
                    
                    print(f"🎯 Widget Simulator - Ejecución #{update_count}")
                    print(f"   📍 {data['city']}")
                    print(f"   {data['icon']} {data['temperature']}°C - {data['description']}")
                    print(f"   💧 Humedad: {data['humidity']}%")
                    print(f"   💨 Viento: {data['wind_speed']} km/h")
                    print(f"   ⏰ Última actualización: {data['last_update'][11:16]}")
                    print("   " + "─" * 40)
                    
                    time.sleep(30)  # Actualizar cada 30 segundos en desarrollo
                    
                except Exception as e:
                    print(f"❌ Error en simulador: {e}")
                    time.sleep(60)
        
        self.thread = threading.Thread(target=development_loop, daemon=True)
        self.thread.start()
        print("🔧 Servicio de widget (simulador) iniciado")
    
    def stop(self):
        """Detiene el servicio del widget"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        print("🛑 Servicio de widget detenido")

# Instancia global del servicio
widget_service = WidgetService()

# Funciones de conveniencia
def start_widget_service():
    """Inicia el servicio del widget"""
    widget_service.start()

def stop_widget_service():
    """Detiene el servicio del widget"""
    widget_service.stop()