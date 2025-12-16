#!/usr/bin/env python3
"""
Sincronizar documentación del proyecto CDP con Confluence
"""

import os
from confluence_integration import ConfluenceClient, markdown_to_confluence

try:
    from confluence_config import (
        CONFLUENCE_SPACE_KEY,
        CDP_PARENT_PAGE_TITLE,
        CDP_PARENT_PAGE_ID
    )
except ImportError:
    print("[ERROR] No se encontró confluence_config.py")
    print("Crea el archivo basado en confluence_config.example.py")
    exit(1)


def read_file(filepath):
    """Leer contenido de un archivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Error leyendo {filepath}: {e}")
        return None


def sync_documentation():
    """Sincronizar toda la documentación con Confluence"""

    print("=" * 80)
    print("Sincronización de Documentación CDP con Confluence")
    print("=" * 80)

    # Crear cliente
    client = ConfluenceClient()

    # Probar conexión
    print("\n1. Probando conexión con Confluence...")
    if not client.test_connection():
        print("[ERROR] No se pudo conectar con Confluence")
        return False

    # Buscar o crear página padre
    print(f"\n2. Buscando página padre: '{CDP_PARENT_PAGE_TITLE}'...")
    parent_page = client.get_page_by_title(CONFLUENCE_SPACE_KEY, CDP_PARENT_PAGE_TITLE)

    if not parent_page:
        print(f"   Página padre no encontrada. Creando '{CDP_PARENT_PAGE_TITLE}'...")
        parent_content = """
        <h1>CDP Tools - Sistema de Análisis y Predicción</h1>
        <p>Esta página contiene toda la documentación del sistema CDP Tools.</p>
        <p>Sistema completo de análisis, visualización y predicción de consumo de créditos CDP con Machine Learning.</p>
        <h2>Características Principales</h2>
        <ul>
            <li>Ingesta automática de datos CDP</li>
            <li>10 dashboards en Kibana con 40+ visualizaciones</li>
            <li>Sistema de predicciones ML para próximos 7 días</li>
            <li>Automatización completa con scripts</li>
        </ul>
        """
        parent_page = client.create_page(
            CONFLUENCE_SPACE_KEY,
            CDP_PARENT_PAGE_TITLE,
            parent_content
        )
        if not parent_page:
            print("[ERROR] No se pudo crear página padre")
            return False

    parent_id = parent_page['id']
    print(f"   [OK] Página padre encontrada/creada (ID: {parent_id})")

    # Documentos a sincronizar
    docs_to_sync = [
        {
            'file': 'README.md',
            'title': 'CDP Tools - README Principal',
            'description': 'Documentación principal del proyecto'
        },
        {
            'file': 'INICIO_RAPIDO.md',
            'title': 'CDP Tools - Inicio Rápido',
            'description': 'Guía de inicio rápido'
        },
        {
            'file': 'RESUMEN_COMPLETO.md',
            'title': 'CDP Tools - Resumen Completo',
            'description': 'Documentación completa del sistema'
        },
        {
            'file': 'DASHBOARDS_KIBANA.md',
            'title': 'CDP Tools - Dashboards de Kibana',
            'description': 'Listado de dashboards y visualizaciones'
        }
    ]

    # Sincronizar cada documento
    print("\n3. Sincronizando documentos...")
    synced_count = 0
    failed_count = 0

    for doc in docs_to_sync:
        print(f"\n   Procesando: {doc['file']}...")

        # Leer archivo
        content = read_file(doc['file'])
        if not content:
            print(f"   [ERROR] No se pudo leer {doc['file']}")
            failed_count += 1
            continue

        # Convertir Markdown a Confluence HTML
        confluence_content = markdown_to_confluence(content)

        # Agregar encabezado
        header = f"""
        <ac:structured-macro ac:name="info">
            <ac:rich-text-body>
                <p><strong>Última sincronización:</strong> {os.popen('date /t').read().strip()}</p>
                <p><strong>Fuente:</strong> {doc['file']}</p>
                <p><strong>Descripción:</strong> {doc['description']}</p>
            </ac:rich-text-body>
        </ac:structured-macro>
        <hr/>
        """

        full_content = header + confluence_content

        # Crear o actualizar página
        result = client.create_or_update_page(
            CONFLUENCE_SPACE_KEY,
            doc['title'],
            full_content,
            parent_id
        )

        if result:
            synced_count += 1
            page_url = f"{client.base_url}/wiki/spaces/{CONFLUENCE_SPACE_KEY}/pages/{result['id']}"
            print(f"   [OK] Sincronizado: {doc['title']}")
            print(f"        URL: {page_url}")
        else:
            failed_count += 1
            print(f"   [ERROR] Falló: {doc['title']}")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE SINCRONIZACIÓN")
    print("=" * 80)
    print(f"  Documentos sincronizados: {synced_count}/{len(docs_to_sync)}")
    print(f"  Fallidos: {failed_count}")

    if synced_count > 0:
        parent_url = f"{client.base_url}/wiki/spaces/{CONFLUENCE_SPACE_KEY}/pages/{parent_id}"
        print(f"\n  Página principal: {parent_url}")

    print("=" * 80)

    return synced_count > 0


if __name__ == "__main__":
    success = sync_documentation()
    exit(0 if success else 1)
