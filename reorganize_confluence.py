#!/usr/bin/env python3
"""
Reorganizar documentación de GCP Knowledge Base
"""

from confluence_integration import ConfluenceClient
from confluence_config import CONFLUENCE_SPACE_KEY
import requests
from datetime import datetime

# Definición de categorías y sus páginas
CATEGORIES = {
    "Gestión y Acceso": {
        "emoji": "🔐",
        "description": "Gestión de usuarios, accesos, entornos y formación en GCP",
        "pages": [
            162302464,  # Gestión de acceso y usuarios
            162273179,  # Gestión de entorno
            162305550,  # Automatizaciones
            158879925,  # Formación GCP
        ]
    },
    "Servicios Cloudera": {
        "emoji": "☁️",
        "description": "Instalación, configuración y uso de servicios Cloudera (KNOX, HDFS, etc.)",
        "pages": [
            298975547,  # Servicios cloudera
            123526867,  # Instalación y configuración del servicio de KNOX
            1643062,    # Pruebas con una conexión JDBC utilizando KNOX
            123523967,  # Ejecutar aplicaciones yarn con motor de spark hacia buckets
            143929342,  # Pruebas de lectura de una ruta HDFS utilizando KNOX y Spark
            123526865,  # Pruebas de lectura y escritura via WebHDFS y Knox
        ]
    },
    "Bases de Datos y Conectores": {
        "emoji": "🗄️",
        "description": "Configuración y uso de bases de datos y conectores en GCP",
        "pages": [
            176662360,  # MySQL GCP
            1682361,    # Utilizar conector BigQuery desde GCP
        ]
    },
    "Troubleshooting": {
        "emoji": "🐛",
        "description": "Errores conocidos, problemas comunes y sus soluciones",
        "pages": [
            123524629,  # ERRORES CONOCIDOS ENTORNOS GCP
            196616437,  # Errores de instalación de zeppelin y solución
            298222805,  # ERRORES INFRA CDP 7.3.1
            303989652,  # Problemas cuando KNOX no arranca
        ]
    },
    "Migraciones y Upgrades": {
        "emoji": "🚀",
        "description": "Procesos de migración y actualización de entornos GCP",
        "pages": [
            123522640,  # Migración GCP - Infraestructura
            215289599,  # Upgrade entorno GCP PRE 7.2.18 -> 7.3.1
            259948892,  # Creación de un datahub completo en 7.3.1
            332301896,  # Migración SOLR GCP - Pruebas
        ]
    },
    "Almacenamiento": {
        "emoji": "💾",
        "description": "Gestión de buckets, HDFS y sistemas de almacenamiento",
        "pages": [
            197788621,  # Buckets en GCP
            123526111,  # Instalar un File Integrity Monitor (FIM)
        ]
    },
    "Rendimiento y Optimización": {
        "emoji": "⚡",
        "description": "Optimización de rendimiento, benchmarking y best practices",
        "pages": [
            269977106,  # Pruebas con 2 tipos de nodos de computo y YARN NodeLabels
            457540377,  # Pruebas de rendimiento / Benchmarking Clusters en GCP
            479527289,  # YARN - Colas y best practices SSPP
        ]
    },
    "Documentación y Checklists": {
        "emoji": "📚",
        "description": "Checklists, guías y documentación de referencia",
        "pages": [
            174662098,  # Checklist GCP DEV
            144973910,  # Resolución de dudas infraestructura SSPP
        ]
    },
    "Análisis y Predicción": {
        "emoji": "📊",
        "description": "Herramientas de análisis, monitorización y predicción",
        "pages": [
            726008509,  # CDP Tools - Sistema de Análisis y Predicción
        ]
    }
}

GCP_KB_PAGE_ID = "162433680"


