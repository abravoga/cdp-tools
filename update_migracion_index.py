#!/usr/bin/env python3
"""
Actualizar página de Migración GCP con índice de páginas hijas
"""

from confluence_integration import ConfluenceClient
from datetime import datetime
import requests

MIGRACION_PAGE_ID = "123522823"


def get_child_pages(client, page_id):
    """Obtener todas las páginas hijas"""
    response = requests.get(
        f"{client.api_url}/content/{page_id}/child/page",
        auth=client.auth,
        headers=client.headers,
        params={'expand': 'version', 'limit': 100}
    )

    if response.status_code == 200:
        return response.json().get('results', [])
    return []


def categorize_pages(pages):
    """Categorizar páginas por tipo"""
    categories = {
        'Use Cases': [],
        'Gestión y Equipo': [],
        'Inventarios': [],
        'Otros': []
    }

    for page in pages:
        title = page.get('title', '')

        if 'UC' in title or 'Use Case' in title:
            categories['Use Cases'].append(page)
        elif any(word in title for word in ['Equipo', 'Gestión', 'entorno']):
            categories['Gestión y Equipo'].append(page)
        elif 'Inventario' in title or 'MSCK' in title:
            categories['Inventarios'].append(page)
        else:
            categories['Otros'].append(page)

    return categories


def main():
    print("="*80)
    print("ACTUALIZANDO INDICE DE MIGRACION GCP")
    print("="*80)

    client = ConfluenceClient()

    # Obtener páginas hijas
    print("\nObteniendo paginas hijas...")
    child_pages = get_child_pages(client, MIGRACION_PAGE_ID)
    print(f"Total de paginas encontradas: {len(child_pages)}")

    # Categorizar
    categories = categorize_pages(child_pages)

    # Crear contenido
    content = f"""
<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="bgColor">#deebff</ac:parameter>
    <ac:rich-text-body>
        <h1>Migracion GCP</h1>
        <p><strong>Documentacion completa del proceso de migracion a Google Cloud Platform</strong></p>
        <p>Total de paginas: {len(child_pages)}</p>
        <p><em>Ultima actualizacion: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
    </ac:rich-text-body>
</ac:structured-macro>

<h2>Indice de Contenidos</h2>
"""

    # Agregar cada categoría
    for category_name, pages in categories.items():
        if not pages:
            continue

        content += f"""
<h3>{category_name} ({len(pages)} paginas)</h3>

<ul>
"""

        # Ordenar páginas alfabéticamente
        sorted_pages = sorted(pages, key=lambda p: p.get('title', ''))

        for page in sorted_pages:
            page_id = page.get('id')
            title = page.get('title')
            content += f'    <li><a href="/wiki/spaces/ITBIGD/pages/{page_id}">{title}</a></li>\n'

        content += "</ul>\n\n"

    # Agregar macro de children al final
    content += """
<hr/>

<h3>Vista de arbol completa</h3>

<ac:structured-macro ac:name="children" ac:schema-version="2" data-layout="default">
    <ac:parameter ac:name="depth">2</ac:parameter>
    <ac:parameter ac:name="all">true</ac:parameter>
    <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>

<hr/>

<ac:structured-macro ac:name="info">
    <ac:rich-text-body>
        <p><strong>Nota:</strong> Esta pagina contiene el indice completo de toda la documentacion relacionada con la migracion GCP.</p>
        <p>Utiliza el indice categorizado arriba para navegacion rapida o la vista de arbol para ver la estructura completa.</p>
    </ac:rich-text-body>
</ac:structured-macro>
"""

    print("\nActualizando pagina...")

    # Obtener versión actual
    page = client.get_page_content(MIGRACION_PAGE_ID)

    if page:
        current_version = page.get('version', {}).get('number', 1)
        result = client.update_page(
            MIGRACION_PAGE_ID,
            "Migracion GCP",
            content,
            current_version
        )

        if result:
            print("[OK] Pagina actualizada con indice completo")
            print(f"\nURL: https://si-cognitio.atlassian.net/wiki/spaces/ITBIGD/pages/{MIGRACION_PAGE_ID}")
            print("\n" + "="*80)
            print("CONTENIDO AGREGADO:")
            print("="*80)
            for category_name, pages in categories.items():
                if pages:
                    print(f"  - {category_name}: {len(pages)} paginas")
            print("  - Vista de arbol completa (macro children)")
            print("="*80)
            return True
        else:
            print("[ERROR] Fallo la actualizacion")
            return False
    else:
        print("[ERROR] No se pudo obtener la pagina")
        return False


if __name__ == "__main__":
    main()
