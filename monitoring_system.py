"""
Sistema de Monitoreo y Alertas para el Agente SQL
"""
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable, Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import os
from dataclasses import dataclass, asdict

from database_manager import DatabaseManager
from config import automation_config, email_config

@dataclass
class Alert:
    """Clase para representar una alerta"""
    id: str
    timestamp: datetime
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str  # 'performance', 'connection', 'disk', 'query'
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    resolved: bool = False
    resolved_timestamp: Optional[datetime] = None

class AlertManager:
    """Gestor de alertas y notificaciones"""
    
    def __init__(self, email_config_obj=None):
        self.email_config = email_config_obj or email_config
        self.logger = logging.getLogger(__name__)
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
    def create_alert(self, category: str, metric_name: str, message: str, 
                    current_value: float, threshold_value: float, 
                    severity: str = 'medium') -> Alert:
        """Crea una nueva alerta"""
        alert_id = f"{category}_{metric_name}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=message,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        self.logger.warning(f"Nueva alerta [{severity.upper()}]: {message}")
        
        # Enviar notificación por email si está configurado
        if self.email_config.username and self.email_config.to_emails:
            self._send_alert_email(alert)
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resuelve una alerta activa"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_timestamp = datetime.now()
            
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alerta resuelta: {alert.message}")
            return True
        
        return False
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Obtiene alertas activas, opcionalmente filtradas por severidad"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de alertas"""
        active_alerts = list(self.active_alerts.values())
        
        summary = {
            'total_active': len(active_alerts),
            'by_severity': {},
            'by_category': {},
            'oldest_alert': None,
            'newest_alert': None
        }
        
        if active_alerts:
            # Contar por severidad
            for alert in active_alerts:
                summary['by_severity'][alert.severity] = summary['by_severity'].get(alert.severity, 0) + 1
                summary['by_category'][alert.category] = summary['by_category'].get(alert.category, 0) + 1
            
            # Alertas más antigua y más nueva
            sorted_alerts = sorted(active_alerts, key=lambda x: x.timestamp)
            summary['oldest_alert'] = sorted_alerts[0].timestamp
            summary['newest_alert'] = sorted_alerts[-1].timestamp
        
        return summary
    
    def _send_alert_email(self, alert: Alert):
        """Envía notificación de alerta por email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config.from_email or self.email_config.username
            msg['To'] = ', '.join(self.email_config.to_emails)
            msg['Subject'] = f"[SQL Agent Alert - {alert.severity.upper()}] {alert.category.title()}"
            
            # Cuerpo del email
            body = f"""
            Se ha generado una nueva alerta en el sistema de monitoreo SQL:
            
            Severidad: {alert.severity.upper()}
            Categoría: {alert.category}
            Métrica: {alert.metric_name}
            Valor actual: {alert.current_value}
            Umbral: {alert.threshold_value}
            Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            
            Mensaje: {alert.message}
            
            ---
            Agente de Automatización SQL
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar email
            server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
            server.starttls()
            server.login(self.email_config.username, self.email_config.password)
            text = msg.as_string()
            server.sendmail(self.email_config.username, self.email_config.to_emails, text)
            server.quit()
            
            self.logger.info(f"Notificación de alerta enviada por email: {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Error enviando email de alerta: {e}")

