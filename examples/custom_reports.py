"""
Ejemplos de Reportes Personalizados para el Agente SQL
"""
from datetime import datetime, timedelta
import sys
import os

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager
from report_generator import ReportGenerator
from config import db_config

def ejemplo_reporte_ventas():
    """Ejemplo: Reporte de ventas por período"""
    
    # Consultas personalizadas para análisis de ventas
    consultas_ventas = {
        'ventas_diarias': """
            SELECT 
                DATE(fecha_venta) as fecha,
                COUNT(*) as num_ventas,
                SUM(total) as total_ventas,
                AVG(total) as promedio_venta
            FROM ventas 
            WHERE fecha_venta >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(fecha_venta)
            ORDER BY fecha DESC
        """,
        
        'productos_mas_vendidos': """
            SELECT 
                p.nombre as producto,
                p.categoria,
                COUNT(v.id) as cantidad_vendida,
                SUM(v.total) as ingresos_totales
            FROM ventas v
            JOIN productos p ON v.producto_id = p.id
            WHERE v.fecha_venta >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY p.id, p.nombre, p.categoria
            ORDER BY cantidad_vendida DESC
            LIMIT 20
        """,
        
        'ventas_por_vendedor': """
            SELECT 
                u.nombre as vendedor,
                u.departamento,
                COUNT(v.id) as num_ventas,
                SUM(v.total) as total_vendido,
                AVG(v.total) as promedio_por_venta
            FROM ventas v
            JOIN usuarios u ON v.vendedor_id = u.id
            WHERE v.fecha_venta >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY u.id, u.nombre, u.departamento
            ORDER BY total_vendido DESC
        """,
        
        'tendencia_mensual': """
            SELECT 
                YEAR(fecha_venta) as año,
                MONTH(fecha_venta) as mes,
                COUNT(*) as num_ventas,
                SUM(total) as total_mes,
                AVG(total) as promedio_mes
            FROM ventas 
            WHERE fecha_venta >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY YEAR(fecha_venta), MONTH(fecha_venta)
            ORDER BY año DESC, mes DESC
        """
    }
    
    return consultas_ventas

def ejemplo_reporte_usuarios():
    """Ejemplo: Reporte de actividad de usuarios"""
    
    consultas_usuarios = {
        'usuarios_activos': """
            SELECT 
                DATE(ultimo_acceso) as fecha,
                COUNT(DISTINCT id) as usuarios_activos,
                COUNT(DISTINCT CASE WHEN tipo_usuario = 'premium' THEN id END) as usuarios_premium,
                COUNT(DISTINCT CASE WHEN tipo_usuario = 'basico' THEN id END) as usuarios_basicos
            FROM usuarios 
            WHERE ultimo_acceso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(ultimo_acceso)
            ORDER BY fecha DESC
        """,
        
        'registros_nuevos': """
            SELECT 
                DATE(fecha_registro) as fecha,
                COUNT(*) as nuevos_registros,
                COUNT(CASE WHEN origen_registro = 'web' THEN 1 END) as desde_web,
                COUNT(CASE WHEN origen_registro = 'mobile' THEN 1 END) as desde_mobile,
                COUNT(CASE WHEN origen_registro = 'api' THEN 1 END) as desde_api
            FROM usuarios 
            WHERE fecha_registro >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(fecha_registro)
            ORDER BY fecha DESC
        """,
        
        'usuarios_por_region': """
            SELECT 
                pais,
                region,
                COUNT(*) as total_usuarios,
                COUNT(CASE WHEN ultimo_acceso >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as activos_semana,
                AVG(DATEDIFF(NOW(), fecha_registro)) as dias_promedio_antiguedad
            FROM usuarios 
            GROUP BY pais, region
            ORDER BY total_usuarios DESC
        """,
        
        'engagement_usuarios': """
            SELECT 
                tipo_usuario,
                COUNT(*) as total_usuarios,
                AVG(sesiones_totales) as promedio_sesiones,
                AVG(tiempo_total_minutos) as promedio_tiempo_minutos,
                COUNT(CASE WHEN ultimo_acceso >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as activos_ultima_semana
            FROM usuarios 
            GROUP BY tipo_usuario
            ORDER BY promedio_sesiones DESC
        """
    }
    
    return consultas_usuarios

