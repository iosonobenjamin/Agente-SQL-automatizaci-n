"""
Script de Instalación Automática para el Agente de Automatización SQL
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import mysql.connector
from mysql.connector import Error

def print_header():
    """Imprime el header del instalador"""
    print("🤖 SQL Automation Agent - Instalador Automático")
    print("=" * 60)
    print("Este script te ayudará a configurar el agente paso a paso")
    print("=" * 60)

def check_python_version():
    """Verifica la versión de Python"""
    print("\n🐍 Verificando versión de Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - OK")
    return True

def check_mysql_client():
    """Verifica si mysqldump está disponible"""
    print("\n🗄️ Verificando cliente MySQL...")
    
    try:
        result = subprocess.run(['mysqldump', '--version'], 
                              capture_output=True, text=True, check=True)
        print("✅ mysqldump encontrado - OK")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: mysqldump no encontrado")
        print("   Instala MySQL client o MariaDB client")
        print("   Ubuntu/Debian: sudo apt install mysql-client")
        print("   CentOS/RHEL: sudo yum install mysql")
        print("   macOS: brew install mysql-client")
        return False

def install_dependencies():
    """Instala las dependencias de Python"""
    print("\n📦 Instalando dependencias de Python...")
    
    try:
        # Verificar si requirements.txt existe
        if not os.path.exists('requirements.txt'):
            print("❌ Error: requirements.txt no encontrado")
            return False
        
        # Instalar dependencias
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dependencias instaladas exitosamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        print("Intenta instalar manualmente: pip install -r requirements.txt")
        return False

def create_directories():
    """Crea los directorios necesarios"""
    print("\n📁 Creando directorios...")
    
    directories = [
        'reports',
        'backups',
        'logs',
        'examples'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Directorio creado: {directory}/")
        except Exception as e:
            print(f"❌ Error creando directorio {directory}: {e}")
            return False
    
    return True

def configure_database():
    """Configura la conexión a la base de datos"""
    print("\n🗄️ Configuración de Base de Datos")
    print("-" * 40)
    
    # Solicitar información de conexión
    print("Ingresa los datos de conexión a MySQL:")
    
    host = input("Host (localhost): ").strip() or "localhost"
    port = input("Puerto (3306): ").strip() or "3306"
    username = input("Usuario: ").strip()
    password = input("Contraseña: ").strip()
    database = input("Base de datos: ").strip()
    
    if not username or not database:
        print("❌ Error: Usuario y base de datos son obligatorios")
        return None
    
    # Probar conexión
    print(f"\n🔍 Probando conexión a {username}@{host}:{port}/{database}...")
    
    try:
        connection = mysql.connector.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database
        )
        
        if connection.is_connected():
            print("✅ Conexión exitosa")
            
            # Verificar permisos (CORREGIDO: Agregado buffered=True)
            cursor = connection.cursor(buffered=True)
            
            # Probar permisos básicos
            try:
                cursor.execute("SELECT 1")
                # Consumir resultado por si acaso
                cursor.fetchone()
                print("✅ Permisos de SELECT - OK")
            except Error:
                print("❌ Sin permisos de SELECT")
            
            # Probar acceso a performance_schema
            try:
                cursor.execute("SELECT COUNT(*) FROM performance_schema.global_status LIMIT 1")
                cursor.fetchone()
                print("✅ Acceso a performance_schema - OK")
            except Error:
                print("⚠️ Sin acceso a performance_schema (monitoreo limitado)")
            
            # Probar acceso a information_schema
            try:
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables LIMIT 1")
                cursor.fetchone()
                print("✅ Acceso a information_schema - OK")
            except Error:
                print("⚠️ Sin acceso a information_schema (reportes limitados)")
            
            cursor.close()
            connection.close()
            
            return {
                'host': host,
                'port': port,
                'username': username,
                'password': password,
                'database': database
            }
            
    except Error as e:
        print(f"❌ Error de conexión: {e}")
        return None

def configure_email():
    """Configura las notificaciones por email"""
    print("\n📧 Configuración de Email (Opcional)")
    print("-" * 40)
    
    enable_email = input("¿Habilitar notificaciones por email? (s/N): ").strip().lower()
    
    if enable_email not in ['s', 'si', 'y', 'yes']:
        return None
    
    print("\nConfigura el servidor SMTP:")
    smtp_server = input("Servidor SMTP (smtp.gmail.com): ").strip() or "smtp.gmail.com"
    smtp_port = input("Puerto SMTP (587): ").strip() or "587"
    email_user = input("Email usuario: ").strip()
    email_password = input("Contraseña/App Password: ").strip()
    email_to = input("Emails destino (separados por coma): ").strip()
    
    if not email_user or not email_password or not email_to:
        print("⚠️ Configuración de email incompleta, se omitirá")
        return None
    
    return {
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'username': email_user,
        'password': email_password,
        'to_emails': [email.strip() for email in email_to.split(',')]
    }

def create_env_file(db_config, email_config=None):
    """Crea el archivo .env con la configuración"""
    print("\n⚙️ Creando archivo de configuración...")
    
    env_content = f"""# Configuración de Base de Datos
