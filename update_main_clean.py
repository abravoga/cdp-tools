#!/usr/bin/env python3
"""
Actualizar página principal - versión limpia sin estadísticas ni tabla resumen
"""

from confluence_integration import ConfluenceClient
from datetime import datetime

GCP_KB_PAGE_ID = "162433680"

# Categorías con información detallada
CATEGORIES = [
    {
        "id": "724730780",
        "name": "Gestión y Acceso",
        "emoji": "🔐",
        "pages": 4,
        "description": "Gestión de usuarios, accesos, entornos y formación",
        "what_find": [
            "Configuración de permisos y roles de usuario",
            "Gestión de accesos a recursos GCP",
            "Automatizaciones de aprovisionamiento",
            "Materiales y guías de formación GCP"
        ],
        "keywords": "usuarios, permisos, IAM, accesos, formación"
    },
    {
        "id": "725058414",
        "name": "Servicios Cloudera",
        "emoji": "☁️",
        "pages": 6,
        "description": "Instalación, configuración y uso de servicios Cloudera",
        "what_find": [
            "Instalación y configuración de KNOX",
            "Pruebas de conexión JDBC con KNOX",
            "Acceso a HDFS mediante KNOX y Spark",
            "Configuración de WebHDFS",
            "Ejecución de aplicaciones YARN con buckets externos"
        ],
        "keywords": "KNOX, HDFS, WebHDFS, JDBC, Spark, YARN"
    },
    {
        "id": "726073900",
        "name": "Bases de Datos y Conectores",
        "emoji": "🗄️",
        "pages": 2,
        "description": "Configuración y uso de bases de datos y conectores",
        "what_find": [
            "Configuración de MySQL en GCP",
            "Uso del conector BigQuery desde CDP",
            "Conexiones a bases de datos externas",
            "Ejemplos de queries y optimizaciones"
        ],
        "keywords": "MySQL, BigQuery, conectores, SQL, bases de datos"
    },
    {
        "id": "725582641",
        "name": "Troubleshooting",
        "emoji": "🐛",
        "pages": 4,
        "description": "Errores conocidos, problemas comunes y soluciones",
        "what_find": [
            "Errores conocidos en entornos GCP",
            "Problemas de instalación de Zeppelin",
            "Errores de infraestructura CDP 7.3.1",
            "Soluciones cuando KNOX no arranca",
            "Acceso a Cloudera Manager en casos críticos"
        ],
        "keywords": "errores, troubleshooting, problemas, soluciones, debug"
    },
    {
        "id": "723552127",
        "name": "Migraciones y Upgrades",
        "emoji": "🚀",
        "pages": 4,
        "description": "Procesos de migración y actualización de entornos",
        "what_find": [
            "Proceso de migración de infraestructura a GCP",
            "Upgrade de CDP 7.2.18 a 7.3.1",
            "Creación de DataHub completo en 7.3.1",
            "Migración de SOLR a GCP",
            "Lecciones aprendidas y best practices"
        ],
        "keywords": "migración, upgrade, actualización, versiones, DataHub"
    },
    {
        "id": "725418739",
        "name": "Almacenamiento",
        "emoji": "💾",
        "pages": 2,
        "description": "Gestión de buckets, HDFS y sistemas de almacenamiento",
        "what_find": [
            "Configuración y gestión de buckets GCP",
            "File Integrity Monitor (FIM) para archivos AVRO",
            "Configuración de AIDE para contingencia",
            "Políticas de almacenamiento y lifecycle"
        ],
        "keywords": "buckets, storage, HDFS, AVRO, FIM, AIDE"
    },
    {
        "id": "725942847",
        "name": "Rendimiento y Optimización",
        "emoji": "⚡",
        "pages": 3,
        "description": "Optimización de rendimiento y best practices",
        "what_find": [
            "Pruebas con YARN NodeLabels y tipos de nodos",
            "Benchmarking de clusters en GCP",
            "Configuración de colas YARN",
            "Best practices para SSPP",
            "Optimización de recursos y costos"
        ],
        "keywords": "rendimiento, optimización, YARN, NodeLabels, benchmarking, colas"
    },
    {
        "id": "724894560",
        "name": "Documentación y Checklists",
        "emoji": "📚",
        "pages": 2,
        "description": "Checklists, guías y documentación de referencia",
        "what_find": [
            "Checklist para entornos GCP DEV",
            "Resolución de dudas sobre infraestructura SSPP",
            "Procedimientos estándar",
            "Guías de referencia rápida"
        ],
        "keywords": "checklist, guías, procedimientos, referencia, SSPP"
    },
    {
        "id": "725156729",
        "name": "Análisis y Predicción",
        "emoji": "📊",
        "pages": 1,
        "description": "Herramientas de análisis, monitorización y predicción",
        "what_find": [
            "CDP Tools - Sistema de análisis de consumo",
            "Dashboards de visualización en Kibana",
            "Predicciones ML de consumo futuro",
            "Monitorización de recursos y costos",
            "Repositorio GitHub del proyecto"
        ],
        "keywords": "análisis, predicción, ML, dashboards, Kibana, monitorización"
    }
]


