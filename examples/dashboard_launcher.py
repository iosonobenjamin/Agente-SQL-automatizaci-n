"""
Lanzador del Dashboard Web - Ejemplo de uso
"""
import sys
import os
import threading
import time
from datetime import datetime

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import SQLAutomationAgent
from web_dashboard import WebDashboard

def launch_dashboard_with_agent():
    """Lanza el agente completo con dashboard web"""
    
    print("🚀 Iniciando Agente de Automatización SQL con Dashboard Web")
    print("=" * 60)
    
    # Crear instancia del agente
    agent = SQLAutomationAgent()
    
    try:
        # Inicializar agente
        print("🔧 Inicializando componentes del agente...")
        if not agent.initialize():
            print("❌ Error: No se pudo inicializar el agente")
            return
        
        print("✅ Agente inicializado exitosamente")
        
        # Iniciar servicios del agente
        print("⚙️ Iniciando servicios automáticos...")
        if not agent.start():
            print("❌ Error: No se pudieron iniciar los servicios")
            return
        
        print("✅ Servicios iniciados exitosamente")
        
        # Crear dashboard web
        print("🌐 Configurando dashboard web...")
        dashboard = WebDashboard(
            agent.db_manager,
            agent.monitoring_system,
            agent.scheduler,
            agent.report_generator
        )
        
        print("✅ Dashboard configurado")
        
        # Mostrar información del sistema
        print("\n📊 Estado inicial del sistema:")
        print("-" * 40)
        
        # Estado de conexión
        if agent.db_manager.test_connection():
            print("🟢 Base de datos: Conectada")
        else:
            print("🔴 Base de datos: Desconectada")
        
        # Estado del monitoreo
        monitoring_status = agent.monitoring_system.get_monitoring_status()
        if monitoring_status['monitoring_active']:
            print("🟢 Monitoreo: Activo")
        else:
            print("🔴 Monitoreo: Inactivo")
        
        # Estado del programador
        scheduler_status = agent.scheduler.get_task_status()
        print(f"🟢 Programador: {scheduler_status['enabled_tasks']}/{scheduler_status['total_tasks']} tareas activas")
        
        # Alertas activas
        active_alerts = len(agent.monitoring_system.alert_manager.active_alerts)
        if active_alerts > 0:
            print(f"🟡 Alertas: {active_alerts} activas")
        else:
            print("🟢 Alertas: Sin alertas activas")
        
        print("-" * 40)
        
        # Información de acceso
        print(f"\n🌐 Dashboard Web disponible en:")
        print(f"   • Local: http://localhost:5000")
        print(f"   • Red:   http://0.0.0.0:5000")
        print(f"\n⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n💡 Funcionalidades disponibles:")
        print(f"   • Monitoreo en tiempo real")
        print(f"   • Gestión de alertas")
        print(f"   • Control de tareas programadas")
        print(f"   • Generación manual de reportes")
        print(f"   • Descarga de backups y reportes")
        
        print(f"\n🔄 El sistema se actualiza automáticamente cada 30 segundos")
        print(f"📧 Las alertas se envían por email (si está configurado)")
        
        print(f"\n" + "=" * 60)
        print(f"🎯 Para detener el sistema, presiona Ctrl+C")
        print(f"=" * 60)
        
        # Ejecutar dashboard (esto bloquea hasta que se detenga)
        dashboard.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print(f"\n\n🛑 Deteniendo sistema...")
        
    except Exception as e:
        print(f"\n❌ Error ejecutando dashboard: {e}")
        
    finally:
        # Detener agente limpiamente
        print("🧹 Limpiando recursos...")
        agent.stop()
        print("✅ Sistema detenido correctamente")

