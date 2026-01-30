 
# 🤖 Agente de Automatización SQL
 
Un agente inteligente y completo para la automatización de tareas de base de datos MySQL, incluyendo monitoreo en tiempo real, generación de reportes automáticos, alertas inteligentes y dashboard web interactivo.
 
## 🚀 Características Principales
 
### 📊 Monitoreo Inteligente
- **Monitoreo en tiempo real** de métricas de base de datos
- **Sistema de alertas** configurable con notificaciones por email
- **Detección automática** de consultas lentas y problemas de rendimiento
- **Métricas del sistema** (CPU, memoria, disco)
 
### 📈 Reportes Automáticos
- **Reportes de salud** de la base de datos con visualizaciones
- **Análisis de rendimiento** con gráficos interactivos
- **Reportes personalizados** basados en consultas SQL
- **Exportación HTML** con gráficos embebidos
 
### ⚙️ Automatización Completa
- **Backups automáticos** programables
- **Optimización de tablas** automática
- **Limpieza de archivos** antiguos
- **Programador de tareas** flexible
 
### 🌐 Dashboard Web
- **Interfaz web moderna** para monitoreo y control
- **Gráficos en tiempo real** con Chart.js
- **Control de tareas** desde la interfaz
- **Descarga de reportes** y backups
 
## 📋 Requisitos del Sistema
 
### Software Requerido
- **Python 3.8+**
- **MySQL 5.7+** o **MariaDB 10.3+**
- **mysqldump** (incluido con MySQL)
- **Navegador web moderno** (para el dashboard)
 
### Dependencias Python
```bash
pip install -r requirements.txt
```
 
## 🛠️ Instalación y Configuración
 
### 1. Clonar y Configurar
```bash
# Descargar el agente
git clone <repository-url>
cd sql_automation_agent
 
# Instalar dependencias
pip install -r requirements.txt
 
# Copiar configuración de ejemplo
cp .env.example .env
```
 
### 2. Configurar Base de Datos
Edita el archivo `.env` con tus credenciales:
 
```env
# Configuración de Base de Datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=tu_base_de_datos
 
# Configuración de Email (opcional)
EMAIL_USERNAME=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
EMAIL_TO=admin@empresa.com
```
 
### 3. Configurar Permisos MySQL
El usuario de MySQL necesita los siguientes permisos:
 
```sql
-- Permisos básicos
GRANT SELECT, INSERT, UPDATE, DELETE ON tu_base_de_datos.* TO 'tu_usuario'@'%';
 
-- Permisos para monitoreo
GRANT SELECT ON performance_schema.* TO 'tu_usuario'@'%';
GRANT SELECT ON information_schema.* TO 'tu_usuario'@'%';
GRANT SHOW DATABASES ON *.* TO 'tu_usuario'@'%';
GRANT PROCESS ON *.* TO 'tu_usuario'@'%';
 
-- Permisos para optimización
GRANT ALTER ON tu_base_de_datos.* TO 'tu_usuario'@'%';
 
FLUSH PRIVILEGES;
```
 
## 🎯 Modos de Ejecución
 
### Modo Interactivo (Recomendado)
```bash
python main.py --mode interactive
```
 
Comandos disponibles:
- `status` - Estado del agente
- `tasks` - Estado de tareas programadas
- `alerts` - Alertas activas
- `report health` - Generar reporte de salud
- `report performance` - Generar reporte de rendimiento
- `backup` - Backup manual
- `optimize` - Optimizar tablas
- `quit` - Salir
 
### Modo Daemon (Producción)
```bash
python main.py --mode daemon
```
 
### Modo OneShot (Tareas Específicas)
```bash
# Generar reporte de salud
python main.py --mode oneshot --task health_report
 
# Realizar backup
python main.py --mode oneshot --task backup
 
# Optimizar tablas
python main.py --mode oneshot --task optimize
```
 
## 🌐 Dashboard Web
 
### Iniciar Dashboard
```python
from web_dashboard import WebDashboard
from main import SQLAutomationAgent
 
# Inicializar agente
agent = SQLAutomationAgent()
agent.initialize()
 
# Crear dashboard
dashboard = WebDashboard(
    agent.db_manager,
    agent.monitoring_system,
    agent.scheduler,
    agent.report_generator
)
 
# Ejecutar en puerto 5000
dashboard.run(host='0.0.0.0', port=5000)
```
 
Accede al dashboard en: `http://localhost:5000`
 
### Características del Dashboard
- **Estado en tiempo real** del sistema
- **Gráficos interactivos** de métricas
- **Gestión de alertas** activas
- **Control de tareas** programadas
- **Generación manual** de reportes
- **Descarga de archivos** (reportes y backups)
 
## 📊 Tipos de Reportes
 
### 1. Reporte de Salud
- Métricas generales de la base de datos
- Conexiones activas
- Consultas lentas detectadas
- Recomendaciones automáticas
- Gráficos de estado
 
### 2. Reporte de Rendimiento
- Análisis de rendimiento por día
- Uso de tablas por tamaño
- Estadísticas de consultas
- Tendencias de crecimiento
 
### 3. Reportes Personalizados
```python
# Ejemplo de reporte personalizado
custom_queries = {
    'usuarios_activos': """
        SELECT DATE(last_login) as fecha, COUNT(*) as usuarios
        FROM users 
        WHERE last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(last_login)
        ORDER BY fecha DESC
    """,
    'ventas_por_categoria': """
        SELECT categoria, SUM(total) as ventas_total
        FROM ventas v
        JOIN productos p ON v.producto_id = p.id
        WHERE v.fecha >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY categoria
        ORDER BY ventas_total DESC
    """
}
 
report_generator.generate_custom_report(custom_queries, "Reporte Semanal de Ventas")
```
 
