"""
Configuración del Agente de Automatización SQL
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

# CARGAR VARIABLES DE ENTORNO (.env)
load_dotenv()

@dataclass
class DatabaseConfig:
    """Configuración de conexión a la base de datos"""
    host: str = "localhost"
    port: int = 3306
    username: str = "root"
    password: str = ""
    database: str = "automation_db"
    charset: str = "utf8mb4"
    
    @classmethod
    def from_env(cls):
        """Carga configuración desde variables de entorno"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            username=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "automation_db"),
            charset=os.getenv("DB_CHARSET", "utf8mb4")
        )

@dataclass
class EmailConfig:
    """Configuración para notificaciones por email"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    to_emails: List[str] = field(default_factory=list)
    
    @classmethod
    def from_env(cls):
        to_emails_str = os.getenv("EMAIL_TO", "")
        return cls(
            smtp_server=os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
            username=os.getenv("EMAIL_USERNAME", ""),
            password=os.getenv("EMAIL_PASSWORD", ""),
            from_email=os.getenv("EMAIL_FROM", ""),
            to_emails=[e.strip() for e in to_emails_str.split(',')] if to_emails_str else []
        )

@dataclass
class AutomationConfig:
    """Configuración general del agente"""
    # Configuración de reportes
    reports_enabled: bool = True
    reports_schedule: str = "daily"
    reports_output_dir: str = "reports"
    
    # Configuración de monitoreo
    monitoring_enabled: bool = True
    monitoring_interval: int = 300
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Configuración de backup
    backup_enabled: bool = True
    backup_schedule: str = "daily"
    backup_retention_days: int = 30
    backup_dir: str = "backups"
    
    # Configuración de logs
    log_level: str = "INFO"
    log_file: str = "logs/sql_agent.log"
    log_max_size: int = 10485760
    log_backup_count: int = 5
    
    @classmethod
    def from_env(cls):
        # Función auxiliar para convertir texto a boolean
        def str_to_bool(s):
            return str(s).lower() in ('true', '1', 'yes', 'on')

        config = cls(
            reports_enabled=str_to_bool(os.getenv("REPORTS_ENABLED", "true")),
            reports_schedule=os.getenv("REPORTS_SCHEDULE", "daily"),
            reports_output_dir=os.getenv("REPORTS_OUTPUT_DIR", "reports"),
            
            monitoring_enabled=str_to_bool(os.getenv("MONITORING_ENABLED", "true")),
            monitoring_interval=int(os.getenv("MONITORING_INTERVAL", "300")),
            
            backup_enabled=str_to_bool(os.getenv("BACKUP_ENABLED", "true")),
            backup_schedule=os.getenv("BACKUP_SCHEDULE", "daily"),
            backup_retention_days=int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
            backup_dir=os.getenv("BACKUP_DIR", "backups"),
            
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/sql_agent.log"),
            log_max_size=int(os.getenv("LOG_MAX_SIZE", "10485760")),
            log_backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
        )
        
        # Cargar umbrales de alertas
        config.alert_thresholds = {
            'connection_count': int(os.getenv("ALERT_CONNECTION_COUNT", "100")),
            'cpu_usage': float(os.getenv("ALERT_CPU_USAGE", "80.0")),
            'memory_usage': float(os.getenv("ALERT_MEMORY_USAGE", "85.0")),
            'disk_usage': float(os.getenv("ALERT_DISK_USAGE", "90.0")),
            'slow_queries_count': 10  # Valor por defecto
        }
        return config

# Instancias globales que usará el resto del programa
db_config = DatabaseConfig.from_env()
email_config = EmailConfig.from_env()
automation_config = AutomationConfig.from_env()