def launch_dashboard_only():
    """Lanza solo el dashboard sin servicios automáticos"""
    
    print("🌐 Iniciando Dashboard Web (Solo Visualización)")
    print("=" * 50)
    
    # Crear instancia del agente sin iniciar servicios automáticos
    agent = SQLAutomationAgent()
    
    try:
        # Solo inicializar componentes básicos
        print("🔧 Inicializando componentes básicos...")
        if not agent.initialize():
            print("❌ Error: No se pudo inicializar el agente")
            return
        
        print("✅ Componentes inicializados")
        print("⚠️ Nota: Servicios automáticos deshabilitados en este modo")
        
        # Crear dashboard
        dashboard = WebDashboard(
            agent.db_manager,
            agent.monitoring_system,
            agent.scheduler,
            agent.report_generator
        )
        
        print(f"\n🌐 Dashboard disponible en: http://localhost:5000")
        print(f"🔍 Modo: Solo visualización (sin automatización)")
        print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ejecutar dashboard
        dashboard.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Deteniendo dashboard...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        agent.stop()

def show_system_info():
    """Muestra información del sistema sin iniciar servicios"""
    
    print("ℹ️ Información del Sistema SQL Agent")
    print("=" * 40)
    
    agent = SQLAutomationAgent()
    
    try:
        if agent.initialize():
            # Información de base de datos
            print("📊 Base de Datos:")
            print(f"   Host: {agent.db_manager.config.host}")
            print(f"   Puerto: {agent.db_manager.config.port}")
            print(f"   Base de datos: {agent.db_manager.config.database}")
            
            # Probar conexión
            if agent.db_manager.test_connection():
                print("   Estado: 🟢 Conectada")
                
                # Obtener métricas básicas
                try:
                    metrics = agent.db_manager.get_database_metrics()
                    if metrics:
                        print("   Métricas disponibles: ✅")
                    else:
                        print("   Métricas disponibles: ❌")
                except:
                    print("   Métricas disponibles: ❌")
                    
            else:
                print("   Estado: 🔴 Desconectada")
            
            # Información de configuración
            from config import automation_config, email_config
            
            print(f"\n⚙️ Configuración:")
            print(f"   Reportes: {'✅' if automation_config.reports_enabled else '❌'}")
            print(f"   Monitoreo: {'✅' if automation_config.monitoring_enabled else '❌'}")
            print(f"   Backups: {'✅' if automation_config.backup_enabled else '❌'}")
            print(f"   Email: {'✅' if email_config.username else '❌'}")
            
            # Información de directorios
            print(f"\n📁 Directorios:")
            print(f"   Reportes: {automation_config.reports_output_dir}")
            print(f"   Backups: {automation_config.backup_dir}")
            print(f"   Logs: {automation_config.log_file}")
            
            # Verificar directorios
            for dir_name, dir_path in [
                ("Reportes", automation_config.reports_output_dir),
                ("Backups", automation_config.backup_dir)
            ]:
                if os.path.exists(dir_path):
                    files_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                    print(f"   {dir_name}: 📂 {files_count} archivos")
                else:
                    print(f"   {dir_name}: 📂 No existe (se creará automáticamente)")
            
        else:
            print("❌ No se pudo inicializar el sistema")
            
    except Exception as e:
        print(f"❌ Error obteniendo información: {e}")
        
    finally:
        agent.stop()

def main():
    """Función principal del lanzador"""
    
    print("🤖 SQL Automation Agent - Dashboard Launcher")
    print("=" * 50)
    
    print("\nOpciones disponibles:")
    print("1. 🚀 Lanzar agente completo con dashboard")
    print("2. 🌐 Lanzar solo dashboard (sin automatización)")
    print("3. ℹ️ Mostrar información del sistema")
    print("4. 🚪 Salir")
    
    while True:
        try:
            opcion = input("\nSelecciona una opción (1-4): ").strip()
            
            if opcion == "1":
                launch_dashboard_with_agent()
                break
                
            elif opcion == "2":
                launch_dashboard_only()
                break
                
            elif opcion == "3":
                show_system_info()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == "4":
                print("👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción no válida. Intenta de nuevo.")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()