## ⚠️ Sistema de Alertas
 
### Umbrales Configurables
```env
# Umbrales de alertas en .env
ALERT_CPU_USAGE=80.0
ALERT_MEMORY_USAGE=85.0
ALERT_DISK_USAGE=90.0
ALERT_CONNECTION_COUNT=100
ALERT_SLOW_QUERY_TIME=5.0
```
 
### Tipos de Alertas
- **Críticas** 🚨 - Requieren atención inmediata
- **Altas** 🔴 - Problemas importantes
- **Medias** 🟠 - Advertencias
- **Bajas** 🟡 - Información
 
### Notificaciones por Email
Las alertas se envían automáticamente por email cuando:
- Se detecta un problema crítico
- Las métricas exceden los umbrales configurados
- Se pierde la conexión a la base de datos
 
## 🔧 Tareas Automáticas
 
### Tareas por Defecto
1. **Reporte Diario de Salud** (8:00 AM)
2. **Reporte Semanal de Rendimiento** (Lunes)
3. **Backup Automático** (2:00 AM diario)
4. **Optimización de Tablas** (Domingo)
5. **Limpieza de Archivos** (3:00 AM diario)
6. **Verificación de Conexión** (Cada 5 minutos)
 
### Personalizar Tareas
```python
# Añadir tarea personalizada
scheduler.add_task(
    task_id="reporte_mensual",
    name="Reporte Mensual de Usuarios",
    function=mi_funcion_personalizada,
    schedule_type="monthly",
    schedule_value=1  # Día 1 del mes
)
```
 
## 📁 Estructura de Archivos
 
```
sql_automation_agent/
├── main.py                 # Agente principal
├── config.py              # Configuración
├── database_manager.py    # Gestor de BD
├── report_generator.py    # Generador de reportes
├── monitoring_system.py   # Sistema de monitoreo
├── scheduler.py           # Programador de tareas
├── web_dashboard.py       # Dashboard web
├── requirements.txt       # Dependencias
├── .env.example          # Configuración de ejemplo
├── README.md             # Documentación
├── reports/              # Reportes generados
├── backups/              # Backups automáticos
└── logs/                 # Archivos de log
```
 
## 🔍 Monitoreo y Logs
 
### Archivos de Log
- `sql_agent.log` - Log principal del agente
- Rotación automática cuando alcanza 10MB
- Mantiene 5 archivos de respaldo
 
### Niveles de Log
- `DEBUG` - Información detallada
- `INFO` - Información general
- `WARNING` - Advertencias
- `ERROR` - Errores
- `CRITICAL` - Errores críticos
 
## 🚨 Solución de Problemas
 
### Problemas Comunes
 
#### Error de Conexión a MySQL
```bash
# Verificar conexión
mysql -h localhost -u tu_usuario -p tu_base_de_datos
 
# Verificar permisos
SHOW GRANTS FOR 'tu_usuario'@'%';
```
 
#### Error de Permisos para Backup
```bash
# Verificar mysqldump
which mysqldump
mysqldump --version
 
# Probar backup manual
mysqldump -h localhost -u tu_usuario -p tu_base_de_datos > test_backup.sql
```
 
#### Dashboard No Carga
```bash
# Verificar puerto disponible
netstat -tlnp | grep :5000
 
# Verificar logs
tail -f sql_agent.log
```
 
### Logs de Depuración
```python
# Habilitar logs detallados en config.py
automation_config.log_level = "DEBUG"
```
 
## 🔒 Seguridad
 
### Mejores Prácticas
1. **Usar usuarios específicos** para el agente (no root)
2. **Configurar permisos mínimos** necesarios
3. **Usar contraseñas seguras** y app passwords para email
4. **Restringir acceso** al dashboard web
5. **Mantener backups** en ubicación segura
 
### Variables de Entorno
Nunca hardcodees credenciales en el código. Usa siempre el archivo `.env`:
 
```env
# ✅ Correcto
DB_PASSWORD=mi_password_seguro
 
# ❌ Incorrecto (en código)
password = "mi_password_seguro"
```
 
## 📈 Optimización de Rendimiento
 
### Configuración de Pool de Conexiones
```python
# En database_manager.py
pool_config = {
    'pool_size': 10,        # Ajustar según carga
    'pool_reset_session': True,
    'autocommit': True
}
```
 
### Intervalos de Monitoreo
```python
# En config.py
automation_config.monitoring_interval = 300  # 5 minutos (ajustable)
```
 
## 🤝 Contribuir
 
### Desarrollo
1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request
 
### Reportar Bugs
Usa el sistema de issues de GitHub incluyendo:
- Descripción del problema
- Pasos para reproducir
- Logs relevantes
- Configuración del sistema
 
## 📄 Licencia
 
Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.
 
## 🆘 Soporte
 
### Documentación
- [Wiki del Proyecto](wiki-url)
- [FAQ](faq-url)
- [Ejemplos](examples-url)
 
### Contacto
- **Email**: soporte@empresa.com
- **Issues**: [GitHub Issues](issues-url)
- **Discusiones**: [GitHub Discussions](discussions-url)
 
---
 
## 🎉 ¡Empezar Ahora!
 
```bash
# Instalación rápida
git clone <repository-url>
cd sql_automation_agent
pip install -r requirements.txt
cp .env.example .env
 
# Editar .env con tus credenciales
nano .env
 
# Ejecutar en modo interactivo
python main.py --mode interactive
```
 
¡Tu agente de automatización SQL estará listo en minutos! 🚀#   A g e n t e - S Q L - a u t o m a t i z a c i - n  
 