class MonitoringSystem:
    """Sistema principal de monitoreo"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = automation_config
        self.alert_manager = AlertManager()
        self.logger = logging.getLogger(__name__)
        
        self.monitoring_active = False
        self.monitoring_thread = None
        self.metrics_history: List[Dict[str, Any]] = []
        
        # Callbacks personalizados
        self.custom_checks: List[Callable] = []
        
    def add_custom_check(self, check_function: Callable):
        """Añade una función de verificación personalizada"""
        self.custom_checks.append(check_function)
        self.logger.info(f"Verificación personalizada añadida: {check_function.__name__}")
    
    def start_monitoring(self):
        """Inicia el monitoreo continuo"""
        if self.monitoring_active:
            self.logger.warning("El monitoreo ya está activo")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Sistema de monitoreo iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("Sistema de monitoreo detenido")
    
    def _monitoring_loop(self):
        """Bucle principal de monitoreo"""
        while self.monitoring_active:
            try:
                # Recopilar métricas
                metrics = self._collect_metrics()
                
                if metrics:
                    # Guardar en historial
                    self.metrics_history.append(metrics)
                    
                    # Mantener solo las últimas 1000 métricas
                    if len(self.metrics_history) > 1000:
                        self.metrics_history = self.metrics_history[-1000:]
                    
                    # Verificar umbrales
                    self._check_thresholds(metrics)
                    
                    # Ejecutar verificaciones personalizadas
                    self._run_custom_checks(metrics)
                
                # Esperar antes del siguiente ciclo
                time.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error en bucle de monitoreo: {e}")
                time.sleep(30)  # Esperar más tiempo en caso de error
    
    def _collect_metrics(self) -> Optional[Dict[str, Any]]:
        """Recopila métricas de la base de datos"""
        try:
            # Obtener métricas básicas
            db_metrics = self.db_manager.get_database_metrics()
            
            if not db_metrics:
                return None
            
            # Procesar y estructurar métricas
            processed_metrics = {
                'timestamp': datetime.now(),
                'connection_count': 0,
                'uptime_hours': 0,
                'slow_queries_count': 0,
                'database_size_mb': 0,
                'queries_per_second': 0,
                'table_locks_waited': 0
            }
            
            # Extraer valores específicos
            if db_metrics.get('connection_count'):
                processed_metrics['connection_count'] = int(db_metrics['connection_count'][0]['Value'])
            
            if db_metrics.get('uptime'):
                uptime_seconds = int(db_metrics['uptime'][0]['Value'])
                processed_metrics['uptime_hours'] = uptime_seconds / 3600
            
            if db_metrics.get('slow_queries'):
                processed_metrics['slow_queries_count'] = int(db_metrics['slow_queries'][0]['Value'])
            
            if db_metrics.get('database_size') and db_metrics['database_size']:
                processed_metrics['database_size_mb'] = float(db_metrics['database_size'][0]['size_mb'])
            
            if db_metrics.get('queries_per_second'):
                processed_metrics['queries_per_second'] = int(db_metrics['queries_per_second'][0]['Value'])
            
            if db_metrics.get('table_locks'):
                processed_metrics['table_locks_waited'] = int(db_metrics['table_locks'][0]['Value'])
            
            # Métricas adicionales del sistema
            processed_metrics.update(self._get_system_metrics())
            
            return processed_metrics
            
        except Exception as e:
            self.logger.error(f"Error recopilando métricas: {e}")
            return None
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """Obtiene métricas del sistema operativo"""
        import psutil
        
        try:
            return {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        except Exception as e:
            self.logger.warning(f"No se pudieron obtener métricas del sistema: {e}")
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_usage': 0
            }
    
    def _check_thresholds(self, metrics: Dict[str, Any]):
        """Verifica si las métricas exceden los umbrales configurados"""
        thresholds = self.config.alert_thresholds
        
        # Verificar cada métrica contra su umbral
        checks = [
            ('connection_count', 'Conexiones activas', 'connection'),
            ('cpu_usage', 'Uso de CPU', 'performance'),
            ('memory_usage', 'Uso de memoria', 'performance'),
            ('disk_usage', 'Uso de disco', 'disk'),
            ('slow_queries_count', 'Consultas lentas', 'query')
        ]
        
        for metric_name, description, category in checks:
            if metric_name in metrics and metric_name in thresholds:
                current_value = metrics[metric_name]
                threshold = thresholds[metric_name]
                
                # Verificar si excede el umbral
                if current_value > threshold:
                    # Verificar si ya existe una alerta activa para esta métrica
                    existing_alert = None
                    for alert in self.alert_manager.active_alerts.values():
                        if alert.metric_name == metric_name:
                            existing_alert = alert
                            break
                    
                    if not existing_alert:
                        # Determinar severidad
                        severity = self._determine_severity(current_value, threshold)
                        
                        # Crear nueva alerta
                        message = f"{description} excede el umbral: {current_value:.2f} > {threshold:.2f}"
                        self.alert_manager.create_alert(
                            category=category,
                            metric_name=metric_name,
                            message=message,
                            current_value=current_value,
                            threshold_value=threshold,
                            severity=severity
                        )
                
                else:
                    # Verificar si hay alertas activas que se pueden resolver
                    alerts_to_resolve = []
                    for alert_id, alert in self.alert_manager.active_alerts.items():
                        if alert.metric_name == metric_name:
                            alerts_to_resolve.append(alert_id)
                    
                    for alert_id in alerts_to_resolve:
                        self.alert_manager.resolve_alert(alert_id)
    
    def _determine_severity(self, current_value: float, threshold: float) -> str:
        """Determina la severidad de una alerta basada en qué tanto excede el umbral"""
        ratio = current_value / threshold
        
        if ratio >= 2.0:
            return 'critical'
        elif ratio >= 1.5:
            return 'high'
        elif ratio >= 1.2:
            return 'medium'
        else:
            return 'low'
    
    def _run_custom_checks(self, metrics: Dict[str, Any]):
        """Ejecuta verificaciones personalizadas"""
        for check_function in self.custom_checks:
            try:
                check_function(metrics, self.alert_manager)
            except Exception as e:
                self.logger.error(f"Error en verificación personalizada {check_function.__name__}: {e}")
    
    def get_metrics_history(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Obtiene el historial de métricas de las últimas N horas"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        return [
            metrics for metrics in self.metrics_history
            if metrics['timestamp'] >= cutoff_time
        ]
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema de monitoreo"""
        return {
            'monitoring_active': self.monitoring_active,
            'monitoring_interval': self.config.monitoring_interval,
            'metrics_collected': len(self.metrics_history),
            'active_alerts': len(self.alert_manager.active_alerts),
            'alert_summary': self.alert_manager.get_alert_summary(),
            'last_collection': self.metrics_history[-1]['timestamp'] if self.metrics_history else None
        }
    
    def export_metrics(self, filepath: str, hours_back: int = 24):
        """Exporta métricas a un archivo JSON"""
        metrics_data = {
            'export_timestamp': datetime.now().isoformat(),
            'hours_back': hours_back,
            'metrics': []
        }
        
        # Convertir timestamps a strings para JSON
        for metrics in self.get_metrics_history(hours_back):
            metrics_copy = metrics.copy()
            metrics_copy['timestamp'] = metrics_copy['timestamp'].isoformat()
            metrics_data['metrics'].append(metrics_copy)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            self.logger.info(f"Métricas exportadas a: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando métricas: {e}")
            return False

# Funciones de verificación personalizadas de ejemplo
def check_database_growth(metrics: Dict[str, Any], alert_manager: AlertManager):
    """Verificación personalizada: crecimiento rápido de la base de datos"""
    pass

def check_query_patterns(metrics: Dict[str, Any], alert_manager: AlertManager):
    """Verificación personalizada: patrones anómalos en consultas"""
    pass