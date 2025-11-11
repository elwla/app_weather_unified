import sqlite3
import os
import json
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_name="weather_app.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas si no existen"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Crear tabla de ciudades
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Crear tabla de configuración para guardar la última ciudad
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_selected_city TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insertar configuración por defecto si no existe
            cursor.execute('''
                INSERT OR IGNORE INTO app_config (id, last_selected_city) 
                VALUES (1, NULL)
            ''')
            
            conn.commit()
            conn.close()
            print("Base de datos inicializada correctamente")
            
        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}")
    
    def get_all_cities(self) -> List[Dict]:
        """Obtiene todas las ciudades de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, latitude, longitude FROM cities 
                ORDER BY name
            ''')
            
            cities = []
            for row in cursor.fetchall():
                cities.append({
                    "name": row[0],
                    "lat": row[1],
                    "lon": row[2]
                })
            
            conn.close()
            return cities
            
        except Exception as e:
            print(f"Error al obtener ciudades: {e}")
            return []
    
    def add_city(self, name: str, latitude: float, longitude: float) -> bool:
        """Agrega una nueva ciudad a la base de datos"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO cities (name, latitude, longitude) 
                VALUES (?, ?, ?)
            ''', (name, latitude, longitude))
            
            conn.commit()
            conn.close()
            print(f"Ciudad {name} agregada a la base de datos")
            return True
            
        except sqlite3.IntegrityError:
            print(f"La ciudad {name} ya existe en la base de datos")
            return False
        except Exception as e:
            print(f"Error al agregar ciudad: {e}")
            return False
    
    def delete_city(self, name: str) -> bool:
        """Elimina una ciudad de la base de datos"""
        try:
            print(f"Eliminando ciudad de BD: {name}")
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Primero verificar si es la última ciudad seleccionada
            cursor.execute('SELECT last_selected_city FROM app_config WHERE id = 1')
            last_city = cursor.fetchone()
            
            cursor.execute('DELETE FROM cities WHERE name = ?', (name,))
            
            # Si la ciudad eliminada era la última seleccionada, limpiar la configuración
            if last_city and last_city[0] == name:
                cursor.execute('UPDATE app_config SET last_selected_city = NULL WHERE id = 1')
            
            conn.commit()
            conn.close()
            
            if cursor.rowcount > 0:
                print(f"Ciudad {name} eliminada de la base de datos")
                return True
            else:
                print(f"Ciudad {name} no encontrada en la base de datos")
                return False
                
        except Exception as e:
            print(f"Error al eliminar ciudad: {e}")
            return False
    
    def get_last_selected_city(self) -> Optional[str]:
        """Obtiene la última ciudad seleccionada por el usuario"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT last_selected_city FROM app_config WHERE id = 1')
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[0]:
                print(f"Última ciudad seleccionada encontrada en BD: {result[0]}")
                return result[0]
            else:
                print("No hay última ciudad seleccionada en la BD")
                return None
                
        except Exception as e:
            print(f"Error al obtener última ciudad: {e}")
            return None
    
    def set_last_selected_city(self, city_name: str) -> bool:
        """Guarda la última ciudad seleccionada por el usuario"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Verificar que la ciudad existe (pero permitir guardar incluso si no existe aún)
            cursor.execute('SELECT 1 FROM cities WHERE name = ?', (city_name,))
            city_exists = cursor.fetchone() is not None
            
            if not city_exists:
                print(f"Advertencia: La ciudad {city_name} no existe en cities, pero se guardará igual")
            
            cursor.execute('''
                UPDATE app_config 
                SET last_selected_city = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = 1
            ''', (city_name,))
            
            conn.commit()
            conn.close()
            
            print(f"Última ciudad seleccionada guardada en BD: {city_name}")
            return True
            
        except Exception as e:
            print(f"Error al guardar última ciudad: {e}")
            return False
    
    def city_exists(self, name: str) -> bool:
        """Verifica si una ciudad existe en la base de datos"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT 1 FROM cities WHERE name = ?', (name,))
            exists = cursor.fetchone() is not None
            
            conn.close()
            return exists
            
        except Exception as e:
            print(f"Error al verificar ciudad: {e}")
            return False
    
    def update_city(self, old_name: str, new_name: str, latitude: float, longitude: float) -> bool:
        """Actualiza los datos de una ciudad"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE cities 
                SET name = ?, latitude = ?, longitude = ? 
                WHERE name = ?
            ''', (new_name, latitude, longitude, old_name))
            
            # Si se actualizó el nombre, actualizar también en la configuración si era la última seleccionada
            if old_name != new_name:
                cursor.execute('''
                    UPDATE app_config 
                    SET last_selected_city = ? 
                    WHERE last_selected_city = ? AND id = 1
                ''', (new_name, old_name))
            
            conn.commit()
            conn.close()
            
            if cursor.rowcount > 0:
                print(f"Ciudad {old_name} actualizada a {new_name}")
                return True
            else:
                print(f"Ciudad {old_name} no encontrada")
                return False
                
        except Exception as e:
            print(f"Error al actualizar ciudad: {e}")
            return False