def main():
    print("="*80)
    print("ACTUALIZANDO PAGINA PRINCIPAL - VERSION LIMPIA")
    print("="*80)

    client = ConfluenceClient()

    # Contenido HTML minimalista
    content = f"""
<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="bgColor">#deebff</ac:parameter>
    <ac:rich-text-body>
        <h1>GCP Knowledge Base</h1>
        <p><strong>Base de conocimiento completa sobre Google Cloud Platform y Cloudera CDP</strong></p>
        <p>Documentacion tecnica, guias, procedimientos y soluciones organizadas por categorias tematicas</p>
        <p><em>Ultima actualizacion: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
    </ac:rich-text-body>
</ac:structured-macro>

"""

    # Agregar solo navegación rápida y guía de uso (sin expandibles)
    content += """
<h2>Navegacion Rapida</h2>

<p>Todas las categorias y subcategorias disponibles:</p>

<ac:structured-macro ac:name="children" ac:schema-version="2" data-layout="default">
    <ac:parameter ac:name="depth">2</ac:parameter>
    <ac:parameter ac:name="all">true</ac:parameter>
    <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>

<hr/>

<h2>Como usar esta base de conocimiento</h2>

<ac:structured-macro ac:name="tip">
    <ac:rich-text-body>
        <p><strong>Buscar por tema:</strong> Navega por las categorias expandibles arriba para ver que contiene cada seccion</p>
        <p><strong>Buscar por palabra clave:</strong> Usa el buscador de Confluence (Ctrl+K) con las palabras clave listadas</p>
        <p><strong>Navegacion directa:</strong> Haz clic en los enlaces dentro de cada categoria expandible</p>
    </ac:rich-text-body>
</ac:structured-macro>

<hr/>

<ac:structured-macro ac:name="note">
    <ac:rich-text-body>
        <p><strong>Contribuir:</strong> Si tienes documentacion nueva o mejoras, contacta al equipo ITBigData para agregarla a la categoria correspondiente.</p>
    </ac:rich-text-body>
</ac:structured-macro>
"""

    print("\nActualizando GCP Knowledge Base (version limpia)...")

    # Obtener página actual
    page = client.get_page_content(GCP_KB_PAGE_ID)

    if page:
        current_version = page.get('version', {}).get('number', 1)
        result = client.update_page(
            GCP_KB_PAGE_ID,
            "GCP Knowledge Base",
            content,
            current_version
        )

        if result:
            print("[OK] Pagina principal actualizada")
            print(f"\nURL: https://si-cognitio.atlassian.net/wiki/spaces/ITBIGD/pages/{GCP_KB_PAGE_ID}")
            print("\n" + "="*80)
            print("CONTENIDO FINAL:")
            print("="*80)
            print("  - Panel informativo principal")
            print("  - Navegacion rapida (macro children)")
            print("  - Guia de uso")
            print("  - Seccion de contribucion")
            print("\n  ELIMINADO:")
            print("  - Categorias expandibles con detalles")
            print("  - Tabla resumen de categorias")
            print("  - Seccion de estadisticas")
            print("="*80)
            return True
        else:
            print("[ERROR] Fallo la actualizacion")
            return False
    else:
        print("[ERROR] No se pudo obtener la pagina principal")
        return False


if __name__ == "__main__":
    main()
