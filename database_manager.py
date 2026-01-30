"""
Gestor de Base de Datos para el Agente de Automatización SQL
"""
import mysql.connector
from mysql.connector import Error
import logging
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import shutil
import subprocess

from config import db_config

class DatabaseManager:
    """Gestor principal para operaciones de base de datos"""
    
    def __init__(self, config=None):
        self.config = config or db_config
        self.logger = logging.getLogger(__name__)
        self._connection_pool = None
        
    def _create_connection_pool(self):
        """Crea un pool de conexiones para mejor rendimiento"""
        try:
            pool_config = {
                'pool_name': 'sql_agent_pool',
                'pool_size': 10,
                'pool_reset_session': True,
                'host': self.config.host,
                'port': self.config.port,
                'user': self.config.username,
                'password': self.config.password,
                'database': self.config.database,
                'charset': self.config.charset,
                'autocommit': True
            }
            self._connection_pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
            self.logger.info("Pool de conexiones creado exitosamente")
        except Error as e:
            self.logger.error(f"Error creando pool de conexiones: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager para obtener conexiones del pool"""
        if not self._connection_pool:
            self._create_connection_pool()
        
        connection = None
        try:
            connection = self._connection_pool.get_connection()
            yield connection
        except Error as e:
            self.logger.error(f"Error en conexión a base de datos: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def execute_query(self, query: str, params: Tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """Ejecuta una consulta SQL y retorna los resultados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True, buffered=True)
                cursor.execute(query, params or ())
                
                if fetch:
                    results = cursor.fetchall()
                    cursor.close()
                    return results
                else:
                    conn.commit()
                    cursor.close()
                    return None
                    
        except Error as e:
            self.logger.error(f"Error ejecutando consulta: {e}")
            self.logger.error(f"Query: {query}")
            raise
    
    def execute_batch(self, query: str, data: List[Tuple]) -> bool:
        """Ejecuta una consulta en lote para múltiples registros"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(buffered=True)
                cursor.executemany(query, data)
                conn.commit()
                cursor.close()
                return True
        except Error as e:
            self.logger.error(f"Error en ejecución batch: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Obtiene información detallada de una tabla"""
        queries = {
            'columns': f"DESCRIBE {table_name}",
            'row_count': f"SELECT COUNT(*) as count FROM {table_name}",
            'size': f"""
                SELECT 
                    table_name,
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.tables 
                WHERE table_schema = '{self.config.database}' 
                AND table_name = '{table_name}'
            """
        }
        
        result = {}
        for key, query in queries.items():
            try:
                result[key] = self.execute_query(query)
            except Error as e:
                self.logger.warning(f"No se pudo obtener {key} para tabla {table_name}: {e}")
                result[key] = None
        
        return result
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas importantes de la base de datos"""
        metrics_queries = {
            'connection_count': "SHOW STATUS LIKE 'Threads_connected'",
            'uptime': "SHOW STATUS LIKE 'Uptime'",
            'queries_per_second': "SHOW STATUS LIKE 'Queries'",
            'slow_queries': "SHOW STATUS LIKE 'Slow_queries'",
            'table_locks': "SHOW STATUS LIKE 'Table_locks_waited'",
            'innodb_buffer_pool': """
                SELECT 
                    VARIABLE_NAME, 
                    VARIABLE_VALUE 
                FROM performance_schema.global_status 
                WHERE VARIABLE_NAME IN (
                    'Innodb_buffer_pool_pages_total',
                    'Innodb_buffer_pool_pages_free',
                    'Innodb_buffer_pool_pages_dirty'
                )
            """,
            'database_size': f"""
                SELECT 
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables 
                WHERE table_schema = '{self.config.database}'
            """
        }
        
        metrics = {}
        for metric_name, query in metrics_queries.items():
            try:
                result = self.execute_query(query)
                metrics[metric_name] = result
            except Error as e:
                self.logger.warning(f"No se pudo obtener métrica {metric_name}: {e}")
                metrics[metric_name] = None
        
        # Agregar timestamp
        metrics['timestamp'] = datetime.now().isoformat()
        return metrics
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Obtiene las consultas más lentas del log de consultas lentas"""
        query = """
            SELECT 
                sql_text,
                exec_count,
                avg_timer_wait/1000000000 as avg_time_seconds,
                sum_timer_wait/1000000000 as total_time_seconds,
                sum_rows_examined,
                sum_rows_sent,
                first_seen,
                last_seen
            FROM performance_schema.events_statements_summary_by_digest 
            WHERE schema_name = %s
            ORDER BY avg_timer_wait DESC 
            LIMIT %s
        """
        
        try:
            return self.execute_query(query, (self.config.database, limit))
        except Error as e:
            self.logger.warning(f"No se pudieron obtener consultas lentas: {e}")
            return []
    
    def optimize_tables(self) -> Dict[str, bool]:
        """Optimiza todas las tablas de la base de datos"""
        # Obtener lista de tablas
        tables_query = f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{self.config.database}' 
            AND table_type = 'BASE TABLE'
        """
        
        tables = self.execute_query(tables_query)
        results = {}
        
        for table in tables:
            table_name = table['table_name']
            try:
                self.execute_query(f"OPTIMIZE TABLE {table_name}", fetch=False)
                results[table_name] = True
                self.logger.info(f"Tabla {table_name} optimizada exitosamente")
            except Error as e:
                results[table_name] = False
                self.logger.error(f"Error optimizando tabla {table_name}: {e}")
        
        return results

    def _get_mysqldump_path(self) -> str:
        """Intenta localizar el ejecutable mysqldump en el sistema"""
        # 1. Verificar si está en el PATH del sistema
        if shutil.which('mysqldump'):
            return 'mysqldump'
        
        # 2. Buscar en rutas comunes de Windows
        common_paths = [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqldump.exe",
            r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
            r"C:\xampp\mysql\bin\mysqldump.exe",
            r"C:\wamp64\bin\mysql\mysql8.0.21\bin\mysqldump.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                self.logger.info(f"mysqldump encontrado en: {path}")
                return path
        
        # Fallback
        return 'mysqldump'

    def backup_database(self, backup_path: str) -> bool:
        """Crea un backup de la base de datos usando mysqldump"""
        
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Obtener ruta de mysqldump
            mysqldump_cmd = self._get_mysqldump_path()
            
            # Comando mysqldump
            cmd = [
                mysqldump_cmd,
                f'--host={self.config.host}',
                f'--port={self.config.port}',
                f'--user={self.config.username}',
                f'--password={self.config.password}',
                '--single-transaction',
                '--routines',
                '--triggers',
                self.config.database
            ]
            
            # Ejecutar backup
            with open(backup_path, 'w') as backup_file:
                result = subprocess.run(cmd, stdout=backup_file, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Backup creado exitosamente: {backup_path}")
                return True
            else:
                self.logger.error(f"Error en backup: {result.stderr}")
                # Si falla por comando no encontrado, dar un mensaje más claro
                if "IsNotRecognized" in str(result.stderr) or result.returncode == 9009:
                    self.logger.error("No se encontró mysqldump. Asegúrate de instalar MySQL Server o añadirlo al PATH.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            if isinstance(e, FileNotFoundError):
                 self.logger.error("Error crítico: No se encuentra el ejecutable 'mysqldump'. Verifica la instalación de MySQL.")
            return False
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(buffered=True)
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True
        except Error as e:
            self.logger.error(f"Error en prueba de conexión: {e}")
            return False
    
    def close_pool(self):
        """Cierra el pool de conexiones"""
        if self._connection_pool:
            try:
                # MySQL Connector no tiene método directo para cerrar el pool
                # pero podemos limpiar las referencias
                self._connection_pool = None
                self.logger.info("Pool de conexiones cerrado")
            except Exception as e:
                self.logger.error(f"Error cerrando pool: {e}")