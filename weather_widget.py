from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform
from jnius import autoclass, cast
import json
import os
from datetime import datetime
from shared_data import SharedWeatherData

# Solo en Android
if platform == 'android':
    from android.runnable import run_on_ui_thread
    
    # Clases de Android para el widget
    Context = autoclass('android.content.Context')
    RemoteViews = autoclass('android.widget.RemoteViews')
    AppWidgetManager = autoclass('android.appwidget.AppWidgetManager')
    ComponentName = autoclass('android.content.ComponentName')
    Intent = autoclass('android.content.Intent')

class AndroidWeatherWidget:
    def __init__(self):
        self.context = None
        self.setup_widget()
    
    def setup_widget(self):
        """Configura el widget de Android"""
        try:
            if platform == 'android':
                from android import mActivity
                self.context = mActivity.getApplicationContext()
                print("✅ Widget Android configurado")
        except Exception as e:
            print(f"❌ Error configurando widget Android: {e}")
    
    @run_on_ui_thread
    def update_widget(self):
        """Actualiza el widget en la UI principal"""
        try:
            if not self.context:
                return
            
            # Cargar datos
            shared_data = SharedWeatherData()
            data = shared_data.get_weather_data()
            
            # Crear RemoteViews
            views = RemoteViews(self.context.getPackageName(), R.layout.widget_weather)
            
            # Actualizar vistas
            views.setTextViewText(R.id.widget_city, data['city'])
            views.setTextViewText(R.id.widget_temp, f"{data['temperature']}°")
            views.setTextViewText(R.id.widget_desc, data['description'])
            views.setTextViewText(R.id.widget_update, 
                                f"Actualizado: {datetime.now().strftime('%H:%M')}")
            
            # Actualizar widget
            appWidgetManager = AppWidgetManager.getInstance(self.context)
            componentName = ComponentName(self.context, WeatherWidgetProvider)
            appWidgetManager.updateAppWidget(componentName, views)
            
            print("✅ Widget actualizado")
            
        except Exception as e:
            print(f"❌ Error actualizando widget: {e}")

# Servicio principal que se ejecuta en segundo plano
class WeatherWidgetService:
    def __init__(self):
        self.widget = AndroidWeatherWidget()
        self.start_widget_updater()
    
    def start_widget_updater(self):
        """Inicia las actualizaciones automáticas del widget"""
        Clock.schedule_interval(lambda dt: self.widget.update_widget(), 300)  # 5 minutos