"""
Dashboard Web para el Agente de Automatización SQL
"""
from flask import Flask, render_template, jsonify, request, send_file
import json
from datetime import datetime, timedelta
import os
import threading
from typing import Dict, Any, List
import logging

from database_manager import DatabaseManager
from monitoring_system import MonitoringSystem
from scheduler import TaskScheduler
from report_generator import ReportGenerator
from config import automation_config

class WebDashboard:
    """Dashboard web para monitoreo y control del agente"""
    
    def __init__(self, db_manager: DatabaseManager, monitoring_system: MonitoringSystem, 
                 scheduler: TaskScheduler, report_generator: ReportGenerator):
        self.db_manager = db_manager
        self.monitoring_system = monitoring_system
        self.scheduler = scheduler
        self.report_generator = report_generator
        
        self.app = Flask(__name__)
        self.app.secret_key = 'sql_automation_agent_secret_key'
        
        self.logger = logging.getLogger(__name__)
        
        # Configurar rutas
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas del dashboard"""
        
        @self.app.route('/')
        def dashboard():
            """Página principal del dashboard"""
            return self._render_dashboard()
        
        @self.app.route('/api/status')
        def api_status():
            """API: Estado general del sistema"""
            return jsonify(self._get_system_status())
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """API: Métricas de monitoreo"""
            hours = request.args.get('hours', 24, type=int)
            return jsonify(self._get_metrics_data(hours))
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """API: Alertas activas"""
            return jsonify(self._get_alerts_data())
        
        @self.app.route('/api/tasks')
        def api_tasks():
            """API: Estado de tareas"""
            return jsonify(self._get_tasks_data())
        
        @self.app.route('/api/reports')
        def api_reports():
            """API: Lista de reportes disponibles"""
            return jsonify(self._get_reports_list())
        
        @self.app.route('/api/task/<task_id>/toggle', methods=['POST'])
        def api_toggle_task(task_id):
            """API: Habilitar/deshabilitar tarea"""
            return jsonify(self._toggle_task(task_id))
        
        @self.app.route('/api/task/<task_id>/run', methods=['POST'])
        def api_run_task(task_id):
            """API: Ejecutar tarea manualmente"""
            return jsonify(self._run_task_manually(task_id))
        
        @self.app.route('/api/generate_report', methods=['POST'])
        def api_generate_report():
            """API: Generar reporte manual"""
            report_type = request.json.get('type', 'health')
            return jsonify(self._generate_manual_report(report_type))
        
        @self.app.route('/api/backup', methods=['POST'])
        def api_backup():
            """API: Realizar backup manual"""
            return jsonify(self._perform_manual_backup())
        
        @self.app.route('/api/optimize', methods=['POST'])
        def api_optimize():
            """API: Optimizar tablas"""
            return jsonify(self._optimize_tables())
        
        @self.app.route('/download/report/<filename>')
        def download_report(filename):
            """Descargar reporte"""
            return self._download_file(filename, automation_config.reports_output_dir)
        
        @self.app.route('/download/backup/<filename>')
        def download_backup(filename):
            """Descargar backup"""
            return self._download_file(filename, automation_config.backup_dir)
    
    def _render_dashboard(self):
        """Renderiza la página principal del dashboard"""
        dashboard_html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SQL Automation Agent - Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
                .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
                .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .card h3 { margin-bottom: 15px; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 5px; }
                .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
                .status-active { background: #28a745; }
                .status-inactive { background: #dc3545; }
                .status-warning { background: #ffc107; }
                .metric-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
                .metric-value { font-weight: bold; color: #667eea; }
                .alert-item { padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid; }
                .alert-critical { background: #f8d7da; border-color: #dc3545; }
                .alert-high { background: #fff3cd; border-color: #ffc107; }
                .alert-medium { background: #d1ecf1; border-color: #17a2b8; }
                .alert-low { background: #d4edda; border-color: #28a745; }
                .task-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; }
                .task-controls button { margin-left: 5px; padding: 5px 10px; border: none; border-radius: 3px; cursor: pointer; }
                .btn-primary { background: #667eea; color: white; }
                .btn-success { background: #28a745; color: white; }
                .btn-warning { background: #ffc107; color: black; }
                .btn-danger { background: #dc3545; color: white; }
                .chart-container { height: 300px; margin: 20px 0; }
                .refresh-btn { position: fixed; bottom: 20px; right: 20px; background: #667eea; color: white; border: none; padding: 15px; border-radius: 50%; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
                .loading { text-align: center; padding: 20px; color: #666; }
                .reports-list { max-height: 300px; overflow-y: auto; }
                .report-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #eee; }
                .timestamp { font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 SQL Automation Agent</h1>
                <p>Dashboard de Monitoreo y Control</p>
                <p class="timestamp" id="last-update">Última actualización: Cargando...</p>
            </div>
            
            <div class="container">
                <!-- Estado del Sistema -->
                <div class="grid">
                    <div class="card">
                        <h3>📊 Estado del Sistema</h3>
                        <div id="system-status" class="loading">Cargando...</div>
                    </div>
                    
                    <div class="card">
                        <h3>🚨 Alertas Activas</h3>
                        <div id="alerts-list" class="loading">Cargando...</div>
                    </div>
                    
                    <div class="card">
                        <h3>⚙️ Tareas Programadas</h3>
                        <div id="tasks-list" class="loading">Cargando...</div>
                    </div>
                </div>
                
                <!-- Métricas y Gráficos -->
                <div class="grid">
                    <div class="card">
                        <h3>📈 Métricas de Rendimiento</h3>
                        <div class="chart-container">
                            <canvas id="performance-chart"></canvas>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>💾 Uso de Recursos</h3>
                        <div class="chart-container">
                            <canvas id="resources-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Reportes y Acciones -->
                <div class="grid">
                    <div class="card">
                        <h3>📋 Reportes Disponibles</h3>
                        <div id="reports-list" class="reports-list loading">Cargando...</div>
                    </div>
                    
                    <div class="card">
                        <h3>🔧 Acciones Manuales</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                            <button class="btn-primary" onclick="generateReport('health')">Reporte de Salud</button>
                            <button class="btn-primary" onclick="generateReport('performance')">Reporte de Rendimiento</button>
                            <button class="btn-warning" onclick="performBackup()">Backup Manual</button>
                            <button class="btn-success" onclick="optimizeTables()">Optimizar Tablas</button>
                        </div>
                        <div id="action-status" style="margin-top: 15px;"></div>
                    </div>
                </div>
            </div>
            
            <button class="refresh-btn" onclick="refreshDashboard()" title="Actualizar Dashboard">🔄</button>
            
            <script>
                let performanceChart, resourcesChart;
                
                // Inicializar dashboard
                $(document).ready(function() {
                    initCharts();
                    refreshDashboard();
                    
                    // Auto-refresh cada 30 segundos
                    setInterval(refreshDashboard, 30000);
                });
                
                function initCharts() {
                    // Gráfico de rendimiento
                    const perfCtx = document.getElementById('performance-chart').getContext('2d');
                    performanceChart = new Chart(perfCtx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Conexiones',
                                data: [],
                                borderColor: '#667eea',
                                tension: 0.1
                            }, {
                                label: 'Consultas Lentas',
                                data: [],
                                borderColor: '#dc3545',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                    
                    // Gráfico de recursos
                    const resCtx = document.getElementById('resources-chart').getContext('2d');
                    resourcesChart = new Chart(resCtx, {
                        type: 'doughnut',
                        data: {
                            labels: ['CPU', 'Memoria', 'Disco'],
                            datasets: [{
                                data: [0, 0, 0],
                                backgroundColor: ['#667eea', '#28a745', '#ffc107']
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                }
                
                function refreshDashboard() {
                    updateLastRefresh();
                    loadSystemStatus();
                    loadAlerts();
                    loadTasks();
                    loadMetrics();
                    loadReports();
                }
                
                function updateLastRefresh() {
                    $('#last-update').text('Última actualización: ' + new Date().toLocaleString());
                }
                
                function loadSystemStatus() {
                    $.get('/api/status', function(data) {
                        let html = '';
                        
                        // Estado de conexión DB
                        const dbStatus = data.database_connected ? 'active' : 'inactive';
                        html += `<div class="metric-item">
                            <span><span class="status-indicator status-${dbStatus}"></span>Base de Datos</span>
                            <span class="metric-value">${data.database_connected ? 'Conectado' : 'Desconectado'}</span>
                        </div>`;
                        
                        // Estado del monitoreo
                        const monStatus = data.monitoring_active ? 'active' : 'inactive';
                        html += `<div class="metric-item">
                            <span><span class="status-indicator status-${monStatus}"></span>Monitoreo</span>
                            <span class="metric-value">${data.monitoring_active ? 'Activo' : 'Inactivo'}</span>
                        </div>`;
                        
                        // Estado del programador
                        const schedStatus = data.scheduler_active ? 'active' : 'inactive';
                        html += `<div class="metric-item">
                            <span><span class="status-indicator status-${schedStatus}"></span>Programador</span>
                            <span class="metric-value">${data.scheduler_active ? 'Activo' : 'Inactivo'}</span>
                        </div>`;
                        
                        // Métricas adicionales
                        if (data.metrics) {
                            html += `<div class="metric-item">
                                <span>Conexiones Activas</span>
                                <span class="metric-value">${data.metrics.connection_count || 0}</span>
                            </div>`;
                            
                            html += `<div class="metric-item">
                                <span>Tamaño BD (MB)</span>
                                <span class="metric-value">${(data.metrics.database_size_mb || 0).toFixed(2)}</span>
                            </div>`;
                        }
                        
                        $('#system-status').html(html);
                    }).fail(function() {
                        $('#system-status').html('<div style="color: red;">Error cargando estado del sistema</div>');
                    });
                }
                
                function loadAlerts() {
                    $.get('/api/alerts', function(data) {
                        let html = '';
                        
                        if (data.alerts && data.alerts.length > 0) {
                            data.alerts.forEach(function(alert) {
                                html += `<div class="alert-item alert-${alert.severity}">
                                    <strong>[${alert.severity.toUpperCase()}]</strong> ${alert.message}<br>
                                    <small>Métrica: ${alert.metric_name} | Valor: ${alert.current_value} | Umbral: ${alert.threshold_value}</small><br>
                                    <small class="timestamp">${new Date(alert.timestamp).toLocaleString()}</small>
                                </div>`;
                            });
                        } else {
                            html = '<div style="color: green; text-align: center; padding: 20px;">✅ No hay alertas activas</div>';
                        }
                        
                        $('#alerts-list').html(html);
                    }).fail(function() {
                        $('#alerts-list').html('<div style="color: red;">Error cargando alertas</div>');
                    });
                }
                
                function loadTasks() {
                    $.get('/api/tasks', function(data) {
                        let html = '';
                        
                        if (data.tasks && data.tasks.length > 0) {
                            data.tasks.forEach(function(task) {
                                const statusIcon = task.enabled ? '✅' : '❌';
                                const lastRun = task.last_run ? new Date(task.last_run).toLocaleString() : 'Nunca';
                                
                                html += `<div class="task-item">
                                    <div>
                                        <strong>${statusIcon} ${task.name}</strong><br>
                                        <small>Última ejecución: ${lastRun}</small><br>
                                        <small>Ejecuciones: ${task.run_count} | Errores: ${task.error_count}</small>
                                    </div>
                                    <div class="task-controls">
                                        <button class="btn-${task.enabled ? 'warning' : 'success'}" 
                                                onclick="toggleTask('${task.id}')">
                                            ${task.enabled ? 'Deshabilitar' : 'Habilitar'}
                                        </button>
                                        <button class="btn-primary" onclick="runTask('${task.id}')">Ejecutar</button>
                                    </div>
                                </div>`;
                            });
                        } else {
                            html = '<div>No hay tareas configuradas</div>';
                        }
                        
                        $('#tasks-list').html(html);
                    }).fail(function() {
                        $('#tasks-list').html('<div style="color: red;">Error cargando tareas</div>');
                    });
                }
                
                function loadMetrics() {
                    $.get('/api/metrics?hours=24', function(data) {
                        if (data.metrics && data.metrics.length > 0) {
                            // Actualizar gráfico de rendimiento
                            const labels = data.metrics.map(m => new Date(m.timestamp).toLocaleTimeString());
                            const connections = data.metrics.map(m => m.connection_count || 0);
                            const slowQueries = data.metrics.map(m => m.slow_queries_count || 0);
                            
                            performanceChart.data.labels = labels.slice(-20); // Últimos 20 puntos
                            performanceChart.data.datasets[0].data = connections.slice(-20);
                            performanceChart.data.datasets[1].data = slowQueries.slice(-20);
                            performanceChart.update();
                            
                            // Actualizar gráfico de recursos (último valor)
                            const lastMetric = data.metrics[data.metrics.length - 1];
                            resourcesChart.data.datasets[0].data = [
                                lastMetric.cpu_usage || 0,
                                lastMetric.memory_usage || 0,
                                lastMetric.disk_usage || 0
                            ];
                            resourcesChart.update();
                        }
                    });
                }
                
                function loadReports() {
                    $.get('/api/reports', function(data) {
                        let html = '';
                        
                        if (data.reports && data.reports.length > 0) {
                            data.reports.forEach(function(report) {
                                html += `<div class="report-item">
                                    <div>
                                        <strong>${report.name}</strong><br>
                                        <small class="timestamp">${new Date(report.timestamp).toLocaleString()}</small>
                                    </div>
                                    <div>
                                        <a href="/download/report/${report.filename}" class="btn-primary" style="text-decoration: none; padding: 5px 10px; border-radius: 3px;">Descargar</a>
                                    </div>
                                </div>`;
                            });
                        } else {
                            html = '<div>No hay reportes disponibles</div>';
                        }
                        
                        $('#reports-list').html(html);
                    });
                }
                
                // Funciones de acciones
                function toggleTask(taskId) {
                    $.post(`/api/task/${taskId}/toggle`, function(data) {
                        if (data.success) {
                            loadTasks();
                        } else {
                            alert('Error: ' + data.message);
                        }
                    });
                }
                
                function runTask(taskId) {
                    $.post(`/api/task/${taskId}/run`, function(data) {
                        if (data.success) {
                            $('#action-status').html('<div style="color: green;">✅ Tarea ejecutada exitosamente</div>');
                            setTimeout(() => $('#action-status').html(''), 3000);
                            loadTasks();
                        } else {
                            $('#action-status').html('<div style="color: red;">❌ Error: ' + data.message + '</div>');
                        }
                    });
                }
                
                function generateReport(type) {
                    $('#action-status').html('<div style="color: blue;">🔄 Generando reporte...</div>');
                    
                    $.post('/api/generate_report', JSON.stringify({type: type}), function(data) {
                        if (data.success) {
                            $('#action-status').html('<div style="color: green;">✅ Reporte generado exitosamente</div>');
                            setTimeout(() => {
                                $('#action-status').html('');
                                loadReports();
                            }, 3000);
                        } else {
                            $('#action-status').html('<div style="color: red;">❌ Error: ' + data.message + '</div>');
                        }
                    }, 'json');
                }
                
                function performBackup() {
                    $('#action-status').html('<div style="color: blue;">🔄 Realizando backup...</div>');
                    
                    $.post('/api/backup', function(data) {
                        if (data.success) {
                            $('#action-status').html('<div style="color: green;">✅ Backup completado exitosamente</div>');
                            setTimeout(() => $('#action-status').html(''), 3000);
                        } else {
                            $('#action-status').html('<div style="color: red;">❌ Error: ' + data.message + '</div>');
                        }
                    });
                }
                
                function optimizeTables() {
                    $('#action-status').html('<div style="color: blue;">🔄 Optimizando tablas...</div>');
                    
                    $.post('/api/optimize', function(data) {
                        if (data.success) {
                            $('#action-status').html('<div style="color: green;">✅ Tablas optimizadas exitosamente</div>');
                            setTimeout(() => $('#action-status').html(''), 3000);
                        } else {
                            $('#action-status').html('<div style="color: red;">❌ Error: ' + data.message + '</div>');
                        }
                    });
                }
            </script>
        </body>
        </html>
        """
        return dashboard_html
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado general del sistema"""
        try:
            # Estado de conexión a BD
            db_connected = self.db_manager.test_connection()
            
            # Estado del monitoreo
            monitoring_status = self.monitoring_system.get_monitoring_status()
            
            # Estado del programador
            scheduler_status = self.scheduler.get_task_status()
            
            # Métricas actuales
            current_metrics = None
            if self.monitoring_system.metrics_history:
                current_metrics = self.monitoring_system.metrics_history[-1]
            
            return {
                'timestamp': datetime.now().isoformat(),
                'database_connected': db_connected,
                'monitoring_active': monitoring_status['monitoring_active'],
                'scheduler_active': scheduler_status['scheduler_active'],
                'metrics': current_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del sistema: {e}")
            return {'error': str(e)}
    
    def _get_metrics_data(self, hours: int) -> Dict[str, Any]:
        """Obtiene datos de métricas para gráficos"""
        try:
            metrics = self.monitoring_system.get_metrics_history(hours)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'hours_requested': hours,
                'metrics_count': len(metrics),
                'metrics': [
                    {
                        'timestamp': m['timestamp'].isoformat(),
                        'connection_count': m.get('connection_count', 0),
                        'slow_queries_count': m.get('slow_queries_count', 0),
                        'cpu_usage': m.get('cpu_usage', 0),
                        'memory_usage': m.get('memory_usage', 0),
                        'disk_usage': m.get('disk_usage', 0),
                        'database_size_mb': m.get('database_size_mb', 0)
                    }
                    for m in metrics
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo métricas: {e}")
            return {'error': str(e)}
    
    def _get_alerts_data(self) -> Dict[str, Any]:
        """Obtiene datos de alertas activas"""
        try:
            alerts = self.monitoring_system.alert_manager.get_active_alerts()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'alert_count': len(alerts),
                'alerts': [
                    {
                        'id': alert.id,
                        'timestamp': alert.timestamp.isoformat(),
                        'severity': alert.severity,
                        'category': alert.category,
                        'message': alert.message,
                        'metric_name': alert.metric_name,
                        'current_value': alert.current_value,
                        'threshold_value': alert.threshold_value
                    }
                    for alert in alerts
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo alertas: {e}")
            return {'error': str(e)}
    
    def _get_tasks_data(self) -> Dict[str, Any]:
        """Obtiene datos de tareas programadas"""
        try:
            return self.scheduler.get_task_status()
            
        except Exception as e:
            self.logger.error(f"Error obteniendo tareas: {e}")
            return {'error': str(e)}
    
    def _get_reports_list(self) -> Dict[str, Any]:
        """Obtiene lista de reportes disponibles"""
        try:
            reports = []
            
            if os.path.exists(automation_config.reports_output_dir):
                for filename in os.listdir(automation_config.reports_output_dir):
                    if filename.endswith('.html'):
                        filepath = os.path.join(automation_config.reports_output_dir, filename)
                        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                        
                        reports.append({
                            'filename': filename,
                            'name': filename.replace('_', ' ').replace('.html', '').title(),
                            'timestamp': file_time.isoformat(),
                            'size': os.path.getsize(filepath)
                        })
            
            # Ordenar por fecha (más reciente primero)
            reports.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'report_count': len(reports),
                'reports': reports
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo lista de reportes: {e}")
            return {'error': str(e)}
    
    def _toggle_task(self, task_id: str) -> Dict[str, Any]:
        """Habilita/deshabilita una tarea"""
        try:
            if task_id not in self.scheduler.scheduled_tasks:
                return {'success': False, 'message': 'Tarea no encontrada'}
            
            task = self.scheduler.scheduled_tasks[task_id]
            
            if task.enabled:
                success = self.scheduler.disable_task(task_id)
                action = 'deshabilitada'
            else:
                success = self.scheduler.enable_task(task_id)
                action = 'habilitada'
            
            if success:
                return {'success': True, 'message': f'Tarea {action} exitosamente'}
            else:
                return {'success': False, 'message': 'Error cambiando estado de la tarea'}
                
        except Exception as e:
            self.logger.error(f"Error cambiando estado de tarea {task_id}: {e}")
            return {'success': False, 'message': str(e)}
    
    def _run_task_manually(self, task_id: str) -> Dict[str, Any]:
        """Ejecuta una tarea manualmente"""
        try:
            if task_id not in self.scheduler.scheduled_tasks:
                return {'success': False, 'message': 'Tarea no encontrada'}
            
            task = self.scheduler.scheduled_tasks[task_id]
            
            # Ejecutar tarea en un hilo separado para no bloquear la respuesta
            def run_task():
                self.scheduler._execute_task(task)
            
            thread = threading.Thread(target=run_task)
            thread.start()
            
            return {'success': True, 'message': 'Tarea iniciada exitosamente'}
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea {task_id}: {e}")
            return {'success': False, 'message': str(e)}
    
    def _generate_manual_report(self, report_type: str) -> Dict[str, Any]:
        """Genera un reporte manual"""
        try:
            if report_type == 'health':
                result = self.report_generator.generate_database_health_report()
            elif report_type == 'performance':
                result = self.report_generator.generate_performance_report(7)
            else:
                return {'success': False, 'message': 'Tipo de reporte no válido'}
            
            return {'success': True, 'message': 'Reporte generado exitosamente', 'result': result}
            
        except Exception as e:
            self.logger.error(f"Error generando reporte {report_type}: {e}")
            return {'success': False, 'message': str(e)}
    
    def _perform_manual_backup(self) -> Dict[str, Any]:
        """Realiza un backup manual"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"manual_backup_{timestamp}.sql"
            backup_path = os.path.join(automation_config.backup_dir, backup_filename)
            
            os.makedirs(automation_config.backup_dir, exist_ok=True)
            
            success = self.db_manager.backup_database(backup_path)
            
            if success:
                return {'success': True, 'message': f'Backup completado: {backup_filename}'}
            else:
                return {'success': False, 'message': 'Error realizando backup'}
                
        except Exception as e:
            self.logger.error(f"Error en backup manual: {e}")
            return {'success': False, 'message': str(e)}
    
    def _optimize_tables(self) -> Dict[str, Any]:
        """Optimiza las tablas de la base de datos"""
        try:
            results = self.db_manager.optimize_tables()
            
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            
            return {
                'success': True, 
                'message': f'Optimización completada: {successful}/{total} tablas optimizadas',
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizando tablas: {e}")
            return {'success': False, 'message': str(e)}
    
    def _download_file(self, filename: str, directory: str):
        """Permite descargar archivos"""
        try:
            filepath = os.path.join(directory, filename)
            
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
            else:
                return jsonify({'error': 'Archivo no encontrado'}), 404
                
        except Exception as e:
            self.logger.error(f"Error descargando archivo {filename}: {e}")
            return jsonify({'error': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Ejecuta el servidor web del dashboard"""
        self.logger.info(f"Iniciando dashboard web en http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)