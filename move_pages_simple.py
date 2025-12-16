#!/usr/bin/env python3
"""
Mover páginas a categorías (sin emojis)
"""

from confluence_integration import ConfluenceClient
import requests

# IDs de categorías ya creadas
CATEGORY_IDS = {
    'Gestión y Acceso': '724730780',
    'Servicios Cloudera': '725058414',
    'Bases de Datos y Conectores': '726073900',
    'Troubleshooting': '725582641',
    'Migraciones y Upgrades': '723552127',
    'Almacenamiento': '725418739',
    'Rendimiento y Optimización': '725942847',
    'Documentación y Checklists': '724894560',
    'Análisis y Predicción': '725156729'
}

# Mapeo de páginas a categorías
PAGE_MOVES = {
    '724730780': [162302464, 162273179, 162305550, 158879925],  # Gestión y Acceso
    '725058414': [298975547, 123526867, 1643062, 123523967, 143929342, 123526865],  # Servicios Cloudera
    '726073900': [176662360, 1682361],  # BD y Conectores
    '725582641': [123524629, 196616437, 298222805, 303989652],  # Troubleshooting
    '723552127': [123522640, 215289599, 259948892, 332301896],  # Migraciones
    '725418739': [197788621, 123526111],  # Almacenamiento
    '725942847': [269977106, 457540377, 479527289],  # Rendimiento
    '724894560': [174662098, 144973910],  # Documentación
    '725156729': [726008509]  # Análisis y Predicción
}


def move_page(client, page_id, new_parent_id):
    """Mover una página a un nuevo padre"""
    try:
        # Obtener página actual
        page = client.get_page_content(str(page_id))

        if not page:
            print(f"  [ERROR] No se pudo obtener pagina {page_id}")
            return False

        title = page.get('title', 'Sin titulo')[:60]
        current_version = page.get('version', {}).get('number', 1)
        content = page.get('body', {}).get('storage', {}).get('value', '')

        print(f"  Moviendo: {title}...")

        # Actualizar con nuevo padre
        data = {
            'version': {'number': current_version + 1},
            'title': page.get('title', 'Sin titulo'),
            'type': 'page',
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            },
            'ancestors': [{'id': new_parent_id}]
        }

        response = requests.put(
            f"{client.api_url}/content/{page_id}",
            auth=client.auth,
            headers=client.headers,
            json=data
        )

        if response.status_code == 200:
            print(f"    [OK] Movida")
            return True
        else:
            print(f"    [ERROR] Fallo: {response.status_code}")
            return False

    except Exception as e:
        print(f"  [ERROR] Excepcion: {e}")
        return False


def main():
    print("="*80)
    print("REORGANIZACION - PASO 2: MOVER PAGINAS")
    print("="*80)

    client = ConfluenceClient()

    moved_count = 0
    failed_count = 0
    total = sum(len(pages) for pages in PAGE_MOVES.values())

    print(f"\nTotal de paginas a mover: {total}")

    for parent_id, page_ids in PAGE_MOVES.items():
        print(f"\nCategoria (ID: {parent_id}): {len(page_ids)} paginas")

        for page_id in page_ids:
            if move_page(client, page_id, parent_id):
                moved_count += 1
            else:
                failed_count += 1

    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print(f"Movidas exitosamente: {moved_count}/{total}")
    print(f"Fallidas: {failed_count}")
    print("="*80)


if __name__ == "__main__":
    main()
