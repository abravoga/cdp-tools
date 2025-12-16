#!/usr/bin/env python3
"""
Actualizar página principal con índice detallado
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
    print("ACTUALIZANDO PAGINA PRINCIPAL CON INDICE DETALLADO")
    print("="*80)

    client = ConfluenceClient()

    # Contenido HTML mejorado
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

<h2>Categorias de Documentacion</h2>

<p>Explora la documentacion navegando por las categorias tematicas. Cada categoria incluye guias detalladas, ejemplos practicos y soluciones a problemas comunes.</p>

<hr/>
"""

    # Crear sección expandible para cada categoría
    for cat in CATEGORIES:
        emoji = cat["emoji"]
        name = cat["name"]
        cat_id = cat["id"]
        description = cat["description"]
        pages = cat["pages"]
        what_find = cat["what_find"]
        keywords = cat["keywords"]

        content += f"""
<ac:structured-macro ac:name="expand">
    <ac:parameter ac:name="title">{emoji} GCP - {name} ({pages} paginas)</ac:parameter>
    <ac:rich-text-body>

        <p><strong>Descripcion:</strong> {description}</p>

        <h4>Que encontraras:</h4>
        <ul>
"""

        for item in what_find:
            content += f"            <li>{item}</li>\n"

        content += f"""
        </ul>

        <p><strong>Palabras clave:</strong> <em>{keywords}</em></p>

        <p><strong><a href="/wiki/spaces/ITBIGD/pages/{cat_id}">Ir a GCP - {name} →</a></strong></p>

    </ac:rich-text-body>
</ac:structured-macro>

<hr/>
"""

    # Agregar tabla resumen
    total_pages = sum(c["pages"] for c in CATEGORIES)

    content += f"""
<h2>Resumen por Categoria</h2>

<table>
    <tr>
        <th>Categoria</th>
        <th>Descripcion</th>
        <th>Paginas</th>
        <th>Enlace</th>
    </tr>
"""

    for cat in CATEGORIES:
        link = f'<a href="/wiki/spaces/ITBIGD/pages/{cat["id"]}">Ver →</a>'
        content += f"""
    <tr>
        <td><strong>{cat["emoji"]} GCP - {cat["name"]}</strong></td>
        <td>{cat["description"]}</td>
        <td>{cat["pages"]}</td>
        <td>{link}</td>
    </tr>
"""

    content += f"""
</table>

<hr/>

<h2>Estadisticas</h2>

<ac:structured-macro ac:name="info">
    <ac:rich-text-body>
        <ul>
            <li><strong>Total de categorias:</strong> {len(CATEGORIES)}</li>
            <li><strong>Total de paginas:</strong> {total_pages}</li>
            <li><strong>Ultima reorganizacion:</strong> {datetime.now().strftime('%Y-%m-%d')}</li>
            <li><strong>Cobertura:</strong> Infraestructura, Servicios, BD, Migraciones, Troubleshooting, Optimizacion</li>
        </ul>
    </ac:rich-text-body>
</ac:structured-macro>

<hr/>

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
        <p><strong>Navegacion directa:</strong> Usa la tabla de enlaces directos para ir rapidamente a cada categoria</p>
    </ac:rich-text-body>
</ac:structured-macro>

<hr/>

<ac:structured-macro ac:name="note">
    <ac:rich-text-body>
        <p><strong>Contribuir:</strong> Si tienes documentacion nueva o mejoras, contacta al equipo ITBigData para agregarla a la categoria correspondiente.</p>
    </ac:rich-text-body>
</ac:structured-macro>
"""

    print("\nActualizando GCP Knowledge Base con indice detallado...")

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
            print("[OK] Pagina principal actualizada con indice detallado")
            print(f"\nURL: https://si-cognitio.atlassian.net/wiki/spaces/ITBIGD/pages/{GCP_KB_PAGE_ID}")
            print("\n" + "="*80)
            print("MEJORAS INCLUIDAS:")
            print("="*80)
            print("  - Secciones expandibles por cada categoria")
            print("  - Lista detallada de contenidos en cada categoria")
            print("  - Palabras clave para facilitar busquedas")
            print("  - Enlaces directos a cada categoria")
            print("  - Tabla resumen con todas las categorias")
            print("  - Guia de uso de la base de conocimiento")
            print("  - Seccion de como contribuir")
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
