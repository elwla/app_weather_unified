#Funcionamiento con la API de Open-Meteo para obtener datos meteorológicos 
# y mostrarlos en una interfaz gráfica usando Flet.

import requests
from datetime import datetime
from database_manager import DatabaseManager  # Agregar esta importación

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.db_manager = DatabaseManager()
        self.locations = self.load_locations_from_db()
    
    def load_locations_from_db(self):
        """Carga las ubicaciones desde la base de datos"""
        cities = self.db_manager.get_all_cities()
        locations = {}
        for city in cities:
            locations[city["name"]] = {
                "lat": city["lat"],
                "lon": city["lon"]
            }
        print(f"Se cargaron {len(locations)} ciudades desde la base de datos")
        return locations
    
    def get_last_selected_city(self):
        """Obtiene la última ciudad seleccionada"""
        return self.db_manager.get_last_selected_city()
    
    def set_last_selected_city(self, city_name):
        """Guarda la última ciudad seleccionada"""
        return self.db_manager.set_last_selected_city(city_name)

    def add_location(self, name: str, lat: float, lon: float) -> bool:
        """Agrega una nueva ubicación a la base de datos y al servicio"""
        success = self.db_manager.add_city(name, lat, lon)
        if success:
            # Actualizar el diccionario en memoria
            self.locations[name] = {"lat": lat, "lon": lon}
            print(f"Ciudad {name} agregada al servicio")
        return success
    
    def delete_location(self, name: str) -> bool:
        """Elimina una ubicación de la base de datos y del servicio"""
        print(f"Intentando eliminar ciudad: {name}")
        success = self.db_manager.delete_city(name)
        if success:
            if name in self.locations:
                # Actualizar el diccionario en memoria
                del self.locations[name]
                print(f"Ciudad {name} eliminada exitosamente del servicio")
            else:
                print(f"Ciudad {name} no encontrada en locations (pero se eliminó de BD)")
        else:
            print(f"Fallo al eliminar ciudad: {name} de la base de datos")
        return success
    
    def get_weather_data(self, location_name):
        """Obtiene datos meteorológicos para una ubicación específica"""
        if location_name not in self.locations:
            return self.get_default_data()
        
        location = self.locations[location_name]
        
        try:
            params = {
                'latitude': location['lat'],
                'longitude': location['lon'],
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,is_day,weather_code',
                'hourly': 'temperature_2m,relative_humidity_2m,precipitation_probability,weather_code',
                'daily': 'weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_sum',
                'timezone': 'auto',
                'forecast_days': 1
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'current': data.get('current', {}),
                    'hourly': data.get('hourly', {}),
                    'daily': data.get('daily', {}),
                    'success': True
                }
            else:
                return self.get_default_data()
                
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return self.get_default_data()
    
    def get_default_data(self):
        """Devuelve datos por defecto en caso de error o cuando no hay ciudades"""
        return {
            'current': {
                'temperature_2m': 0,
                'relative_humidity_2m': 0,
                'wind_speed_10m': 0,
                'pressure_msl': 0,
                'precipitation': 0,
                'weather_code': 0,
                'is_day': 1
            },
            'hourly': {
                'time': [],
                'temperature_2m': [],
                'weather_code': []
            },
            'daily': {
                'temperature_2m_max': [0],
                'temperature_2m_min': [0],
                'sunrise': ['--:--'],
                'sunset': ['--:--'],
                'uv_index_max': [0],
                'weather_code': [0]
            },
            'success': False
        }
    
    def get_weather_icon(self, weather_code, is_day=True):
        """Obtiene el icono correspondiente al código del clima"""
        weather_icons = {
            0: "wi-day-sunny",  # Despejado
            1: "wi-day-sunny-overcast",  # Mayormente despejado
            2: "wi-day-cloudy",  # Parcialmente nublado
            3: "wi-cloudy",  # Nublado
            45: "wi-fog",  # Niebla
            48: "wi-fog",  # Niebla escarchada
            51: "wi-day-sprinkle",  # Llovizna ligera
            53: "wi-day-sprinkle",  # Llovizna moderada
            55: "wi-day-sprinkle",  # Llovizna densa
            61: "wi-day-rain",  # Lluvia ligera
            63: "wi-day-rain",  # Lluvia moderada
            65: "wi-day-rain",  # Lluvia fuerte
            80: "wi-day-rain",  # Chubascos ligeros
            81: "wi-day-rain",  # Chubascos moderados
            82: "wi-day-rain",  # Chubascos fuertes
            95: "wi-day-thunderstorm",  # Tormenta ligera
            96: "wi-day-thunderstorm",  # Tormenta con granizo ligero
            99: "wi-day-thunderstorm",  # Tormenta con granizo fuerte
        }

        icon = weather_icons.get(weather_code, "wi-day-sunny")
        if not is_day:
            icon = icon.replace("day", "night")
        
        return f"{icon}.svg"
    
    def get_weather_description(self, weather_code):
        """Obtiene la descripción del clima basada en el código"""
        descriptions = {
            0: "Sin datos",
            1: "Mayormente despejado", 
            2: "Parcialmente nublado",
            3: "Nublado",
            45: "Niebla",
            48: "Niebla escarchada",
            51: "Llovizna ligera",
            53: "Llovizna moderada", 
            55: "Llovizna densa",
            61: "Lluvia ligera",
            63: "Lluvia moderada",
            65: "Lluvia fuerte",
            80: "Chubascos ligeros",
            81: "Chubascos moderados",
            82: "Chubascos fuertes",
            95: "Tormenta eléctrica",
            96: "Tormenta con granizo",
            99: "Tormenta fuerte con granizo"
        }
        return descriptions.get(weather_code, "Sin datos")
    

    def format_time(self, time_str, format_type='hour'):
        """Formatea el tiempo de la API"""
        try:
            if not time_str or time_str == '--:--':
                return '--:--'
                
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            if format_type == 'hour':
                return dt.strftime('%I %p').lstrip('0')
            elif format_type == 'time':
                return dt.strftime('%H:%M')
            else:
                return time_str
        except:
            return time_str
        
    def get_all_locations(self):
        """Devuelve todas las ubicaciones disponibles"""
        return list(self.locations.keys())
    
    def has_locations(self):
        """Verifica si hay ciudades disponibles"""
        return len(self.locations) > 0