def ejemplo_reporte_inventario():
    """Ejemplo: Reporte de gestión de inventario"""
    
    consultas_inventario = {
        'stock_bajo': """
            SELECT 
                p.codigo,
                p.nombre,
                p.categoria,
                i.cantidad_actual,
                i.stock_minimo,
                i.stock_maximo,
                (i.stock_minimo - i.cantidad_actual) as deficit,
                p.precio_unitario,
                (i.stock_minimo - i.cantidad_actual) * p.precio_unitario as valor_deficit
            FROM productos p
            JOIN inventario i ON p.id = i.producto_id
            WHERE i.cantidad_actual < i.stock_minimo
            ORDER BY deficit DESC
        """,
        
        'movimientos_inventario': """
            SELECT 
                DATE(m.fecha_movimiento) as fecha,
                m.tipo_movimiento,
                COUNT(*) as num_movimientos,
                SUM(m.cantidad) as cantidad_total,
                SUM(m.cantidad * p.precio_unitario) as valor_total
            FROM movimientos_inventario m
            JOIN productos p ON m.producto_id = p.id
            WHERE m.fecha_movimiento >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(m.fecha_movimiento), m.tipo_movimiento
            ORDER BY fecha DESC, tipo_movimiento
        """,
        
        'productos_sin_movimiento': """
            SELECT 
                p.codigo,
                p.nombre,
                p.categoria,
                i.cantidad_actual,
                p.precio_unitario,
                (i.cantidad_actual * p.precio_unitario) as valor_inmovilizado,
                MAX(m.fecha_movimiento) as ultimo_movimiento,
                DATEDIFF(NOW(), MAX(m.fecha_movimiento)) as dias_sin_movimiento
            FROM productos p
            JOIN inventario i ON p.id = i.producto_id
            LEFT JOIN movimientos_inventario m ON p.id = m.producto_id
            GROUP BY p.id, p.codigo, p.nombre, p.categoria, i.cantidad_actual, p.precio_unitario
            HAVING dias_sin_movimiento > 90 OR ultimo_movimiento IS NULL
            ORDER BY dias_sin_movimiento DESC, valor_inmovilizado DESC
        """,
        
        'rotacion_inventario': """
            SELECT 
                p.categoria,
                COUNT(DISTINCT p.id) as productos_categoria,
                SUM(i.cantidad_actual) as stock_total,
                SUM(i.cantidad_actual * p.precio_unitario) as valor_total,
                AVG(DATEDIFF(NOW(), COALESCE(m.ultima_salida, p.fecha_creacion))) as dias_promedio_rotacion
            FROM productos p
            JOIN inventario i ON p.id = i.producto_id
            LEFT JOIN (
                SELECT 
                    producto_id, 
                    MAX(fecha_movimiento) as ultima_salida
                FROM movimientos_inventario 
                WHERE tipo_movimiento = 'salida'
                GROUP BY producto_id
            ) m ON p.id = m.producto_id
            GROUP BY p.categoria
            ORDER BY dias_promedio_rotacion ASC
        """
    }
    
    return consultas_inventario

def ejemplo_reporte_financiero():
    """Ejemplo: Reporte financiero básico"""
    
    consultas_financiero = {
        'ingresos_mensuales': """
            SELECT 
                YEAR(fecha) as año,
                MONTH(fecha) as mes,
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) as ingresos,
                SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END) as gastos,
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE -monto END) as utilidad_neta
            FROM transacciones_financieras 
            WHERE fecha >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY YEAR(fecha), MONTH(fecha)
            ORDER BY año DESC, mes DESC
        """,
        
        'gastos_por_categoria': """
            SELECT 
                categoria,
                COUNT(*) as num_transacciones,
                SUM(monto) as total_gastado,
                AVG(monto) as promedio_por_transaccion,
                MIN(monto) as gasto_minimo,
                MAX(monto) as gasto_maximo
            FROM transacciones_financieras 
            WHERE tipo = 'gasto' 
            AND fecha >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
            GROUP BY categoria
            ORDER BY total_gastado DESC
        """,
        
        'flujo_caja_diario': """
            SELECT 
                DATE(fecha) as fecha,
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) as ingresos_dia,
                SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END) as gastos_dia,
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE -monto END) as flujo_neto_dia
            FROM transacciones_financieras 
            WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(fecha)
            ORDER BY fecha DESC
        """,
        
        'cuentas_por_cobrar': """
            SELECT 
                cliente,
                COUNT(*) as facturas_pendientes,
                SUM(monto_pendiente) as total_por_cobrar,
                MIN(fecha_vencimiento) as vencimiento_mas_proximo,
                MAX(DATEDIFF(NOW(), fecha_vencimiento)) as dias_vencido_maximo,
                AVG(DATEDIFF(NOW(), fecha_emision)) as dias_promedio_pendiente
            FROM cuentas_por_cobrar 
            WHERE estado = 'pendiente'
            GROUP BY cliente
            ORDER BY total_por_cobrar DESC
        """
    }
    
    return consultas_financiero