DB_HOST={db_config['host']}
DB_PORT={db_config['port']}
DB_USER={db_config['username']}
DB_PASSWORD={db_config['password']}
DB_NAME={db_config['database']}
DB_CHARSET=utf8mb4

# Configuración de Automatización
REPORTS_ENABLED=true
REPORTS_SCHEDULE=daily
REPORTS_OUTPUT_DIR=reports

MONITORING_ENABLED=true
MONITORING_INTERVAL=300

BACKUP_ENABLED=true
BACKUP_SCHEDULE=daily
BACKUP_RETENTION_DAYS=30
BACKUP_DIR=backups

# Umbrales de Alertas
ALERT_CPU_USAGE=80.0
ALERT_MEMORY_USAGE=85.0
ALERT_DISK_USAGE=90.0
ALERT_CONNECTION_COUNT=100
ALERT_SLOW_QUERY_TIME=5.0

# Configuración de Logs
LOG_LEVEL=INFO
LOG_FILE=logs/sql_agent.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
"""
    
    if email_config:
        env_content += f"""
# Configuración de Email
EMAIL_SMTP_SERVER={email_config['smtp_server']}
EMAIL_SMTP_PORT={email_config['smtp_port']}
EMAIL_USERNAME={email_config['username']}
EMAIL_PASSWORD={email_config['password']}
EMAIL_FROM={email_config['username']}
EMAIL_TO={','.join(email_config['to_emails'])}
"""
    else:
        env_content += """
# Configuración de Email (Deshabilitado)
EMAIL_SMTP_SERVER=
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_FROM=
EMAIL_TO=
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Archivo .env creado exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando .env: {e}")
        return False

def create_startup_scripts():
    """Crea scripts de inicio convenientes"""
    print("\n📜 Creando scripts de inicio...")
    
    # Script para Linux/macOS
    startup_script = """#!/bin/bash
# Script de inicio para SQL Automation Agent

echo "🤖 Iniciando SQL Automation Agent..."

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio del agente"
    exit 1
fi

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "❌ Error: Archivo .env no encontrado"
    echo "Ejecuta python install.py para configurar"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "🐍 Activando entorno virtual..."
    source venv/bin/activate
fi

# Ejecutar agente
echo "🚀 Iniciando agente en modo interactivo..."
python main.py --mode interactive

echo "👋 Agente detenido"
"""
    
    try:
        with open('start_agent.sh', 'w') as f:
            f.write(startup_script)
        os.chmod('start_agent.sh', 0o755)
        print("✅ Script start_agent.sh creado")
    except Exception as e:
        print(f"⚠️ Error creando start_agent.sh: {e}")
    
    # Script para Windows
    windows_script = """@echo off
REM Script de inicio para SQL Automation Agent

echo 🤖 Iniciando SQL Automation Agent...

REM Verificar que estamos en el directorio correcto
if not exist "main.py" (
    echo ❌ Error: Ejecuta este script desde el directorio del agente
    pause
    exit /b 1
)

REM Verificar archivo .env
if not exist ".env" (
    echo ❌ Error: Archivo .env no encontrado
    echo Ejecuta python install.py para configurar
    pause
    exit /b 1
)

REM Activar entorno virtual si existe
if exist "venv\\Scripts\\activate.bat" (
    echo 🐍 Activando entorno virtual...
    call venv\\Scripts\\activate.bat
)

REM Ejecutar agente
echo 🚀 Iniciando agente en modo interactivo...
python main.py --mode interactive

echo 👋 Agente detenido
pause
"""
    
    try:
        with open('start_agent.bat', 'w') as f:
            f.write(windows_script)
        print("✅ Script start_agent.bat creado")
    except Exception as e:
        print(f"⚠️ Error creando start_agent.bat: {e}")

