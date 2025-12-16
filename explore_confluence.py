#!/usr/bin/env python3
"""
Explorar contenido del espacio ITBIGD en Confluence
"""

from confluence_integration import ConfluenceClient
from confluence_config import CONFLUENCE_SPACE_KEY

def explore_space():
    """Explorar el espacio de Confluence"""

    print("=" * 80)
    print(f"Explorando Espacio: {CONFLUENCE_SPACE_KEY}")
    print("=" * 80)

    client = ConfluenceClient()

    # Obtener información del espacio
    print(f"\n1. Obteniendo información del espacio {CONFLUENCE_SPACE_KEY}...")
    try:
        response = client.auth.__self__.get(
            f"{client.api_url}/space/{CONFLUENCE_SPACE_KEY}",
            auth=client.auth,
            headers=client.headers,
            params={'expand': 'description,homepage'}
        )

        if response.status_code == 200:
            space = response.json()
            print(f"\n   Nombre: {space.get('name', 'N/A')}")
            print(f"   Key: {space.get('key', 'N/A')}")
            print(f"   Tipo: {space.get('type', 'N/A')}")

            if 'homepage' in space:
                print(f"   Página principal: {space['homepage'].get('title', 'N/A')}")
        else:
            print(f"   [WARNING] No se pudo obtener info del espacio: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Listar páginas del espacio
    print(f"\n2. Listando páginas en {CONFLUENCE_SPACE_KEY}...")
    try:
        import requests
        response = requests.get(
            f"{client.api_url}/content",
            auth=client.auth,
            headers=client.headers,
            params={
                'spaceKey': CONFLUENCE_SPACE_KEY,
                'type': 'page',
                'limit': 20,
                'expand': 'version,space'
            }
        )

        if response.status_code == 200:
            data = response.json()
            pages = data.get('results', [])

            if pages:
                print(f"\n   Páginas encontradas ({len(pages)}):")
                for i, page in enumerate(pages, 1):
                    title = page.get('title', 'Sin título')
                    page_id = page.get('id', 'N/A')
                    version = page.get('version', {}).get('number', 'N/A')
                    print(f"\n   {i}. {title}")
                    print(f"      ID: {page_id}")
                    print(f"      Versión: {version}")
                    print(f"      URL: {client.base_url}/wiki/spaces/{CONFLUENCE_SPACE_KEY}/pages/{page_id}")
            else:
                print("\n   [INFO] No se encontraron páginas en este espacio")
                print("   El espacio está vacío o no tienes permisos de lectura")
        else:
            print(f"   [ERROR] Error listando páginas: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    print("\n" + "=" * 80)
    print("Exploración completada")
    print("=" * 80)

if __name__ == "__main__":
    explore_space()
