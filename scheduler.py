"""
Sistema de Programación de Tareas para el Agente SQL
"""
import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import json
import os

from database_manager import DatabaseManager
from report_generator import ReportGenerator
from monitoring_system import MonitoringSystem
from config import automation_config

@dataclass
class ScheduledTask:
    """Representa una tarea programada"""
    id: str
    name: str
    function: Callable
    schedule_type: str  # 'interval', 'daily', 'weekly', 'monthly'
    schedule_value: Any  # intervalo en segundos, hora del día, etc.
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None

class TaskScheduler:
    """Programador de tareas automáticas"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = automation_config
        self.logger = logging.getLogger(__name__)
        
        # Componentes del sistema
        self.report_generator = ReportGenerator(db_manager)
        self.monitoring_system = MonitoringSystem(db_manager)
        
        # Control del scheduler
        self.scheduler_active = False
        self.scheduler_thread = None
        
        # Registro de tareas
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        
        # Configurar tareas por defecto
        self._setup_default_tasks()
    
    def _setup_default_tasks(self):
        """Configura las tareas automáticas por defecto"""
        
        # Reporte de salud diario
        if self.config.reports_enabled:
            self.add_task(
                task_id="daily_health_report",
                name="Reporte Diario de Salud",
                function=self._generate_health_report,
                schedule_type="daily",
                schedule_value="08:00"  # 8:00 AM
            )
            
            # Reporte de rendimiento semanal
            self.add_task(
                task_id="weekly_performance_report",
                name="Reporte Semanal de Rendimiento",
                function=self._generate_performance_report,
                schedule_type="weekly",
                schedule_value="monday"
            )
        
        # Backup automático
        if self.config.backup_enabled:
            if self.config.backup_schedule == "daily":
                self.add_task(
                    task_id="daily_backup",
                    name="Backup Diario",
                    function=self._perform_backup,
                    schedule_type="daily",
                    schedule_value="02:00"  # 2:00 AM
                )
            elif self.config.backup_schedule == "weekly":
                self.add_task(
                    task_id="weekly_backup",
                    name="Backup Semanal",
                    function=self._perform_backup,
                    schedule_type="weekly",
                    schedule_value="sunday"
                )
        
        # Optimización de tablas
        self.add_task(
            task_id="weekly_optimization",
            name="Optimización Semanal de Tablas",
            function=self._optimize_tables,
            schedule_type="weekly",
            schedule_value="sunday"
        )
        
        # Limpieza de archivos antiguos
        self.add_task(
            task_id="cleanup_old_files",
            name="Limpieza de Archivos Antiguos",
            function=self._cleanup_old_files,
            schedule_type="daily",
            schedule_value="03:00"  # 3:00 AM
        )
        
        # Verificación de conexión
        self.add_task(
            task_id="connection_check",
            name="Verificación de Conexión",
            function=self._check_database_connection,
            schedule_type="interval",
            schedule_value=300  # Cada 5 minutos
        )
    
    def add_task(self, task_id: str, name: str, function: Callable, 
                 schedule_type: str, schedule_value: Any, enabled: bool = True) -> bool:
        """Añade una nueva tarea programada"""
        
        if task_id in self.scheduled_tasks:
            self.logger.warning(f"La tarea {task_id} ya existe")
            return False
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            function=function,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            enabled=enabled
        )
        
        self.scheduled_tasks[task_id] = task
        
        # Programar la tarea
        if enabled:
            self._schedule_task(task)
        
        self.logger.info(f"Tarea añadida: {name} ({task_id})")
        return True
    
    def remove_task(self, task_id: str) -> bool:
        """Elimina una tarea programada"""
        if task_id not in self.scheduled_tasks:
            self.logger.warning(f"La tarea {task_id} no existe")
            return False
        
        # Cancelar la tarea en schedule
        schedule.clear(task_id)
        
        # Eliminar del registro
        del self.scheduled_tasks[task_id]
        
        self.logger.info(f"Tarea eliminada: {task_id}")
        return True
    
    def enable_task(self, task_id: str) -> bool:
        """Habilita una tarea"""
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        task.enabled = True
        self._schedule_task(task)
        
        self.logger.info(f"Tarea habilitada: {task_id}")
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """Deshabilita una tarea"""
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        task.enabled = False
        
        # Cancelar en schedule
        schedule.clear(task_id)
        
        self.logger.info(f"Tarea deshabilitada: {task_id}")
        return True
    
    def _schedule_task(self, task: ScheduledTask):
        """Programa una tarea individual en el scheduler"""
        
        def wrapped_function():
            self._execute_task(task)
        
        if task.schedule_type == "interval":
            schedule.every(task.schedule_value).seconds.do(wrapped_function).tag(task.id)
        
        elif task.schedule_type == "daily":
            schedule.every().day.at(task.schedule_value).do(wrapped_function).tag(task.id)
        
        elif task.schedule_type == "weekly":
            if task.schedule_value.lower() == "monday":
                schedule.every().monday.do(wrapped_function).tag(task.id)
            elif task.schedule_value.lower() == "tuesday":
                schedule.every().tuesday.do(wrapped_function).tag(task.id)
            elif task.schedule_value.lower() == "wednesday":
                schedule.every().wednesday.do(wrapped_function).tag(task.id)
            elif task.schedule_value.lower() == "thursday":
                schedule.every().thursday.do(wrapped_function).tag(task.id)
            elif task.schedule_value.lower() == "friday":
                schedule.every().friday.do(wrapped_function).tag(task.id)
            elif task.schedule_value.lower() == "saturday":
                schedule.every().saturday.do(wrapped_function).tag(task.id)
            elif task.schedule_value.lower() == "sunday":
                schedule.every().sunday.do(wrapped_function).tag(task.id)
        
        elif task.schedule_type == "monthly":
            # Para tareas mensuales, usamos un enfoque diferente
            schedule.every().day.do(self._check_monthly_task, task).tag(task.id)
    
    def _check_monthly_task(self, task: ScheduledTask):
        """Verifica si una tarea mensual debe ejecutarse"""
        now = datetime.now()
        
        # Ejecutar el primer día del mes
        if now.day == 1:
            if not task.last_run or task.last_run.month != now.month:
                self._execute_task(task)
    
    def _execute_task(self, task: ScheduledTask):
        """Ejecuta una tarea y maneja errores"""
        try:
            self.logger.info(f"Ejecutando tarea: {task.name}")
            
            # Actualizar información de ejecución
            task.last_run = datetime.now()
            task.run_count += 1
            
            # Ejecutar la función
            result = task.function()
            
            # Log del resultado
            if result is not None:
                self.logger.info(f"Tarea {task.name} completada. Resultado: {result}")
            else:
                self.logger.info(f"Tarea {task.name} completada exitosamente")
            
            # Limpiar error anterior si existía
            task.last_error = None
            
        except Exception as e:
            task.error_count += 1
            task.last_error = str(e)
            
            self.logger.error(f"Error ejecutando tarea {task.name}: {e}")
            
            # Si hay demasiados errores, deshabilitar la tarea
            if task.error_count >= 5:
                self.logger.error(f"Deshabilitando tarea {task.name} por exceso de errores")
                self.disable_task(task.id)
    
    def start_scheduler(self):
        """Inicia el programador de tareas"""
        if self.scheduler_active:
            self.logger.warning("El programador ya está activo")
            return
        
        self.scheduler_active = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # Iniciar monitoreo si está habilitado
        if self.config.monitoring_enabled:
            self.monitoring_system.start_monitoring()
        
        self.logger.info("Programador de tareas iniciado")
    
    def stop_scheduler(self):
        """Detiene el programador de tareas"""
        self.scheduler_active = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # Detener monitoreo
        self.monitoring_system.stop_monitoring()
        
        self.logger.info("Programador de tareas detenido")
    
    def _scheduler_loop(self):
        """Bucle principal del programador"""
        while self.scheduler_active:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error en bucle del programador: {e}")
                time.sleep(10)
    
    def get_task_status(self) -> Dict[str, Any]:
        """Obtiene el estado de todas las tareas"""
        status = {
            'scheduler_active': self.scheduler_active,
            'total_tasks': len(self.scheduled_tasks),
            'enabled_tasks': sum(1 for task in self.scheduled_tasks.values() if task.enabled),
            'tasks': []
        }
        
        for task in self.scheduled_tasks.values():
            task_info = {
                'id': task.id,
                'name': task.name,
                'enabled': task.enabled,
                'schedule_type': task.schedule_type,
                'schedule_value': task.schedule_value,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'run_count': task.run_count,
                'error_count': task.error_count,
                'last_error': task.last_error
            }
            status['tasks'].append(task_info)
        
        return status
    
    def export_task_log(self, filepath: str):
        """Exporta el log de tareas a un archivo"""
        log_data = {
            'export_timestamp': datetime.now().isoformat(),
            'scheduler_status': self.get_task_status()
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.logger.info(f"Log de tareas exportado a: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando log de tareas: {e}")
            return False
    
    # Funciones de tareas específicas
    def _generate_health_report(self):
        """Genera reporte de salud de la base de datos"""
        try:
            return self.report_generator.generate_database_health_report()
        except Exception as e:
            self.logger.error(f"Error generando reporte de salud: {e}")
            raise
    
    def _generate_performance_report(self):
        """Genera reporte de rendimiento"""
        try:
            return self.report_generator.generate_performance_report(7)
        except Exception as e:
            self.logger.error(f"Error generando reporte de rendimiento: {e}")
            raise
    
    def _perform_backup(self):
        """Realiza backup de la base de datos"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{self.db_manager.config.database}_{timestamp}.sql"
            backup_path = os.path.join(self.config.backup_dir, backup_filename)
            
            # Crear directorio si no existe
            os.makedirs(self.config.backup_dir, exist_ok=True)
            
            success = self.db_manager.backup_database(backup_path)
            
            if success:
                self.logger.info(f"Backup completado: {backup_path}")
                return backup_path
            else:
                raise Exception("Falló la creación del backup")
                
        except Exception as e:
            self.logger.error(f"Error en backup automático: {e}")
            raise
    
    def _optimize_tables(self):
        """Optimiza todas las tablas de la base de datos"""
        try:
            results = self.db_manager.optimize_tables()
            
            total_tables = len(results)
            successful = sum(1 for success in results.values() if success)
            
            self.logger.info(f"Optimización completada: {successful}/{total_tables} tablas optimizadas")
            return results
            
        except Exception as e:
            self.logger.error(f"Error en optimización de tablas: {e}")
            raise
    
    def _cleanup_old_files(self):
        """Limpia archivos antiguos de reportes y backups"""
        try:
            cleaned_files = 0
            cutoff_date = datetime.now() - timedelta(days=self.config.backup_retention_days)
            
            # Limpiar backups antiguos
            if os.path.exists(self.config.backup_dir):
                for filename in os.listdir(self.config.backup_dir):
                    filepath = os.path.join(self.config.backup_dir, filename)
                    
                    if os.path.isfile(filepath):
                        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                        
                        if file_time < cutoff_date:
                            os.remove(filepath)
                            cleaned_files += 1
                            self.logger.info(f"Archivo eliminado: {filepath}")
            
            # Limpiar reportes antiguos
            if os.path.exists(self.config.reports_output_dir):
                for filename in os.listdir(self.config.reports_output_dir):
                    filepath = os.path.join(self.config.reports_output_dir, filename)
                    
                    if os.path.isfile(filepath):
                        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                        
                        if file_time < cutoff_date:
                            os.remove(filepath)
                            cleaned_files += 1
                            self.logger.info(f"Reporte eliminado: {filepath}")
            
            self.logger.info(f"Limpieza completada: {cleaned_files} archivos eliminados")
            return cleaned_files
            
        except Exception as e:
            self.logger.error(f"Error en limpieza de archivos: {e}")
            raise
    
    def _check_database_connection(self):
        """Verifica la conexión a la base de datos"""
        try:
            is_connected = self.db_manager.test_connection()
            
            if not is_connected:
                # Crear alerta crítica
                self.monitoring_system.alert_manager.create_alert(
                    category="connection",
                    metric_name="database_connection",
                    message="Conexión a la base de datos perdida",
                    current_value=0,
                    threshold_value=1,
                    severity="critical"
                )
                
                self.logger.error("Conexión a la base de datos perdida")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando conexión: {e}")
            raise