def run_initial_test():
    """Ejecuta una prueba inicial del sistema"""
    print("\n🧪 Ejecutando prueba inicial...")
    
    try:
        # Importar y probar componentes básicos
        sys.path.append('.')
        
        from config import db_config
        from database_manager import DatabaseManager
        
        # Probar gestor de base de datos
        db_manager = DatabaseManager(db_config)
        
        if db_manager.test_connection():
            print("✅ Conexión a base de datos - OK")
            
            # Probar obtención de métricas
            try:
                metrics = db_manager.get_database_metrics()
                if metrics:
                    print("✅ Obtención de métricas - OK")
                else:
                    print("⚠️ Métricas limitadas (permisos insuficientes)")
            except Exception as e:
                print(f"⚠️ Error obteniendo métricas: {e}")
            
            db_manager.close_pool()
            return True
        else:
            print("❌ Error en conexión a base de datos")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba inicial: {e}")
        return False

def show_completion_info():
    """Muestra información de finalización"""
    print("\n🎉 ¡Instalación Completada!")
    print("=" * 50)
    
    print("\n📋 Próximos pasos:")
    print("1. Ejecutar el agente:")
    print("   • Linux/macOS: ./start_agent.sh")
    print("   • Windows: start_agent.bat")
    print("   • Manual: python main.py --mode interactive")
    
    print("\n2. Acceder al dashboard web:")
    print("   • Ejecutar: python examples/dashboard_launcher.py")
    print("   • Abrir: http://localhost:5000")
    
    print("\n3. Generar reportes personalizados:")
    print("   • Ejecutar: python examples/custom_reports.py")
    
    print("\n📁 Archivos importantes:")
    print("   • .env - Configuración principal")
    print("   • logs/sql_agent.log - Logs del sistema")
    print("   • reports/ - Reportes generados")
    print("   • backups/ - Backups automáticos")
    
    print("\n📖 Documentación:")
    print("   • README.md - Documentación completa")
    print("   • examples/ - Ejemplos de uso")
    
    print("\n🆘 Soporte:")
    print("   • Revisa los logs en caso de problemas")
    print("   • Verifica la configuración en .env")
    print("   • Consulta README.md para más detalles")

def main():
    """Función principal del instalador"""
    print_header()
    
    # Verificaciones previas
    if not check_python_version():
        return False
    
    if not check_mysql_client():
        print("\n⚠️ Continuando sin mysqldump (backups deshabilitados)")
    
    # Instalación de dependencias
    if not install_dependencies():
        return False
    
    # Crear directorios
    if not create_directories():
        return False
    
    # Configurar base de datos
    db_config = configure_database()
    if not db_config:
        print("❌ Configuración de base de datos requerida")
        return False
    
    # Configurar email (opcional)
    email_config = configure_email()
    
    # Crear archivo .env
    if not create_env_file(db_config, email_config):
        return False
    
    # Crear scripts de inicio
    create_startup_scripts()
    
    # Prueba inicial
    if not run_initial_test():
        print("⚠️ La prueba inicial falló, pero la instalación está completa")
        print("Revisa la configuración en .env")
    
    # Información de finalización
    show_completion_info()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Instalación exitosa")
        else:
            print("\n❌ Instalación falló")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)