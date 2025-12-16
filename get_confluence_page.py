#!/usr/bin/env python3
"""
Obtener información de una página específica de Confluence
"""

import requests
import sys
from confluence_integration import ConfluenceClient

def get_page_from_short_url(short_id):
    """Obtener página desde URL corta (/wiki/x/XXXXX)"""

    client = ConfluenceClient()

    print("=" * 80)
    print(f"Obteniendo Página de Confluence")
    print("=" * 80)

    # Primero intentar obtener la página directamente
    # La URL corta /wiki/x/XXXXX normalmente redirige a la página real
    try:
        # Intentar obtener información usando el ID corto
        full_url = f"{client.base_url}/wiki/x/{short_id}"

        print(f"\n1. Resolviendo URL corta: {full_url}")

        # Hacer request con allow_redirects para seguir la redirección
        response = requests.get(
            full_url,
            auth=client.auth,
            allow_redirects=False
        )

        # Obtener la URL de redirección
        if response.status_code in [301, 302, 303, 307, 308]:
            redirect_url = response.headers.get('Location', '')
            print(f"   Redirecciona a: {redirect_url}")

            # Extraer el ID de la página de la URL
            if '/pages/' in redirect_url:
                page_id = redirect_url.split('/pages/')[-1].split('/')[0].split('?')[0]
                print(f"   ID de página encontrado: {page_id}")

                # Obtener contenido de la página
                return get_page_content(client, page_id)

        # Si no redirige, intentar buscar directamente
        print("\n2. Intentando acceso directo...")
        response = requests.get(
            full_url,
            auth=client.auth,
            allow_redirects=True
        )

        if response.status_code == 200:
            # Extraer información de la página HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar el ID de la página en el HTML
            page_id_meta = soup.find('meta', {'name': 'ajs-page-id'})
            if page_id_meta:
                page_id = page_id_meta.get('content')
                print(f"   ID de página encontrado en HTML: {page_id}")
                return get_page_content(client, page_id)

    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    return None

def get_page_content(client, page_id):
    """Obtener contenido completo de una página"""

    print(f"\n3. Obteniendo contenido de la página {page_id}...")

    try:
        response = requests.get(
            f"{client.api_url}/content/{page_id}",
            auth=client.auth,
            headers=client.headers,
            params={'expand': 'body.storage,version,space,ancestors,history'}
        )

        if response.status_code == 200:
            page = response.json()

            print("\n" + "=" * 80)
            print("INFORMACIÓN DE LA PÁGINA")
            print("=" * 80)

            print(f"\nTítulo: {page.get('title', 'N/A')}")
            print(f"ID: {page.get('id', 'N/A')}")
            print(f"Tipo: {page.get('type', 'N/A')}")
            print(f"Versión: {page.get('version', {}).get('number', 'N/A')}")

            space = page.get('space', {})
            print(f"\nEspacio: {space.get('name', 'N/A')} ({space.get('key', 'N/A')})")

            # Ancestros (páginas padres)
            ancestors = page.get('ancestors', [])
            if ancestors:
                print(f"\nPáginas padres:")
                for ancestor in ancestors:
                    print(f"  - {ancestor.get('title', 'N/A')} (ID: {ancestor.get('id', 'N/A')})")

            # URL
            page_url = f"{client.base_url}/wiki/spaces/{space.get('key')}/pages/{page.get('id')}"
            print(f"\nURL: {page_url}")

            # Historial
            history = page.get('history', {})
            created_by = history.get('createdBy', {})
            print(f"\nCreado por: {created_by.get('displayName', 'N/A')}")
            print(f"Fecha creación: {history.get('createdDate', 'N/A')}")

            # Contenido
            body = page.get('body', {}).get('storage', {})
            content = body.get('value', '')

            print(f"\n" + "=" * 80)
            print("CONTENIDO (primeros 1000 caracteres)")
            print("=" * 80)
            print(content[:1000])
            if len(content) > 1000:
                print(f"\n... (total: {len(content)} caracteres)")

            print("\n" + "=" * 80)

            return page
        else:
            print(f"   [ERROR] Error obteniendo página: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return None

if __name__ == "__main__":
    # ID de la página desde la URL corta
    # https://si-cognitio.atlassian.net/wiki/x/kIquCQ
    short_id = "kIquCQ"

    if len(sys.argv) > 1:
        short_id = sys.argv[1]

    page = get_page_from_short_url(short_id)

    if page:
        print("\n[OK] Página obtenida exitosamente")
    else:
        print("\n[ERROR] No se pudo obtener la página")
