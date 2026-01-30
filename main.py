"""
Agente Principal de Automatización SQL
"""
import logging
import logging.handlers
import sys
import os
import argparse
from datetime import datetime
import signal
import json
from typing import Dict, Any

# Configurar el path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import db_config, email_config, automation_config
from database_manager import DatabaseManager
from report_generator import ReportGenerator
from monitoring_system import MonitoringSystem
from scheduler import TaskScheduler

class SQLAutomationAgent:
    """Agente principal de automatización SQL"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Componentes principales
        self.db_manager = None
        self.report_generator = None
        self.monitoring_system = None
        self.scheduler = None
        
        # Estado del agente
        self.running = False
        
        # Configurar manejadores de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def setup_logging(self):
        """Configura el sistema de logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # CORRECCIÓN: Verificar si hay un directorio antes de intentar crearlo
        log_dir = os.path.dirname(automation_config.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Configurar logging básico
        logging.basicConfig(
            level=getattr(logging, automation_config.log_level),
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.handlers.RotatingFileHandler(
                    automation_config.log_file,
                    maxBytes=automation_config.log_max_size,
                    backupCount=automation_config.log_backup_count
                )
            ]
        )
    
    def initialize(self) -> bool:
        """Inicializa todos los componentes del agente"""
        self.logger.info("Inicializando SQL Automation Agent...")
        
        try:
            # 1. Conectar a base de datos
            self.db_manager = DatabaseManager(db_config)
            if not self.db_manager.test_connection():
                self.logger.error("No se pudo conectar a la base de datos")
                return False
                
            self.logger.info("Conexión a base de datos establecida")
            
            # 2. Inicializar generador de reportes
            self.report_generator = ReportGenerator(self.db_manager)
            
            # 3. Inicializar sistema de monitoreo
            self.monitoring_system = MonitoringSystem(self.db_manager)
            
            # 4. Inicializar planificador de tareas
            self.scheduler = TaskScheduler(self)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante inicialización: {e}")
            return False
    
    def start(self) -> bool:
        """Inicia la ejecución del agente"""
        if not self.initialize():
            return False
            
        self.running = True
        self.logger.info("Agente iniciado correctamente")
        
        # Iniciar componentes activos
        if automation_config.monitoring_enabled:
            self.monitoring_system.start_monitoring()
            
        # Iniciar planificador
        self.scheduler.start()
        
        return True
    
    def stop(self):
        """Detiene la ejecución del agente"""
        self.logger.info("Deteniendo agente...")
        self.running = False
        
        if self.monitoring_system:
            self.monitoring_system.stop_monitoring()
            
        if self.db_manager:
            self.db_manager.close_pool()
            
        self.logger.info("Agente detenido")
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de terminación (Ctrl+C)"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Señal recibida: {signal_name}")
        self.stop()
        sys.exit(0)
        
    def run_interactive_mode(self):
        """Ejecuta el agente en modo interactivo (menú)"""
        if not self.initialize():
            print("Error inicializando el agente. Revisa los logs.")
            return

        print("\n🤖 SQL Automation Agent - Modo Interactivo")
        print("==========================================")
        
        while True:
            print("\nOpciones disponibles:")
            print("1. 📊 Generar reporte de salud de base de datos")
            print("2. 📈 Generar reporte de rendimiento")
            print("3. 💾 Crear backup manual")
            print("4. 🧹 Optimizar tablas")
            print("5. 👁️ Ver estado del monitoreo")
            print("6. 📋 Ver últimas alertas")
            print("0. 🚪 Salir")
            
            choice = input("\nSelecciona una opción: ").strip()
            
            if choice == '1':
                print("\nGenerando reporte de salud...")
                report_path = self.report_generator.generate_database_health_report()
                if report_path:
                    print(f"✅ Reporte generado: {report_path}")
                else:
                    print("❌ Error generando reporte")
                    
            elif choice == '2':
                days = input("¿De cuántos días? (7): ").strip() or "7"
                print(f"\nGenerando reporte de rendimiento ({days} días)...")
                try:
                    report_path = self.report_generator.generate_performance_report(int(days))
                    if report_path:
                        print(f"✅ Reporte generado: {report_path}")
                    else:
                        print("❌ Error generando reporte")
                except ValueError:
                    print("❌ Por favor ingresa un número válido")
                    
            elif choice == '3':
                print("\nIniciando backup manual...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(
                    automation_config.backup_dir, 
                    f"manual_backup_{timestamp}.sql"
                )
                if self.db_manager.backup_database(backup_path):
                    print(f"✅ Backup completado: {backup_path}")
                else:
                    print("❌ Error creando backup")
                    
            elif choice == '4':
                print("\nOptimizando tablas...")
                results = self.db_manager.optimize_tables()
                print("\nResultados:")
                for table, success in results.items():
                    status = "✅" if success else "❌"
                    print(f"{status} {table}")
                    
            elif choice == '5':
                if self.monitoring_system:
                    # Asegurar que el monitoreo esté activo para ver datos en tiempo real
                    was_active = self.monitoring_system.monitoring_active
                    if not was_active:
                         print("Iniciando monitoreo temporal para obtener métricas...")
                         self.monitoring_system.start_monitoring()
                         import time
                         time.sleep(2) # Esperar a que recolecte algo
                    
                    status = self.monitoring_system.get_monitoring_status()
                    print("\nEstado del Monitoreo:")
                    print(json.dumps(status, indent=2, default=str))
                    
                    if not was_active:
                        self.monitoring_system.stop_monitoring()
                else:
                    print("Sistema de monitoreo no inicializado")
                    
            elif choice == '6':
                if self.monitoring_system:
                    alerts = self.monitoring_system.alert_manager.get_active_alerts()
                    if alerts:
                        print(f"\nAlertas Activas ({len(alerts)}):")
                        for alert in alerts:
                            print(f"[{alert.severity.upper()}] {alert.message} ({alert.timestamp})")
                    else:
                        print("\n✅ No hay alertas activas")
                else:
                    print("Sistema de monitoreo no inicializado")
                    
            elif choice == '0':
                print("\n👋 ¡Hasta luego!")
                self.stop()
                break
            else:
                print("❌ Opción no válida")

def main():
    """Función principal de entrada"""
    parser = argparse.ArgumentParser(description='SQL Automation Agent')
    parser.add_argument('--mode', choices=['interactive', 'daemon', 'oneshot'], 
                      default='interactive', help='Modo de ejecución')
    parser.add_argument('--task', help='Tarea específica para modo oneshot')
    
    args = parser.parse_args()
    
    agent = SQLAutomationAgent()
    
    try:
        if args.mode == 'interactive':
            agent.run_interactive_mode()
        
        elif args.mode == 'daemon':
            if agent.start():
                # Mantener el agente corriendo
                import time
                while agent.running:
                    time.sleep(1)
            
        elif args.mode == 'oneshot':
            if args.task:
                # Ejecutar tarea específica
                if agent.initialize():
                    if args.task == 'health_report':
                        agent.report_generator.generate_database_health_report()
                    elif args.task == 'performance_report':
                        agent.report_generator.generate_performance_report(7)
                    elif args.task == 'backup':
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_path = f"oneshot_backup_{timestamp}.sql"
                        agent.db_manager.backup_database(backup_path)
                    elif args.task == 'optimize':
                        agent.db_manager.optimize_tables()
                    else:
                        print(f"Tarea desconocida: {args.task}")
            else:
                print("Modo oneshot requiere especificar --task")
    
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    except Exception as e:
        print(f"Error ejecutando agente: {e}")
    finally:
        agent.stop()

if __name__ == "__main__":
    main()