def generar_reporte_ejemplo():
    """Función principal para generar un reporte de ejemplo"""
    
    try:
        # Inicializar componentes
        db_manager = DatabaseManager(db_config)
        report_generator = ReportGenerator(db_manager)
        
        # Probar conexión
        if not db_manager.test_connection():
            print("❌ Error: No se pudo conectar a la base de datos")
            return
        
        print("✅ Conexión a base de datos establecida")
        
        # Seleccionar tipo de reporte
        print("\n📊 Tipos de reportes disponibles:")
        print("1. Reporte de Ventas")
        print("2. Reporte de Usuarios")
        print("3. Reporte de Inventario")
        print("4. Reporte Financiero")
        
        opcion = input("\nSelecciona el tipo de reporte (1-4): ").strip()
        
        # Obtener consultas según la opción
        if opcion == "1":
            consultas = ejemplo_reporte_ventas()
            nombre_reporte = "Análisis de Ventas - 30 días"
        elif opcion == "2":
            consultas = ejemplo_reporte_usuarios()
            nombre_reporte = "Actividad de Usuarios - 30 días"
        elif opcion == "3":
            consultas = ejemplo_reporte_inventario()
            nombre_reporte = "Gestión de Inventario"
        elif opcion == "4":
            consultas = ejemplo_reporte_financiero()
            nombre_reporte = "Reporte Financiero"
        else:
            print("❌ Opción no válida")
            return
        
        print(f"\n🔄 Generando {nombre_reporte}...")
        
        # Generar reporte personalizado
        resultado = report_generator.generate_custom_report(consultas, nombre_reporte)
        
        print(f"✅ Reporte generado exitosamente!")
        print(f"📁 Consultas ejecutadas: {len(resultado.get('results', {}))}")
        print(f"📊 Gráficos generados: {len(resultado.get('charts', {}))}")
        print(f"⏰ Timestamp: {resultado.get('timestamp', 'N/A')}")
        
        # Mostrar resumen de resultados
        print(f"\n📈 Resumen de datos:")
        for query_name, result in resultado.get('results', {}).items():
            if not query_name.endswith('_summary') and isinstance(result, list):
                print(f"  • {query_name.replace('_', ' ').title()}: {len(result)} registros")
        
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")
    
    finally:
        # Cerrar conexiones
        if 'db_manager' in locals():
            db_manager.close_pool()

def mostrar_consulta_ejemplo():
    """Muestra un ejemplo de consulta personalizada"""
    
    print("\n📝 Ejemplo de consulta personalizada:")
    print("=" * 50)
    
    consulta_ejemplo = """
    -- Análisis de rendimiento de productos por mes
    SELECT 
        p.categoria,
        p.nombre as producto,
        YEAR(v.fecha_venta) as año,
        MONTH(v.fecha_venta) as mes,
        COUNT(v.id) as unidades_vendidas,
        SUM(v.total) as ingresos_totales,
        AVG(v.total) as precio_promedio,
        
        -- Calcular ranking dentro de la categoría
        RANK() OVER (
            PARTITION BY p.categoria, YEAR(v.fecha_venta), MONTH(v.fecha_venta) 
            ORDER BY SUM(v.total) DESC
        ) as ranking_categoria,
        
        -- Calcular porcentaje del total de la categoría
        ROUND(
            SUM(v.total) * 100.0 / SUM(SUM(v.total)) OVER (
                PARTITION BY p.categoria, YEAR(v.fecha_venta), MONTH(v.fecha_venta)
            ), 2
        ) as porcentaje_categoria
        
    FROM ventas v
    JOIN productos p ON v.producto_id = p.id
    WHERE v.fecha_venta >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
    GROUP BY p.categoria, p.id, p.nombre, YEAR(v.fecha_venta), MONTH(v.fecha_venta)
    HAVING unidades_vendidas >= 5  -- Solo productos con ventas significativas
    ORDER BY año DESC, mes DESC, categoria, ranking_categoria
    """
    
    print(consulta_ejemplo)
    print("=" * 50)
    
    print("\n💡 Características de esta consulta:")
    print("  • Usa funciones de ventana (RANK, SUM OVER)")
    print("  • Calcula métricas agregadas y porcentajes")
    print("  • Incluye filtros para datos relevantes")
    print("  • Ordena resultados de manera lógica")
    print("  • Usa alias descriptivos para claridad")

if __name__ == "__main__":
    print("🤖 Ejemplos de Reportes Personalizados - Agente SQL")
    print("=" * 60)
    
    print("\nOpciones disponibles:")
    print("1. Generar reporte de ejemplo")
    print("2. Mostrar consulta de ejemplo")
    print("3. Salir")
    
    while True:
        opcion = input("\nSelecciona una opción (1-3): ").strip()
        
        if opcion == "1":
            generar_reporte_ejemplo()
            break
        elif opcion == "2":
            mostrar_consulta_ejemplo()
            break
        elif opcion == "3":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")