def create_category_pages(client):
    """Crear páginas organizadoras para cada categoría"""

    print("\n" + "=" * 80)
    print("PASO 1: Creando Páginas Organizadoras")
    print("=" * 80)

    category_ids = {}

    for category_name, category_info in CATEGORIES.items():
        emoji = category_info["emoji"]
        description = category_info["description"]

        # Contenido de la página organizadora
        content = f"""
<ac:structured-macro ac:name="info">
    <ac:rich-text-body>
        <p><strong>Categoría:</strong> {emoji} {category_name}</p>
        <p><strong>Descripción:</strong> {description}</p>
        <p><strong>Total de páginas:</strong> {len(category_info['pages'])}</p>
    </ac:rich-text-body>
</ac:structured-macro>

<h2>{emoji} {category_name}</h2>

<p>{description}</p>

<hr/>

<h3>Páginas en esta categoría:</h3>

<ac:structured-macro ac:name="children" ac:schema-version="2" data-layout="default">
    <ac:parameter ac:name="depth">1</ac:parameter>
    <ac:parameter ac:name="all">true</ac:parameter>
    <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>

<hr/>

<p><em>Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
"""

        title = f"GCP - {category_name}"

        print(f"\nCreando: {title}")

        # Verificar si ya existe
        existing = client.get_page_by_title(CONFLUENCE_SPACE_KEY, title)

        if existing:
            print(f"  [INFO] Ya existe, actualizando...")
            page_id = existing['id']
            current_version = existing['version']['number']
            result = client.update_page(page_id, title, content, current_version)
        else:
            print(f"  [INFO] Creando nueva página...")
            result = client.create_page(
                CONFLUENCE_SPACE_KEY,
                title,
                content,
                parent_id=GCP_KB_PAGE_ID
            )

        if result:
            category_ids[category_name] = result['id']
            print(f"  [OK] ID: {result['id']}")
        else:
            print(f"  [ERROR] Falló la creación")

    return category_ids


def move_pages_to_categories(client, category_ids):
    """Mover páginas existentes a sus categorías"""

    print("\n" + "=" * 80)
    print("PASO 2: Reorganizando Páginas Existentes")
    print("=" * 80)

    moved_count = 0
    failed_count = 0

    for category_name, category_info in CATEGORIES.items():
        if category_name not in category_ids:
            print(f"\n[WARNING] Categoría {category_name} no tiene ID, saltando...")
            continue

        parent_id = category_ids[category_name]

        print(f"\n{category_info['emoji']} {category_name} (ID: {parent_id})")
        print(f"  Moviendo {len(category_info['pages'])} páginas...")

        for page_id in category_info['pages']:
            try:
                # Obtener página actual
                page = client.get_page_content(str(page_id))

                if not page:
                    print(f"    [ERROR] No se pudo obtener página {page_id}")
                    failed_count += 1
                    continue

                title = page.get('title', 'Sin título')
                current_version = page.get('version', {}).get('number', 1)
                content = page.get('body', {}).get('storage', {}).get('value', '')

                # Actualizar la página con nuevo padre
                print(f"    Moviendo: {title[:50]}...")

                data = {
                    'version': {'number': current_version + 1},
                    'title': title,
                    'type': 'page',
                    'body': {
                        'storage': {
                            'value': content,
                            'representation': 'storage'
                        }
                    },
                    'ancestors': [{'id': parent_id}]  # Esto cambia el padre
                }

                response = requests.put(
                    f"{client.api_url}/content/{page_id}",
                    auth=client.auth,
                    headers=client.headers,
                    json=data
                )

                if response.status_code == 200:
                    print(f"      [OK] Movida exitosamente")
                    moved_count += 1
                else:
                    print(f"      [ERROR] Falló: {response.status_code}")
                    failed_count += 1

            except Exception as e:
                print(f"    [ERROR] Error con página {page_id}: {e}")
                failed_count += 1

    print(f"\n  Total movidas: {moved_count}")
    print(f"  Total fallidas: {failed_count}")

    return moved_count, failed_count


