import flet as ft
from weather_service import WeatherService
import threading
import time
from datetime import datetime, timedelta
from shared_data import SharedWeatherData
from widget_service import start_widget_service, stop_widget_service

class WeatherApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.weather_service = WeatherService()
        self.shared_data = SharedWeatherData()
        
        # Configuración de colores
        self.bgcolor = '#6E3405'
        self.container_color = '#8A430A'
        self.black_color = '#000000'
        self.contorn_color = '#9E5C26'
        self.accent_color = '#F58427'

        self.auto_refresh_interval = 1800  # 30 minutos
        self.last_refresh = None
        self.is_running_in_background = False

        # Variables para el pull to refresh
        self.start_y = None
        self.current_y = None
        self.refresh_threshold = 100
        self.is_refreshing = False
        
        # Datos de la aplicación
        self.current_location = None
        self.weather_data = None
        
        # Configurar página
        self.setup_page()

        self.load_initial_data()
        
        # Cargar datos iniciales
        self.load_weather_data()
        
        # Construir la interfaz
        self.build_interface()

        # Iniciar auto-refresh
        self.start_auto_refresh()

        self.start_widget_services()

    def load_initial_data(self):
        """Carga los datos iniciales, usando la última ciudad seleccionada"""      
        # Primero intentar cargar la última ciudad seleccionada
        last_city = self.weather_service.get_last_selected_city()
        available_cities = self.weather_service.get_all_locations()
        
        if last_city and last_city in available_cities:
            # Usar la última ciudad seleccionada
            self.current_location = last_city
            self.load_weather_data(self.current_location)
        elif available_cities:
            # Si no hay última ciudad, usar la primera disponible
            self.current_location = available_cities[0]
            self.load_weather_data(self.current_location)
            # Guardar como última seleccionada
            self.weather_service.set_last_selected_city(self.current_location)
        else:
            # No hay ciudades
            self.current_location = None
            self.weather_data = self.weather_service.get_default_data()
        
    def setup_page(self):
        """Configura la página principal"""
        self.page.bgcolor = self.bgcolor
        self.page.title = "Weather App"
        self.page.spacing = 5
        self.page.padding = 5
        self.page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap",
            "OpenSans": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap"
        }
        self.page.theme = ft.Theme(
            scrollbar_theme=ft.ScrollbarTheme(thumb_color=self.container_color),
            font_family="Roboto"
        )
    
    def load_weather_data(self, location_name=None):
        """Carga los datos meteorológicos desde el servicio"""
        try:
            if location_name:
                self.current_location = location_name
                print(f"Cargando datos para: {location_name}")
            
            self.weather_data = self.weather_service.get_weather_data(self.current_location)
            
            # ACTUALIZAR DATOS PARA EL WIDGET <-- AGREGAR ESTO
            if self.weather_data and self.current_location:
                current_data = self.weather_data['current']
                temperature = round(current_data.get('temperature_2m', 0))
                description = self.weather_service.get_weather_description(
                    current_data.get('weather_code', 0)
                )
                
                # Mapear iconos simples para el widget
                icon_map = {
                    0: "☀️",   # Despejado
                    1: "⛅",   # Mayormente despejado  
                    2: "🌤️",  # Parcialmente nublado
                    3: "☁️",   # Nublado
                    45: "🌫️", # Niebla
                    61: "🌧️", # Lluvia ligera
                    63: "🌧️", # Lluvia moderada
                    95: "⛈️",  # Tormenta
                }
                icon = icon_map.get(current_data.get('weather_code', 0), "🌈")
                
                self.shared_data.update_weather_data(
                    city=self.current_location,
                    temperature=temperature,
                    description=description,
                    humidity=current_data.get('relative_humidity_2m', 0),
                    wind_speed=current_data.get('wind_speed_10m', 0),
                    icon=icon
                )
                
        except Exception as e:
            self.weather_data = self.weather_service.get_default_data()
    
    def start_widget_services(self):
        """Inicia todos los servicios relacionados con el widget"""
        try:
            start_widget_service()
            print("✅ Servicio de widget iniciado")
        except Exception as e:
            print(f"❌ Error iniciando servicio widget: {e}")
    
    def refresh_interface(self):
        """Actualiza toda la interfaz con los datos actuales"""
        try:
            # Limpiar la página
            self.page.controls.clear()
            
            # Reconstruir la interfaz
            self.build_interface()
            
            # Actualizar la página
            self.page.update()
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def start_auto_refresh(self):
        """Inicia la actualización automática"""
        def refresh_loop():
            while self.is_running_in_background:
                try:
                    # Actualizar cada 30 minutos o cuando la app se reactive
                    time.sleep(self.auto_refresh_interval)
                    if self.current_location:
                        print(f"Auto-refresh: Actualizando datos para {self.current_location}")
                        self.load_weather_data()
                        self.page.run_thread(self.refresh_interface)
                except Exception as e:
                    print(f"Error en auto-refresh: {e}")
        
        self.is_running_in_background = True
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()
    
    def stop_auto_refresh(self):
        """Detiene la actualización automática"""
        self.is_running_in_background = False
    
    def on_app_reactivate(self):
        """Se llama cuando la app se reactiva"""
        print("App reactivada - actualizando datos...")
        if self.current_location:
            self.load_weather_data()
            self.refresh_interface()
    
    def build_interface(self):
        """Construye la interfaz de usuario"""
        try:
            # Limpiar la página completamente
            self.page.controls.clear()
            
            # Verificar si hay datos de clima disponibles
            if not self.weather_service.has_locations() or self.current_location is None:
                # Mostrar interfaz para agregar primera ciudad
                self.show_empty_state()
                return
                
            # Obtener datos actuales
            current_data = self.weather_data['current']
            current_temp = round(current_data.get('temperature_2m', 18))
            weather_code = current_data.get('weather_code', 1)
            is_day = current_data.get('is_day', 1) == 1
            weather_desc = self.weather_service.get_weather_description(weather_code)
            weather_icon = self.weather_service.get_weather_icon(weather_code, is_day)

            self.last_update_text = ft.Text(
                f"Última actualización: {datetime.now().strftime('%H:%M')}",
                size=12,
                color=ft.Colors.WHITE60,
                text_align=ft.TextAlign.CENTER
            )
                        
            # Container 1 - Vista principal
            self.container_1 = self.build_container_1(current_temp, weather_desc, weather_icon)
            
            # Container 2 - Vista de ubicación alternativa
            self.container_2 = self.build_container_2(current_temp, weather_desc)
            
            # Container 3 - Lista de ubicaciones
            self.container_3 = self.build_locations_list()
            
            # Navigation y controles
            self.selected = ft.Container(
                shape=ft.BoxShape.CIRCLE,
                offset=ft.Offset(0, 0),
                animate_offset=ft.Animation(200, "easeIn"),
                gradient=ft.SweepGradient(colors=[self.black_color, self.container_color, self.black_color]),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=10),
                height=40,
                content=ft.Icon(ft.Icons.ADD_CIRCLE, size=40, color="white")
            )
            
            self.nav = ft.Container(
                gradient=ft.LinearGradient(colors=[self.black_color, self.container_color, self.black_color]),
                alignment=ft.alignment.center,
                border_radius=10,
                padding=0,
                height=50,
                margin=ft.margin.only(top=5),
                content=ft.Row(
                    alignment= ft.MainAxisAlignment.SPACE_AROUND,
                    controls=[
                        ft.IconButton(icon= ft.Icons.LOCATION_ON, data="1", icon_color="white", on_click=self.change_position),
                        ft.IconButton(icon= ft.Icons.ADD_CIRCLE, data="2", icon_color="white", on_click=self.change_position),
                        ft.IconButton(icon= ft.Icons.MENU, data="3", icon_color="white", on_click=self.change_position),
                    ],
                ),
            )

            # Agregar todo a la página
            self.page.add(
                ft.Column(
                    expand=True,
                    controls=[
                        ft.Stack(
                            expand=True,
                            controls=[
                                self.container_1,
                                self.container_2,
                                self.container_3,
                            ]
                        ),
                        ft.Stack(
                            height=60,
                            controls=[
                                self.nav,
                                self.selected,
                            ]
                        )
                    ]
                )
            )
            
            # Forzar la vista principal al inicio
            self.selected.offset = ft.Offset(-0.33, 0)
            self.selected.content = ft.Icon(name=ft.Icons.LOCATION_ON, size=30, color="white")
            self.container_1.offset = ft.Offset(0, 0)
            self.container_2.offset = ft.Offset(-2, -2)
            self.container_3.offset = ft.Offset(-2, -2)
            
            print("✓ Interfaz construida exitosamente")
            
        except Exception as e:
            print(f"Error en build_interface: {e}")
            import traceback
            traceback.print_exc()
            # Fallback básico
            self.page.add(ft.Text(f"Error cargando la aplicación: {str(e)}", color="white"))
    
    def show_empty_state(self):
        """Muestra la interfaz cuando no hay ciudades"""
        empty_content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.LOCATION_OFF, size=80, color=ft.Colors.WHITE54),
                ft.Text("No hay ciudades agregadas", size=24, color="white", weight=ft.FontWeight.BOLD),
                ft.Text("Agrega tu primera ciudad para ver el clima", size=16, color=ft.Colors.WHITE70),
                ft.Container(height=30),
                ft.ElevatedButton(
                    "Agregar Primera Ciudad",
                    on_click=self.add_new_city,
                    style=ft.ButtonStyle(
                        color="white",
                        bgcolor=self.accent_color,
                        padding=20
                    ),
                    icon=ft.Icons.ADD_LOCATION
                )
            ]
        )
        
        self.page.add(
            ft.Container(
                expand=True,
                content=empty_content,
                alignment=ft.alignment.center
            )
        )
    
    def build_container_1(self, current_temp, weather_desc, weather_icon):
        """Construye el contenedor 1 con funcionalidad pull to refresh"""
        # Indicador de refresh
        self.refresh_indicator_1 = ft.Container(
            height=0,
            bgcolor=self.accent_color,
            border_radius=ft.border_radius.only(top_left=10, top_right=10),
            alignment=ft.alignment.center,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.ProgressRing(width=20, height=20, stroke_width=2, color="white"),
                    ft.Text("Actualizando...", color="white", size=12)
                ]
            ),
            animate=ft.Animation(300, "easeOut")
        )
        
        return ft.Container(
            expand=True,
            border_radius=10,
            offset=ft.Offset(2,0),
            animate_offset=ft.Animation(500, ft.AnimationCurve.SLOW_MIDDLE),
            content=ft.Column(
                expand=True,
                controls=[
                    self.refresh_indicator_1,
                    ft.GestureDetector(
                        expand=True,
                        on_pan_start=self.on_pan_start_container1,
                        on_pan_update=self.on_pan_update_container1,
                        on_pan_end=self.on_pan_end_container1,
                        content=ft.Column(
                            expand=True,
                            controls=[
                                # Header con ubicación y clima actual
                                ft.Container(
                                    expand=True,
                                    border_radius=20,
                                    gradient=ft.LinearGradient(colors=[
                                        ft.Colors.with_opacity(0.1, self.container_color), 
                                        self.black_color, 
                                        ft.Colors.with_opacity(0.1, self.container_color)
                                    ]),
                                    margin=5,
                                    alignment=ft.alignment.center,
                                    content=ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(self.current_location, size=25, weight=ft.FontWeight.BOLD, color="white"),
                                        ]
                                    ),
                                ),
                                
                                # Pronóstico por horas
                                self.build_hourly_forecast(),
                                
                                # Detalles del clima
                                self.build_weather_details()
                            ]
                        )
                    )
                ]
            )
        )
    
    def build_container_2(self, current_temp, weather_desc):
        """Construye el contenedor 2 con funcionalidad pull to refresh"""
        # Indicador de refresh
        self.refresh_indicator_2 = ft.Container(
            height=0,
            bgcolor=self.accent_color,
            border_radius=ft.border_radius.only(top_left=10, top_right=10),
            alignment=ft.alignment.center,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.ProgressRing(width=20, height=20, stroke_width=2, color="white"),
                    ft.Text("Actualizando...", color="white", size=12)
                ]
            ),
            animate=ft.Animation(300, "easeOut")
        )
        
        return ft.Container(
            expand=True,
            border_radius=10,
            offset=ft.Offset(0,0),
            animate_offset=ft.Animation(500, ft.AnimationCurve.SLOW_MIDDLE),
            content=ft.Column(
                expand=True,
                controls=[
                    self.refresh_indicator_2,
                    ft.GestureDetector(
                        expand=True,
                        on_pan_start=self.on_pan_start_container2,
                        on_pan_update=self.on_pan_update_container2,
                        on_pan_end=self.on_pan_end_container2,
                        content=ft.Stack(
                            controls=[
                                ft.Image(src="weather.jpg", width=self.page.width, height=self.page.height, fit=ft.ImageFit.COVER, opacity=1),
                                ft.Image(src="snow.gif", width=self.page.width, height=self.page.height, fit=ft.ImageFit.COVER, opacity=0.1),
                                ft.Column(
                                    spacing=2,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(height=20),
                                        ft.Text(f"{self.current_location}, Chile", size=30, color="white", weight=ft.FontWeight.NORMAL, opacity=0.5),
                                        ft.Text(f"{current_temp}º", size=80, color="white", opacity=0.5),
                                        ft.Text(weather_desc, size=15, color="white", opacity=0.5),
                                        ft.Text(f"Máxima: {round(self.weather_data['daily']['temperature_2m_max'][0])}º Mínima: {round(self.weather_data['daily']['temperature_2m_min'][0])}º", 
                                               size=20, color="white", opacity=0.5),
                                    ]
                                ),
                            ]
                        )
                    )
                ]
            )
        )
    
    # Métodos para el pull to refresh
    def on_pan_start_container1(self, e: ft.DragStartEvent):
        if not self.is_refreshing:
            self.start_y = e.local_y
            self.current_y = e.local_y
            self.refresh_indicator_1.height = 0
            self.page.update()

    def on_pan_update_container1(self, e: ft.DragUpdateEvent):
        if self.is_refreshing or self.start_y is None:
            return
            
        self.current_y = e.local_y
        drag_distance = self.current_y - self.start_y
        
        if drag_distance > 0 and drag_distance <= self.refresh_threshold:
            indicator_height = min(drag_distance / 2, 60)
            self.refresh_indicator_1.height = indicator_height
            self.page.update()

    def on_pan_end_container1(self, e: ft.DragEndEvent):
        if self.is_refreshing or self.start_y is None:
            return
            
        drag_distance = self.current_y - self.start_y if self.current_y else 0
        
        if drag_distance >= self.refresh_threshold:
            self.trigger_refresh(1)
        else:
            self.refresh_indicator_1.height = 0
            self.page.update()
        
        self.start_y = None
        self.current_y = None

    def on_pan_start_container2(self, e: ft.DragStartEvent):
        if not self.is_refreshing:
            self.start_y = e.local_y
            self.current_y = e.local_y
            self.refresh_indicator_2.height = 0
            self.page.update()

    def on_pan_update_container2(self, e: ft.DragUpdateEvent):
        if self.is_refreshing or self.start_y is None:
            return
            
        self.current_y = e.local_y
        drag_distance = self.current_y - self.start_y
        
        if drag_distance > 0 and drag_distance <= self.refresh_threshold:
            indicator_height = min(drag_distance / 2, 60)
            self.refresh_indicator_2.height = indicator_height
            self.page.update()

    def on_pan_end_container2(self, e: ft.DragEndEvent):
        if self.is_refreshing or self.start_y is None:
            return
            
        drag_distance = self.current_y - self.start_y if self.current_y else 0
        
        if drag_distance >= self.refresh_threshold:
            self.trigger_refresh(2)
        else:
            self.refresh_indicator_2.height = 0
            self.page.update()
        
        self.start_y = None
        self.current_y = None

    def trigger_refresh(self, container_number):
        """Activa el refresh"""
        if self.is_refreshing:
            return
            
        self.is_refreshing = True
        print(f"Iniciando refresh para container {container_number}")
        
        # Mostrar indicador completo
        if container_number == 1:
            self.refresh_indicator_1.height = 60
        else:
            self.refresh_indicator_2.height = 60
        self.page.update()
        
        def refresh_task():
            try:
                # Simular delay de red
                time.sleep(1)
                
                # Recargar datos
                self.load_weather_data()
                
                # Actualizar la interfaz
                self.page.run_thread(self.complete_refresh)
                
            except Exception as e:
                print(f"Error en refresh: {e}")
                self.page.run_thread(self.reset_refresh_indicators)
        
        thread = threading.Thread(target=refresh_task)
        thread.daemon = True
        thread.start()

    def complete_refresh(self):
        """Completa el proceso de refresh"""
        try:
            print("Completando refresh...")
            
            # Ocultar indicadores
            self.refresh_indicator_1.height = 0
            self.refresh_indicator_2.height = 0
            
            # Actualizar toda la interfaz
            self.refresh_interface()
            
            print("Refresh completado exitosamente")
            
        except Exception as e:
            print(f"Error completando refresh: {e}")
        finally:
            self.is_refreshing = False

    def reset_refresh_indicators(self):
        """Resetea los indicadores de refresh"""
        self.refresh_indicator_1.height = 0
        self.refresh_indicator_2.height = 0
        self.is_refreshing = False
        self.page.update()

    def build_hourly_forecast(self):
        """Construye el pronóstico por horas"""
        try:
            hourly_controls = []
            hourly_data = self.weather_data['hourly']
            
            if 'time' in hourly_data:
                times = hourly_data['time']
                presipitations = hourly_data.get('precipitation_probability', [0] * len(times))
                temps = hourly_data['temperature_2m']
                weather_codes = hourly_data.get('weather_code', [1] * len(times))
                
                for i in range(min(24, len(times))):
                    hour = self.weather_service.format_time(times[i], 'hour')
                    temp = round(temps[i])
                    presipitation = presipitations[i]
                    weather_icon = self.weather_service.get_weather_icon(weather_codes[i])
                    
                    hourly_controls.append(
                        ft.Container(
                            width=60,
                            gradient=ft.LinearGradient(colors=[self.container_color, self.black_color, self.accent_color]),
                            padding=10,
                            margin=10,
                            border_radius=50,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(hour, size=12, color="white"),
                                    ft.Image(src=weather_icon, width=30, color="white"),
                                    ft.Text(f'{presipitation} %', size=12, color="white"),
                                    ft.Text(f'{temp} ºC', size=12, color="white"),
                                ]
                            )
                        )
                    )
            
            return ft.Row(
                scroll=ft.ScrollMode.AUTO,
                controls=hourly_controls
            )
        except Exception as e:
            print(f"Error en build_hourly_forecast: {e}")
            return ft.Row(controls=[ft.Text("Error cargando pronóstico", color="white")])
    
    def build_weather_details(self):
        """Construye la sección de detalles del clima"""
        try:
            current_data = self.weather_data['current']
            daily_data = self.weather_data['daily']
            
            humidity = current_data.get('relative_humidity_2m', 90)
            wind_speed = current_data.get('wind_speed_10m', 13)
            pressure = current_data.get('pressure_msl', 1013)
            precipitation = current_data.get('precipitation', 1.5)
            uv_index = daily_data.get('uv_index_max', [3])[0]
            uv_color = 'white' if uv_index < 3 else self.container_color if uv_index < 6 else 'red'
            
            return ft.Container(
                expand=5,
                margin=10,
                content=ft.Column(
                    scroll="auto",
                    expand=True,
                    controls=[
                        # Fila 1: UV y Amanecer/Atardecer
                        ft.Row(
                            controls=[
                                ft.Container(
                                    bgcolor=self.container_color,
                                    expand=True,
                                    height=100,
                                    border_radius=10,
                                    padding=10,
                                    border=ft.border.all(1, self.contorn_color),
                                    gradient=ft.SweepGradient(colors=[self.black_color, self.container_color], center=ft.alignment.top_center),
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text('Indicador ultravioleta', size=15, color="white"),
                                            ft.Text('Bajo' if uv_index < 3 else 'Moderado' if uv_index < 6 else 'Alto', size=20, color="white"),
                                            ft.Container(height=10, gradient=ft.LinearGradient(colors=[self.accent_color, uv_color]), border_radius=5),
                                        ]
                                    )
                                ),
                                ft.Container(
                                    bgcolor=self.container_color,
                                    expand=True,
                                    height=100,
                                    border_radius=10,
                                    padding=10,
                                    border=ft.border.all(1, self.contorn_color),
                                    gradient=ft.SweepGradient(colors=[self.black_color, self.container_color], center=ft.alignment.top_center),
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text('Amanecer/Atardecer', size=15, color="white"),
                                            ft.Text(self.weather_service.format_time(daily_data["sunrise"][0], 'time'), size=12, color="white"),
                                            ft.Text(f'Atardecer {self.weather_service.format_time(daily_data["sunset"][0], "time")}', size=10, color="white"),
                                        ]
                                    )
                                )
                            ]
                        ),
                        
                        # Fila 2: Viento y Lluvia
                        ft.Row(
                            controls=[
                                ft.Container(
                                    bgcolor=self.container_color,
                                    expand=True,
                                    height=100,
                                    border_radius=10,
                                    padding=10,
                                    border=ft.border.all(1, self.contorn_color),
                                    gradient=ft.SweepGradient(colors=[self.black_color, self.container_color], center=ft.alignment.top_center),
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text('Viento', size=20, color="white"),
                                            ft.Text(f'{wind_speed} km/h', size=16, color="white"),
                                        ]
                                    )
                                ),
                                ft.Container(
                                    bgcolor=self.container_color,
                                    expand=True,
                                    height=100,
                                    border_radius=10,
                                    padding=10,
                                    border=ft.border.all(1, self.contorn_color),
                                    gradient=ft.SweepGradient(colors=[self.black_color, self.container_color], center=ft.alignment.top_center),
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text('Lluvia', size=20, color="white"),
                                            ft.Text(f'{precipitation} mm', size=16, color="white"),
                                        ]
                                    )
                                )
                            ]
                        ),
                        
                        # Fila 3: Presión y Humedad
                        ft.Row(
                            controls=[
                                ft.Container(
                                    bgcolor=self.container_color,
                                    expand=True,
                                    height=100,
                                    border_radius=10,
                                    padding=10,
                                    border=ft.border.all(1, self.contorn_color),
                                    gradient=ft.SweepGradient(colors=[self.black_color, self.container_color], center=ft.alignment.top_center),
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text('Presión', size=16, color="white"),
                                            ft.Text(f'{pressure} hPa', size=14, color="white"),
                                        ]
                                    )
                                ),
                                ft.Container(
                                    bgcolor=self.container_color,
                                    expand=True,
                                    height=100,
                                    border_radius=10,
                                    padding=10,
                                    border=ft.border.all(1, self.contorn_color),
                                    gradient=ft.SweepGradient(colors=[self.black_color, self.container_color], center=ft.alignment.top_center),
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text('Humedad', size=16, color="white"),
                                            ft.Text(f'{humidity}%', size=14, color="white"),
                                        ]
                                    )
                                )
                            ]
                        )
                    ]
                )
            )
        except Exception as e:
            print(f"Error en build_weather_details: {e}")
            return ft.Container(content=ft.Text("Error cargando detalles", color="white"))
    
    def build_locations_list(self):
        """Construye la lista de ubicaciones con botón para eliminar"""
        try:
            location_containers = []
            locations = self.weather_service.get_all_locations()
            
            for i, location_name in enumerate(locations):
                location_data = self.weather_service.get_weather_data(location_name)
                current_data = location_data['current']
                
                temp = round(current_data.get('temperature_2m', 20))
                weather_code = current_data.get('weather_code', 1)
                is_day = current_data.get('is_day', 1) == 1
                weather_desc = self.weather_service.get_weather_description(weather_code)
                weather_icon = self.weather_service.get_weather_icon(weather_code, is_day)
                
                # Crear contenedor de ubicación con botón de eliminar
                location_containers.append(
                    ft.Container(
                        padding=10,
                        offset=ft.Offset(0,0),
                        animate_offset=ft.Animation(500, ft.AnimationCurve.DECELERATE),
                        border_radius=ft.border_radius.only(top_left=0, top_right=50, bottom_left=50, bottom_right=0),
                        on_click=lambda e, loc=location_name: self.select_location(loc),
                        on_hover=lambda e: self.mov_hover_direct(e.control, e.data),
                        margin=10,
                        gradient=ft.SweepGradient(colors=[self.black_color, self.container_color], center=ft.alignment.top_center),
                        content=ft.Row(
                            controls=[
                                # Información de la ciudad
                                ft.Column(
                                    expand=True,
                                    controls=[
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                            controls=[
                                                ft.Text(f'{temp} ºC', size=20, color="white"),
                                                ft.Image(src=weather_icon, width=60, color="white"),
                                            ]
                                        ),
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                            controls=[
                                                ft.Text(location_name, size=20, color="white"),
                                                ft.Text(weather_desc, size=20, color="white"),
                                            ]
                                        )
                                    ]
                                ),
                                # Botón de eliminar
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    icon_size=24,
                                    tooltip="Eliminar ciudad",
                                    on_click=lambda e, loc=location_name: self.delete_city_simple(loc),
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED_400),
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    )
                                )
                            ]
                        )
                    )
                )
            
            # Botón para agregar más ciudades
            add_city_button = ft.Container(
                padding=15,
                offset=ft.Offset(0,0),
                animate_offset=ft.Animation(500, ft.AnimationCurve.DECELERATE),
                border_radius=ft.border_radius.only(top_left=0, top_right=50, bottom_left=50, bottom_right=0),
                on_click=self.add_new_city,
                on_hover=lambda e: self.mov_hover_direct(e.control, e.data),
                margin=10,
                gradient=ft.SweepGradient(colors=[self.black_color, self.container_color], center=ft.alignment.top_center),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.ADD, size=40, color=self.accent_color),
                        ft.Text("Agregar Ciudad", size=16, color="white", weight=ft.FontWeight.BOLD),
                        ft.Text("Toca para agregar una nueva ubicación", size=12, color="white", opacity=0.8),
                    ]
                )
            )
            
            # Agregar el botón al final de la lista
            location_containers.append(add_city_button)
            
            return ft.Container(
                expand=True,
                border_radius=10,
                on_hover=lambda e: self.mov_hover_reset_all(e),
                offset=ft.Offset(-2,0),
                animate_offset=ft.Animation(500, ft.AnimationCurve.SLOW_MIDDLE),
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    controls=location_containers
                )
            )
        except Exception as e:
            print(f"Error en build_locations_list: {e}")
            return ft.Container(content=ft.Text("Error cargando ubicaciones", color="white"))
    
    def add_new_city(self, e):
        """Abre un BottomSheet para agregar una nueva ciudad con autocompletado global"""
        try:
            print("Abriendo BottomSheet para agregar ciudad con autocompletado global...")
            
            # Crear campos de entrada
            city_name_field = ft.TextField(
                label="Nombre de la ciudad, país o región",
                hint_text="Ej: Paris, Tokyo, New York, Santiago Chile...",
                border_color=self.accent_color,
                focused_border_color=self.accent_color,
                color="white",
                text_style=ft.TextStyle(color="white"),
                label_style=ft.TextStyle(color="white"),
                hint_style=ft.TextStyle(color=ft.Colors.WHITE60),
                bgcolor=ft.Colors.with_opacity(0.2, self.black_color),
                expand=True,
                on_change=self.on_city_search_change,  # Este método ya existe ahora
                autofocus=True
            )
            
            latitude_field = ft.TextField(
                label="Latitud",
                hint_text="Se completará automáticamente",
                border_color=self.accent_color,
                focused_border_color=self.accent_color,
                color="white",
                text_style=ft.TextStyle(color="white"),
                label_style=ft.TextStyle(color="white"),
                hint_style=ft.TextStyle(color=ft.Colors.WHITE60),
                bgcolor=ft.Colors.with_opacity(0.2, self.black_color),
                keyboard_type=ft.KeyboardType.NUMBER,
                expand=True,
                read_only=True
            )
            
            longitude_field = ft.TextField(
                label="Longitud",
                hint_text="Se completará automáticamente",
                border_color=self.accent_color,
                focused_border_color=self.accent_color,
                color="white",
                text_style=ft.TextStyle(color="white"),
                label_style=ft.TextStyle(color="white"),
                hint_style=ft.TextStyle(color=ft.Colors.WHITE60),
                bgcolor=ft.Colors.with_opacity(0.2, self.black_color),
                keyboard_type=ft.KeyboardType.NUMBER,
                expand=True,
                read_only=True
            )
            
            # Contenedor para sugerencias de autocompletado
            # Contenedor para sugerencias de autocompletado
            suggestions_container = ft.Container(
                content=ft.Column(
                    spacing=2,
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=200,  # Altura máxima
                visible=False,
            )
            
            # Indicador de carga
            loading_indicator = ft.Row(
                controls=[
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=self.accent_color),
                    ft.Text("Buscando ciudades...", size=12, color=ft.Colors.WHITE70)
                ],
                visible=False
            )
            
            # Guardar referencias para usar en los callbacks
            self.current_city_field = city_name_field
            self.current_lat_field = latitude_field
            self.current_lon_field = longitude_field
            self.current_suggestions = suggestions_container
            self.current_loading = loading_indicator
            
            def on_suggestion_click(city_data):
                """Cuando se selecciona una sugerencia"""
                def handler(e):
                    # Completar los campos con los datos de la ciudad seleccionada
                    city_name_field.value = city_data["name"]
                    latitude_field.value = str(city_data["latitude"])
                    longitude_field.value = str(city_data["longitude"])
                    
                    # Ocultar sugerencias
                    suggestions_container.visible = False
                    suggestions_container.content.controls.clear()
                    loading_indicator.visible = False
                    
                    self.page.update()
                
                return handler
            
            def search_cities_online(query):
                """Busca ciudades usando la API de Open-Meteo"""
                import requests
                import threading
                
                def search_task():
                    try:
                        # Mostrar indicador de carga
                        self.page.run_thread(lambda: set_loading(True))
                        
                        url = "https://geocoding-api.open-meteo.com/v1/search"
                        params = {
                            'name': query,
                            'count': 10,  # Número de resultados
                            'language': 'es',
                            'format': 'json'
                        }
                        
                        response = requests.get(url, params=params, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            results = data.get('results', [])
                            
                            # Actualizar la UI en el hilo principal
                            self.page.run_thread(lambda: display_results(results))
                        else:
                            self.page.run_thread(lambda: show_error("Error en la búsqueda"))
                            
                    except requests.exceptions.Timeout:
                        self.page.run_thread(lambda: show_error("Tiempo de espera agotado"))
                    except requests.exceptions.RequestException as e:
                        self.page.run_thread(lambda: show_error(f"Error de conexión: {e}"))
                    except Exception as e:
                        self.page.run_thread(lambda: show_error(f"Error inesperado: {e}"))
                
                def set_loading(loading):
                    """Actualiza el estado de carga"""
                    loading_indicator.visible = loading
                    if not loading:
                        suggestions_container.visible = False
                    self.page.update()
                
                def display_results(results):
                    """Muestra los resultados en la UI"""
                    suggestions_container.content.controls.clear()
                    loading_indicator.visible = False
                    
                    if results:
                        for city in results:
                            # Formatear el nombre de la ciudad
                            name = city.get('name', '')
                            country = city.get('country', '')
                            admin1 = city.get('admin1', '')  # Estado/Región
                            
                            display_name = name
                            if admin1:
                                display_name += f", {admin1}"
                            if country:
                                display_name += f", {country}"
                            
                            # Crear item de sugerencia
                            suggestion_item = ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.LOCATION_ON, size=16, color=self.accent_color),
                                    ft.Column([
                                        ft.Text(display_name, size=14, color="white", weight="bold"),
                                        ft.Text(f"Lat: {city['latitude']:.4f}, Lon: {city['longitude']:.4f}", 
                                            size=11, color=ft.Colors.WHITE70),
                                        ft.Text(f"Población: {city.get('population', 0):,}", 
                                            size=10, color=ft.Colors.WHITE60),
                                    ], spacing=0, tight=True),
                                ], spacing=10),
                                padding=10,
                                border_radius=5,
                                bgcolor=ft.Colors.with_opacity(0.1, self.container_color),
                                on_click=on_suggestion_click({
                                    "name": display_name,
                                    "latitude": city['latitude'],
                                    "longitude": city['longitude']
                                }),
                                on_hover=lambda e: self.on_suggestion_hover(e.control, e.data),
                            )
                            suggestions_container.content.controls.append(suggestion_item)
                        
                        suggestions_container.visible = True
                    else:
                        suggestions_container.visible = False
                        # Mostrar mensaje de no resultados
                        no_results = ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SEARCH_OFF, size=16, color=ft.Colors.WHITE60),
                                ft.Text("No se encontraron ciudades", size=12, color=ft.Colors.WHITE60),
                            ]),
                            padding=10,
                        )
                        suggestions_container.content.controls.append(no_results)
                        suggestions_container.visible = True
                    
                    self.page.update()
                
                def show_error(message):
                    """Muestra un mensaje de error"""
                    loading_indicator.visible = False
                    suggestions_container.content.controls.clear()
                    
                    error_item = ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ERROR, size=16, color=ft.Colors.RED_400),
                            ft.Text(message, size=12, color=ft.Colors.RED_400),
                        ]),
                        padding=10,
                    )
                    suggestions_container.content.controls.append(error_item)
                    suggestions_container.visible = True
                    
                    self.page.update()
                
                # Ejecutar la búsqueda en un hilo separado
                thread = threading.Thread(target=search_task)
                thread.daemon = True
                thread.start()
            
            def update_suggestions(query):
                """Actualiza las sugerencias de autocompletado"""
                query = query.strip()
                
                if not query or len(query) < 2:
                    suggestions_container.visible = False
                    loading_indicator.visible = False
                    suggestions_container.content.controls.clear()
                    self.page.update()
                    return
                
                # Buscar ciudades online
                search_cities_online(query)
            
            # Asignar la función de actualización al campo de ciudad
            self.current_city_update_fn = update_suggestions
            
            # Función para guardar la ciudad
            def save_city(e):
                """Función para guardar la ciudad"""
                try:
                    city_name = city_name_field.value.strip()
                    lat = latitude_field.value.strip()
                    lon = longitude_field.value.strip()
                    
                    if not city_name:
                        self.show_snackbar("Por favor ingresa un nombre de ciudad")
                        return
                        
                    if not lat or not lon:
                        self.show_snackbar("Por favor completa las coordenadas")
                        return
                        
                    try:
                        lat_float = float(lat)
                        lon_float = float(lon)
                    except ValueError:
                        self.show_snackbar("Las coordenadas deben ser números válidos")
                        return
                    
                    # Validar rangos de coordenadas
                    if not (-90 <= lat_float <= 90):
                        self.show_snackbar("La latitud debe estar entre -90 y 90")
                        return
                        
                    if not (-180 <= lon_float <= 180):
                        self.show_snackbar("La longitud debe estar entre -180 y 180")
                        return
                    
                    # Usar solo el primer nombre para la clave (evitar nombres muy largos)
                    simple_name = city_name.split(',')[0].strip()
                    
                    # Agregar la nueva ciudad usando el método del servicio que guarda en la BD
                    success = self.weather_service.add_location(simple_name, lat_float, lon_float)
                    
                    if success:
                        print(f"Ciudad {simple_name} agregada al servicio y base de datos")
                        
                        # Cerrar el BottomSheet
                        self.close_bottomsheet()
                        
                        # Mostrar mensaje de éxito
                        self.show_snackbar(f"¡{simple_name} agregada correctamente!")
                        
                        # Actualizar la interfaz después de un pequeño delay
                        import threading
                        def refresh_after_delay():
                            import time
                            time.sleep(0.5)
                            self.page.run_thread(self.refresh_interface)
                        
                        thread = threading.Thread(target=refresh_after_delay)
                        thread.daemon = True
                        thread.start()
                    else:
                        self.show_snackbar("Error: La ciudad ya existe o no se pudo guardar")
                            
                except Exception as ex:
                    print(f"Error en save_city: {ex}")
                    import traceback
                    traceback.print_exc()
                    self.show_snackbar("Error al guardar la ciudad")
            
            def close_bottomsheet(e):
                """Función para cerrar el bottomsheet"""
                self.close_bottomsheet()
            
            # Crear el BottomSheet
            bottomsheet_content = ft.Container(
                width=500,
                height=500,
                padding=25,
                bgcolor=self.container_color,
                border_radius=ft.border_radius.only(top_left=20, top_right=20),
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=15,
                    controls=[
                        # Header
                        ft.Row([
                            ft.Icon(ft.Icons.SEARCH, color=self.accent_color, size=28),
                            ft.Text("Buscar Ciudad en el Mundo", 
                                size=22, 
                                color="white", 
                                weight=ft.FontWeight.BOLD,
                                expand=True),
                        ]),
                        
                        ft.Divider(color=ft.Colors.WHITE24, height=1),
                        
                        # Campo de búsqueda
                        city_name_field,
                        
                        # Indicador de carga
                        loading_indicator,
                        
                        # Sugerencias de autocompletado
                        suggestions_container,
                        
                        # Campos de coordenadas (solo lectura)
                        ft.Row([
                            latitude_field,
                            longitude_field,
                        ], spacing=10),
                        
                        # Información
                        ft.Container(
                            padding=10,
                            bgcolor=ft.Colors.with_opacity(0.2, self.black_color),
                            border_radius=8,
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.PUBLIC, color=self.accent_color, size=16),
                                    ft.Text("Búsqueda Global", size=14, color="white", weight="bold"),
                                ]),
                                ft.Text(
                                    "• Busca cualquier ciudad del mundo\n"
                                    "• Escribe al menos 2 caracteres\n"
                                    "• Los resultados incluyen país y región\n"
                                    "• Las coordenadas se completan automáticamente",
                                    size=12,
                                    color=ft.Colors.WHITE70
                                )
                            ], spacing=8)
                        ),
                        
                        # Botones
                        ft.Row([
                            ft.OutlinedButton(
                                "Cancelar",
                                on_click=close_bottomsheet,
                                style=ft.ButtonStyle(
                                    color="white",
                                    side=ft.BorderSide(1, self.accent_color)
                                ),
                                expand=True
                            ),
                            ft.ElevatedButton(
                                "Agregar Ciudad",
                                on_click=save_city,
                                style=ft.ButtonStyle(
                                    color="white",
                                    bgcolor=self.accent_color,
                                    padding=15
                                ),
                                expand=True
                            ),
                        ], spacing=10)
                    ]
                )
            )
            
            bottomsheet = ft.BottomSheet(
                bottomsheet_content,
                open=True,
                dismissible=True,
                enable_drag=True,
                show_drag_handle=True,
                maintain_bottom_view_insets_padding=True
            )
            
            # Guardar referencia al bottomsheet
            self.current_bottomsheet = bottomsheet
            
            # Añadir el BottomSheet al overlay
            self.page.overlay.append(bottomsheet)
            self.page.update()
            print("BottomSheet de búsqueda global abierto")
            
        except Exception as ex:
            print(f"Error al abrir BottomSheet: {ex}")
            import traceback
            traceback.print_exc()

    def on_city_search_change(self, e):
        """Maneja el cambio en el campo de búsqueda de ciudades"""
        try:
            if hasattr(self, 'current_city_update_fn'):
                query = e.control.value.strip()
                # Solo buscar si hay al menos 2 caracteres
                if len(query) >= 2:
                    self.current_city_update_fn(query)
                else:
                    # Limpiar sugerencias si hay menos de 2 caracteres
                    if hasattr(self, 'current_suggestions'):
                        self.current_suggestions.visible = False
                        self.current_suggestions.controls.clear()
                    if hasattr(self, 'current_loading'):
                        self.current_loading.visible = False
                    self.page.update()
        except Exception as ex:
            print(f"Error en on_city_search_change: {ex}")

    def on_suggestion_hover(self, control, hover_data):
        """Maneja el hover en las sugerencias"""
        try:
            if hover_data == "true":
                control.bgcolor = ft.Colors.with_opacity(0.2, self.accent_color)
            else:
                control.bgcolor = ft.Colors.with_opacity(0.1, self.container_color)
            self.page.update()
        except Exception as ex:
            print(f"Error en on_suggestion_hover: {ex}")
    
    def close_bottomsheet(self):
        """Cierra el BottomSheet actual"""
        try:
            if hasattr(self, 'current_bottomsheet') and self.current_bottomsheet:
                # Remover el bottomsheet específico
                if self.current_bottomsheet in self.page.overlay:
                    self.page.overlay.remove(self.current_bottomsheet)
                self.current_bottomsheet = None
            else:
                # Limpiar todos los overlays como fallback
                self.page.overlay.clear()
            
            self.page.update()
            print("BottomSheet cerrado")
        except Exception as ex:
            print(f"Error cerrando BottomSheet: {ex}")
            # Fallback: limpiar todo
            try:
                self.page.overlay.clear()
                self.page.update()
            except:
                pass

    def save_new_city(self, city_name, latitude, longitude, dialog=None):
        """Guarda la nueva ciudad y actualiza la interfaz"""
        try:
            if not city_name or not latitude or not longitude:
                self.show_snackbar("Por favor completa todos los campos")
                return
                
            try:
                lat = float(latitude)
                lon = float(longitude)
            except ValueError:
                self.show_snackbar("Las coordenadas deben ser números válidos")
                return
            
            # Agregar la nueva ciudad al servicio
            self.weather_service.locations[city_name] = {"lat": lat, "lon": lon}
            
            # Cerrar el diálogo
            if dialog:
                dialog.open = False
            else:
                self.close_dialog(None)
            
            # Mostrar mensaje de éxito
            self.show_snackbar(f"¡{city_name} agregada correctamente!")
            
            # Actualizar la lista de ubicaciones
            self.refresh_interface()
            
        except Exception as ex:
            print(f"Error al guardar nueva ciudad: {ex}")
            self.show_snackbar("Error al agregar la ciudad")

    def delete_city_simple(self, city_name):
        """Versión simplificada para eliminar ciudades"""
        try:
            print(f"Eliminando ciudad: {city_name}")
            
            success = self.weather_service.delete_location(city_name)
            
            if success:
                print(f"Ciudad {city_name} eliminada")
                self.show_snackbar(f"¡{city_name} eliminada!")
                
                # Verificar si todavía hay ciudades disponibles
                available_cities = self.weather_service.get_all_locations()
                
                if available_cities:
                    # Obtener la última ciudad seleccionada (puede haber cambiado después de eliminar)
                    last_city = self.weather_service.get_last_selected_city()
                    
                    if last_city and last_city in available_cities:
                        # Usar la última ciudad seleccionada
                        self.current_location = last_city
                    else:
                        # Usar la primera ciudad disponible
                        self.current_location = available_cities[0]
                        # Guardar como última seleccionada
                        self.weather_service.set_last_selected_city(self.current_location)
                    
                    self.load_weather_data(self.current_location)
                else:
                    # No hay ciudades, mostrar estado vacío
                    self.current_location = None
                    self.weather_data = self.weather_service.get_default_data()
                
                self.refresh_interface()
            else:
                self.show_snackbar("Error al eliminar la ciudad")
                
        except Exception as ex:
            print(f"Error: {ex}")
            self.show_snackbar("Error al eliminar")
    
    def close_dialog(self, dialog):
        """Cierra el diálogo actual"""
        try:
            if dialog:
                dialog.open = False
            elif self.page.dialog:
                self.page.dialog.open = False
            self.page.update()
        except Exception as ex:
            print(f"Error al cerrar diálogo: {ex}")

    def show_snackbar(self, message):
        """Muestra un mensaje snackbar"""
        try:
            # Primero limpiar cualquier snackbar existente
            if hasattr(self.page, 'snack_bar'):
                self.page.snack_bar.open = False
            
            snackbar = ft.SnackBar(
                content=ft.Text(message, color="white", size=14),
                bgcolor=self.accent_color,
                duration=3000,
                behavior=ft.SnackBarBehavior.FLOATING,
                margin=10,
                shape=ft.RoundedRectangleBorder(radius=10),
                show_close_icon=True,
                close_icon_color="white"
            )
            
            self.page.snack_bar = snackbar
            snackbar.open = True
            self.page.update()
        except Exception as ex:
            print(f"Error al mostrar snackbar: {ex}")
    
    def debug_cities(self):
        """Método de debug para verificar el estado de las ciudades"""
        print("=== DEBUG DE CIUDADES ===")
        print(f"Ciudad actual: {self.current_location}")
        print(f"Total de ciudades en servicio: {len(self.weather_service.locations)}")
        print(f"Ciudades disponibles: {list(self.weather_service.locations.keys())}")
        
        # Debug más detallado del servicio
        if hasattr(self.weather_service, 'db_manager'):
            try:
                db_cities = self.weather_service.db_manager.get_all_cities()
                print(f"Ciudades en base de datos: {len(db_cities)}")
                for city in db_cities:
                    print(f"  - {city['name']}: ({city['lat']}, {city['lon']})")
            except Exception as e:
                print(f"Error al obtener ciudades de BD: {e}")
        print("=========================")
    
    def select_location(self, location_name):
        """Selecciona una ubicación y actualiza la interfaz"""
        try:
            self.selected.offset = ft.Offset(-0.33, 0)
            self.selected.content = ft.Icon(name=ft.Icons.LOCATION_ON, size=30, color="white")
            self.container_1.offset = ft.Offset(0, 0)
            self.container_2.offset = ft.Offset(-2, -2)
            self.container_3.offset = ft.Offset(-2, -2)

            self.weather_service.set_last_selected_city(location_name)
            
            self.load_weather_data(location_name)
            self.refresh_interface()
        except Exception as e:
            print(f"Error en select_location: {e}")

    def mov_hover_direct(self, control, hover_data):
        """Maneja el hover directamente en el control"""
        try:
            if hover_data == "true":
                control.offset = ft.Offset(-0.05, -0.05)
            else:
                control.offset = ft.Offset(0, 0)
            self.page.update()
        except Exception as e:
            print(f"Error en mov_hover_direct: {e}")

    def mov_hover_reset_all(self, e):
        """Resetea todos los controles cuando el mouse sale del contenedor principal"""
        try:
            if e.data == "false":
                if hasattr(self, 'container_3') and self.container_3.content.controls:
                    for control in self.container_3.content.controls:
                        control.offset = ft.Offset(0, 0)
                    self.page.update()
        except Exception as e:
            print(f"Error en mov_hover_reset_all: {e}")

    def change_position(self, e):
        """Cambia entre las diferentes vistas"""
        try:
            if e.control.data == "1":
                self.selected.offset = ft.Offset(-0.33, 0)
                self.selected.content = ft.Icon(name=ft.Icons.LOCATION_ON, size=30, color="white")
                self.container_1.offset = ft.Offset(0, 0)
                self.container_2.offset = ft.Offset(-2, -2)
                self.container_3.offset = ft.Offset(-2, -2)
            elif e.control.data == "2":
                self.selected.offset = ft.Offset(0, 0)
                self.selected.content = ft.Icon(name=ft.Icons.ADD_CIRCLE, size=30, color="white")
                self.container_1.offset = ft.Offset(-2, -2)
                self.container_2.offset = ft.Offset(0, 0)
                self.container_3.offset = ft.Offset(-2, -2)
            elif e.control.data == "3":
                self.selected.offset = ft.Offset(0.33, 0)
                self.selected.content = ft.Icon(name=ft.Icons.MENU, size=30, color="white")
                self.container_1.offset = ft.Offset(-2, -2)
                self.container_2.offset = ft.Offset(-2, -2)
                self.container_3.offset = ft.Offset(0, 0)
            self.page.update()
        except Exception as e:
            print(f"Error en change_position: {e}")

    def on_app_close(self):
        """Maneja el cierre de la aplicación"""
        print("🛑 Cerrando aplicación...")
        self.stop_auto_refresh()
        stop_widget_service()


def main(page: ft.Page):
    app = WeatherApp(page)
    page.on_close = app.on_app_close

if __name__ == "__main__":
    ft.app(target=main)