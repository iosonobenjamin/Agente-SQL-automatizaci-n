"""
Generador de Reportes Automáticos para el Agente SQL
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import json
from typing import Dict, List, Any, Optional
import logging
from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

from database_manager import DatabaseManager
from config import automation_config

class ReportGenerator:
    """Generador de reportes automáticos con visualizaciones"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = automation_config
        self.logger = logging.getLogger(__name__)
        
        # Configurar estilo de gráficos
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Crear directorio de reportes
        os.makedirs(self.config.reports_output_dir, exist_ok=True)
    
    def generate_database_health_report(self) -> Dict[str, Any]:
        """Genera reporte de salud de la base de datos"""
        self.logger.info("Generando reporte de salud de base de datos")
        
        # Obtener métricas
        metrics = self.db_manager.get_database_metrics()
        slow_queries = self.db_manager.get_slow_queries(20)
        
        # Procesar métricas
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'database_name': self.db_manager.config.database,
            'metrics': self._process_metrics(metrics),
            'slow_queries': slow_queries,
            'recommendations': self._generate_recommendations(metrics, slow_queries)
        }
        
        # Generar visualizaciones
        charts = self._create_health_charts(report_data)
        report_data['charts'] = charts
        
        # Generar HTML
        html_report = self._generate_html_report(report_data, 'database_health')
        
        # Guardar reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(
            self.config.reports_output_dir, 
            f"database_health_{timestamp}.html"
        )
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        self.logger.info(f"Reporte de salud guardado: {report_path}")
        return report_data
    
    def generate_performance_report(self, days_back: int = 7) -> Dict[str, Any]:
        """Genera reporte de rendimiento de los últimos N días"""
        self.logger.info(f"Generando reporte de rendimiento ({days_back} días)")
        
        # Consultas de rendimiento
        performance_queries = {
            'query_performance': """
                SELECT 
                    DATE(last_seen) as date,
                    COUNT(*) as query_count,
                    AVG(avg_timer_wait/1000000000) as avg_execution_time,
                    SUM(sum_rows_examined) as total_rows_examined,
                    SUM(sum_rows_sent) as total_rows_sent
                FROM performance_schema.events_statements_summary_by_digest 
                WHERE schema_name = %s 
                AND last_seen >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY DATE(last_seen)
                ORDER BY date DESC
            """,
            'table_usage': f"""
                SELECT 
                    table_name,
                    table_rows,
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                    ROUND((data_length / 1024 / 1024), 2) AS data_mb,
                    ROUND((index_length / 1024 / 1024), 2) AS index_mb
                FROM information_schema.tables 
                WHERE table_schema = '{self.db_manager.config.database}'
                ORDER BY size_mb DESC
                LIMIT 20
            """
        }
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'period_days': days_back,
            'database_name': self.db_manager.config.database
        }
        
        # Ejecutar consultas
        for key, query in performance_queries.items():
            try:
                if key == 'query_performance':
                    result = self.db_manager.execute_query(
                        query, (self.db_manager.config.database, days_back)
                    )
                else:
                    result = self.db_manager.execute_query(query)
                report_data[key] = result
            except Exception as e:
                self.logger.error(f"Error en consulta {key}: {e}")
                report_data[key] = []
        
        # Generar gráficos
        charts = self._create_performance_charts(report_data)
        report_data['charts'] = charts
        
        # Generar HTML
        html_report = self._generate_html_report(report_data, 'performance')
        
        # Guardar reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(
            self.config.reports_output_dir, 
            f"performance_report_{timestamp}.html"
        )
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        self.logger.info(f"Reporte de rendimiento guardado: {report_path}")
        return report_data
    
    def generate_custom_report(self, queries: Dict[str, str], report_name: str) -> Dict[str, Any]:
        """Genera un reporte personalizado basado en consultas definidas por el usuario"""
        self.logger.info(f"Generando reporte personalizado: {report_name}")
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'report_name': report_name,
            'database_name': self.db_manager.config.database,
            'results': {}
        }
        
        # Ejecutar consultas personalizadas
        for query_name, query_sql in queries.items():
            try:
                result = self.db_manager.execute_query(query_sql)
                report_data['results'][query_name] = result
                
                # Crear DataFrame para análisis
                if result:
                    df = pd.DataFrame(result)
                    report_data['results'][f"{query_name}_summary"] = {
                        'row_count': len(df),
                        'columns': list(df.columns),
                        'data_types': df.dtypes.to_dict() if not df.empty else {}
                    }
                
            except Exception as e:
                self.logger.error(f"Error en consulta personalizada {query_name}: {e}")
                report_data['results'][query_name] = []
        
        # Generar visualizaciones automáticas
        charts = self._create_custom_charts(report_data)
        report_data['charts'] = charts
        
        # Generar HTML
        html_report = self._generate_html_report(report_data, 'custom')
        
        # Guardar reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in report_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        report_path = os.path.join(
            self.config.reports_output_dir, 
            f"custom_{safe_name}_{timestamp}.html"
        )
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        self.logger.info(f"Reporte personalizado guardado: {report_path}")
        return report_data
    
    def _process_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa las métricas brutas en formato más legible"""
        processed = {}
        
        # Procesar conexiones
        if metrics.get('connection_count'):
            conn_data = metrics['connection_count'][0]
            processed['connections'] = int(conn_data['Value'])
        
        # Procesar uptime
        if metrics.get('uptime'):
            uptime_seconds = int(metrics['uptime'][0]['Value'])
            uptime_hours = uptime_seconds / 3600
            processed['uptime_hours'] = round(uptime_hours, 2)
        
        # Procesar consultas lentas
        if metrics.get('slow_queries'):
            processed['slow_queries_count'] = int(metrics['slow_queries'][0]['Value'])
        
        # Procesar tamaño de base de datos
        if metrics.get('database_size') and metrics['database_size']:
            processed['database_size_mb'] = float(metrics['database_size'][0]['size_mb'])
        
        return processed
    
    def _generate_recommendations(self, metrics: Dict[str, Any], slow_queries: List[Dict]) -> List[str]:
        """Genera recomendaciones basadas en las métricas"""
        recommendations = []
        
        # Analizar conexiones
        processed = self._process_metrics(metrics)
        
        if processed.get('connections', 0) > self.config.alert_thresholds['connection_count']:
            recommendations.append(
                f"Alto número de conexiones activas ({processed['connections']}). "
                "Considere optimizar el pool de conexiones."
            )
        
        # Analizar consultas lentas
        if len(slow_queries) > 5:
            recommendations.append(
                f"Se detectaron {len(slow_queries)} consultas lentas. "
                "Revise los índices y optimice las consultas más problemáticas."
            )
        
        # Analizar tamaño de base de datos
        if processed.get('database_size_mb', 0) > 1000:  # > 1GB
            recommendations.append(
                f"Base de datos grande ({processed['database_size_mb']:.2f} MB). "
                "Considere implementar archivado de datos históricos."
            )
        
        if not recommendations:
            recommendations.append("La base de datos está funcionando dentro de parámetros normales.")
        
        return recommendations
    
    def _create_health_charts(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Crea gráficos para el reporte de salud"""
        charts = {}
        
        try:
            # Gráfico de consultas lentas
            if report_data['slow_queries']:
                df_slow = pd.DataFrame(report_data['slow_queries'])
                
                fig = px.bar(
                    df_slow.head(10), 
                    x='avg_time_seconds', 
                    y='sql_text',
                    orientation='h',
                    title='Top 10 Consultas Más Lentas',
                    labels={'avg_time_seconds': 'Tiempo Promedio (segundos)', 'sql_text': 'Consulta SQL'}
                )
                fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
                charts['slow_queries'] = pio.to_html(fig, include_plotlyjs='cdn')
            
            # Gráfico de métricas generales
            metrics = report_data['metrics']
            if metrics:
                metric_names = []
                metric_values = []
                
                for key, value in metrics.items():
                    if isinstance(value, (int, float)) and key != 'database_size_mb':
                        metric_names.append(key.replace('_', ' ').title())
                        metric_values.append(value)
                
                if metric_names:
                    fig = go.Figure(data=[
                        go.Bar(x=metric_names, y=metric_values, marker_color='lightblue')
                    ])
                    fig.update_layout(
                        title='Métricas Generales de la Base de Datos',
                        xaxis_title='Métrica',
                        yaxis_title='Valor'
                    )
                    charts['general_metrics'] = pio.to_html(fig, include_plotlyjs='cdn')
        
        except Exception as e:
            self.logger.error(f"Error creando gráficos de salud: {e}")
        
        return charts
    
    def _create_performance_charts(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Crea gráficos para el reporte de rendimiento"""
        charts = {}
        
        try:
            # Gráfico de rendimiento por día
            if report_data.get('query_performance'):
                df_perf = pd.DataFrame(report_data['query_performance'])
                
                if not df_perf.empty:
                    fig = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('Número de Consultas por Día', 'Tiempo Promedio de Ejecución'),
                        vertical_spacing=0.1
                    )
                    
                    # Gráfico de cantidad de consultas
                    fig.add_trace(
                        go.Scatter(x=df_perf['date'], y=df_perf['query_count'], 
                                 mode='lines+markers', name='Consultas'),
                        row=1, col=1
                    )
                    
                    # Gráfico de tiempo de ejecución
                    fig.add_trace(
                        go.Scatter(x=df_perf['date'], y=df_perf['avg_execution_time'], 
                                 mode='lines+markers', name='Tiempo Avg (s)', line_color='red'),
                        row=2, col=1
                    )
                    
                    fig.update_layout(height=600, title_text="Rendimiento de Consultas")
                    charts['query_performance'] = pio.to_html(fig, include_plotlyjs='cdn')
            
            # Gráfico de uso de tablas
            if report_data.get('table_usage'):
                df_tables = pd.DataFrame(report_data['table_usage'])
                
                if not df_tables.empty:
                    fig = px.bar(
                        df_tables.head(15), 
                        x='table_name', 
                        y='size_mb',
                        title='Top 15 Tablas por Tamaño',
                        labels={'size_mb': 'Tamaño (MB)', 'table_name': 'Tabla'}
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    charts['table_usage'] = pio.to_html(fig, include_plotlyjs='cdn')
        
        except Exception as e:
            self.logger.error(f"Error creando gráficos de rendimiento: {e}")
        
        return charts
    
    def _create_custom_charts(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Crea gráficos automáticos para reportes personalizados"""
        charts = {}
        
        try:
            for query_name, result in report_data['results'].items():
                if isinstance(result, list) and result and not query_name.endswith('_summary'):
                    df = pd.DataFrame(result)
                    
                    # Detectar columnas numéricas
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    
                    if len(numeric_cols) >= 1:
                        # Crear gráfico de barras simple
                        if len(df) <= 20:  # Solo para datasets pequeños
                            x_col = df.columns[0]  # Primera columna como X
                            y_col = numeric_cols[0]  # Primera columna numérica como Y
                            
                            fig = px.bar(
                                df, 
                                x=x_col, 
                                y=y_col,
                                title=f'Visualización: {query_name.replace("_", " ").title()}'
                            )
                            fig.update_layout(xaxis_tickangle=-45)
                            charts[query_name] = pio.to_html(fig, include_plotlyjs='cdn')
        
        except Exception as e:
            self.logger.error(f"Error creando gráficos personalizados: {e}")
        
        return charts
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Genera el HTML del reporte usando templates"""
        
        html_template = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ report_title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; }
                .metric-card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
                .chart-container { margin: 20px 0; padding: 15px; background: white; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
                .recommendations { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .slow-query { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 5px 0; border-radius: 3px; font-family: monospace; font-size: 12px; }
                table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .timestamp { color: #666; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{ report_title }}</h1>
                    <p class="timestamp">Generado: {{ timestamp }}</p>
                    <p>Base de datos: {{ database_name }}</p>
                </div>
                
                {% if report_type == 'database_health' %}
                    <h2>Métricas de Salud</h2>
                    {% for key, value in metrics.items() %}
                    <div class="metric-card">
                        <strong>{{ key.replace('_', ' ').title() }}:</strong> {{ value }}
                    </div>
                    {% endfor %}
                    
                    {% if recommendations %}
                    <div class="recommendations">
                        <h3>Recomendaciones</h3>
                        <ul>
                        {% for rec in recommendations %}
                            <li>{{ rec }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    
                    {% if slow_queries %}
                    <h2>Consultas Lentas (Top 10)</h2>
                    {% for query in slow_queries[:10] %}
                    <div class="slow-query">
                        <strong>Tiempo promedio:</strong> {{ "%.3f"|format(query.avg_time_seconds) }}s<br>
                        <strong>Consulta:</strong> {{ query.sql_text[:200] }}{% if query.sql_text|length > 200 %}...{% endif %}
                    </div>
                    {% endfor %}
                    {% endif %}
                
                {% elif report_type == 'performance' %}
                    <h2>Resumen de Rendimiento ({{ period_days }} días)</h2>
                    
                    {% if query_performance %}
                    <h3>Rendimiento por Día</h3>
                    <table>
                        <tr><th>Fecha</th><th>Consultas</th><th>Tiempo Promedio (s)</th><th>Filas Examinadas</th></tr>
                        {% for row in query_performance %}
                        <tr>
                            <td>{{ row.date }}</td>
                            <td>{{ row.query_count }}</td>
                            <td>{{ "%.3f"|format(row.avg_execution_time) }}</td>
                            <td>{{ row.total_rows_examined }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% endif %}
                    
                    {% if table_usage %}
                    <h3>Uso de Tablas</h3>
                    <table>
                        <tr><th>Tabla</th><th>Filas</th><th>Tamaño Total (MB)</th><th>Datos (MB)</th><th>Índices (MB)</th></tr>
                        {% for table in table_usage[:15] %}
                        <tr>
                            <td>{{ table.table_name }}</td>
                            <td>{{ table.table_rows }}</td>
                            <td>{{ table.size_mb }}</td>
                            <td>{{ table.data_mb }}</td>
                            <td>{{ table.index_mb }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% endif %}
                
                {% elif report_type == 'custom' %}
                    <h2>Reporte: {{ report_name }}</h2>
                    
                    {% for query_name, result in results.items() %}
                        {% if not query_name.endswith('_summary') %}
                        <h3>{{ query_name.replace('_', ' ').title() }}</h3>
                        
                        {% if result %}
                            {% if result|length <= 50 %}
                            <table>
                                <tr>
                                {% for key in result[0].keys() %}
                                    <th>{{ key }}</th>
                                {% endfor %}
                                </tr>
                                {% for row in result %}
                                <tr>
                                {% for value in row.values() %}
                                    <td>{{ value }}</td>
                                {% endfor %}
                                </tr>
                                {% endfor %}
                            </table>
                            {% else %}
                            <p>Resultado con {{ result|length }} filas (demasiadas para mostrar en tabla)</p>
                            {% endif %}
                        {% else %}
                            <p>Sin resultados</p>
                        {% endif %}
                        {% endif %}
                    {% endfor %}
                {% endif %}
                
                <!-- Gráficos -->
                {% if charts %}
                <h2>Visualizaciones</h2>
                {% for chart_name, chart_html in charts.items() %}
                <div class="chart-container">
                    <h3>{{ chart_name.replace('_', ' ').title() }}</h3>
                    {{ chart_html|safe }}
                </div>
                {% endfor %}
                {% endif %}
                
                <div style="margin-top: 40px; text-align: center; color: #666; font-size: 12px;">
                    <p>Generado por Agente de Automatización SQL - {{ timestamp }}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Configurar datos del template
        template_data = report_data.copy()
        
        if report_type == 'database_health':
            template_data['report_title'] = 'Reporte de Salud de Base de Datos'
        elif report_type == 'performance':
            template_data['report_title'] = 'Reporte de Rendimiento'
        elif report_type == 'custom':
            template_data['report_title'] = f'Reporte Personalizado: {report_data.get("report_name", "Sin Nombre")}'
        
        template_data['report_type'] = report_type
        
        # Renderizar template
        template = Template(html_template)
        return template.render(**template_data)
    
    def schedule_reports(self):
        """Programa la generación automática de reportes"""
        # Esta función sería llamada por el scheduler principal
        self.logger.info("Ejecutando reportes programados")
        
        try:
            # Generar reporte de salud
            self.generate_database_health_report()
            
            # Generar reporte de rendimiento semanal
            if datetime.now().weekday() == 0:  # Lunes
                self.generate_performance_report(7)
            
        except Exception as e:
            self.logger.error(f"Error en reportes programados: {e}")