def update_main_page(client, category_ids):
    """Actualizar página principal con índice mejorado"""

    print("\n" + "=" * 80)
    print("PASO 3: Actualizando Página Principal")
    print("=" * 80)

    # Contenido nuevo para la página principal
    content = f"""
<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="bgColor">#deebff</ac:parameter>
    <ac:rich-text-body>
        <h1>📚 GCP Knowledge Base</h1>
        <p>Base de conocimiento completa sobre Google Cloud Platform y Cloudera CDP</p>
        <p><em>Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
    </ac:rich-text-body>
</ac:structured-macro>

<h2>🗂️ Categorías de Documentación</h2>

<p>La documentación está organizada en las siguientes categorías temáticas:</p>

<table>
    <tr>
        <th>Categoría</th>
        <th>Descripción</th>
        <th>Páginas</th>
    </tr>
"""

    # Agregar fila por cada categoría
    for category_name, category_info in CATEGORIES.items():
        emoji = category_info['emoji']
        description = category_info['description']
        page_count = len(category_info['pages'])
        category_id = category_ids.get(category_name, '')

        if category_id:
            link = f'<a href="/wiki/spaces/{CONFLUENCE_SPACE_KEY}/pages/{category_id}">GCP - {category_name}</a>'
        else:
            link = f"GCP - {category_name}"

        content += f"""
    <tr>
        <td><strong>{emoji} {link}</strong></td>
        <td>{description}</td>
        <td>{page_count}</td>
    </tr>
"""

    content += """
</table>

<hr/>

<h2>📊 Estadísticas</h2>

<ul>
"""

    total_pages = sum(len(cat['pages']) for cat in CATEGORIES.values())
    total_categories = len(CATEGORIES)

    content += f"""
    <li><strong>Total de categorías:</strong> {total_categories}</li>
    <li><strong>Total de páginas:</strong> {total_pages}</li>
    <li><strong>Última reorganización:</strong> {datetime.now().strftime('%Y-%m-%d')}</li>
</ul>

<hr/>

<h2>🔍 Navegación Rápida</h2>

<ac:structured-macro ac:name="children" ac:schema-version="2" data-layout="default">
    <ac:parameter ac:name="depth">1</ac:parameter>
    <ac:parameter ac:name="all">true</ac:parameter>
    <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>

<hr/>

<ac:structured-macro ac:name="tip">
    <ac:rich-text-body>
        <p><strong>💡 Consejo:</strong> Usa el buscador de Confluence o navega por las categorías para encontrar la documentación que necesitas.</p>
    </ac:rich-text-body>
</ac:structured-macro>
"""

    print("\nActualizando GCP Knowledge Base...")

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
            print("[OK] Página principal actualizada")
            return True
        else:
            print("[ERROR] Falló la actualización")
            return False
    else:
        print("[ERROR] No se pudo obtener la página principal")
        return False


def main():
    """Ejecutar reorganización completa"""

    print("=" * 80)
    print("REORGANIZACIÓN DE GCP KNOWLEDGE BASE")
    print("=" * 80)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Categorías a crear: {len(CATEGORIES)}")

    total_pages = sum(len(cat['pages']) for cat in CATEGORIES.values())
    print(f"Páginas a reorganizar: {total_pages}")

    input("\nPresiona ENTER para continuar...")

    client = ConfluenceClient()

    # Paso 1: Crear categorías
    category_ids = create_category_pages(client)

    # Paso 2: Mover páginas
    moved, failed = move_pages_to_categories(client, category_ids)

    # Paso 3: Actualizar página principal
    main_updated = update_main_page(client, category_ids)

    # Resumen final
    print("\n" + "=" * 80)
    print("REORGANIZACIÓN COMPLETADA")
    print("=" * 80)
    print(f"\nCategorías creadas: {len(category_ids)}/{len(CATEGORIES)}")
    print(f"Páginas movidas: {moved}/{total_pages}")
    print(f"Páginas fallidas: {failed}")
    print(f"Página principal actualizada: {'Sí' if main_updated else 'No'}")

    print("\n" + "=" * 80)
    print("URL: https://si-cognitio.atlassian.net/wiki/spaces/ITBIGD/pages/162433680")
    print("=" * 80)


if __name__ == "__main__":
    main()
