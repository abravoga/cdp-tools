#!/usr/bin/env python3
"""
Integración con Confluence para lectura y escritura de documentación
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import os

# Intentar importar configuración
try:
    from confluence_config import (
        CONFLUENCE_URL,
        CONFLUENCE_USERNAME,
        CONFLUENCE_API_TOKEN,
        CONFLUENCE_SPACE_KEY
    )
    CONFIG_LOADED = True
except ImportError:
    CONFIG_LOADED = False
    print("[WARNING] No se encontró confluence_config.py")
    print("Copia confluence_config.example.py a confluence_config.py y configúralo")


class ConfluenceClient:
    """Cliente para interactuar con Confluence"""

    def __init__(self, url=None, username=None, api_token=None):
        if not CONFIG_LOADED and not all([url, username, api_token]):
            raise ValueError("Debes proporcionar credenciales o crear confluence_config.py")

        self.base_url = url or CONFLUENCE_URL
        self.username = username or CONFLUENCE_USERNAME
        self.api_token = api_token or CONFLUENCE_API_TOKEN

        # Limpiar URL (quitar /wiki si existe al final)
        self.base_url = self.base_url.rstrip('/')
        if self.base_url.endswith('/wiki'):
            self.base_url = self.base_url[:-5]

        self.api_url = f"{self.base_url}/wiki/rest/api"
        self.auth = HTTPBasicAuth(self.username, self.api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_connection(self):
        """Probar conexión con Confluence"""
        try:
            response = requests.get(
                f"{self.api_url}/space",
                auth=self.auth,
                headers=self.headers
            )
            if response.status_code == 200:
                print("[OK] Conexión exitosa con Confluence")
                return True
            else:
                print(f"[ERROR] Error de conexión: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR] No se pudo conectar: {e}")
            return False

    def get_spaces(self):
        """Obtener lista de espacios"""
        try:
            response = requests.get(
                f"{self.api_url}/space",
                auth=self.auth,
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            return []
        except Exception as e:
            print(f"[ERROR] Error obteniendo espacios: {e}")
            return []

    def get_page_by_title(self, space_key, title):
        """Buscar página por título en un espacio"""
        try:
            params = {
                'spaceKey': space_key,
                'title': title,
                'expand': 'body.storage,version'
            }
            response = requests.get(
                f"{self.api_url}/content",
                auth=self.auth,
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                return results[0] if results else None
            return None
        except Exception as e:
            print(f"[ERROR] Error buscando página: {e}")
            return None

    def get_page_content(self, page_id):
        """Obtener contenido de una página"""
        try:
            response = requests.get(
                f"{self.api_url}/content/{page_id}",
                auth=self.auth,
                headers=self.headers,
                params={'expand': 'body.storage,version'}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[ERROR] Error obteniendo contenido: {e}")
            return None

    def search_content(self, query, space_key=None):
        """Buscar contenido en Confluence"""
        try:
            cql = f'text ~ "{query}"'
            if space_key:
                cql += f' and space = {space_key}'

            params = {
                'cql': cql,
                'limit': 10
            }
            response = requests.get(
                f"{self.api_url}/content/search",
                auth=self.auth,
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            return []
        except Exception as e:
            print(f"[ERROR] Error buscando: {e}")
            return []

    def create_page(self, space_key, title, content, parent_id=None):
        """Crear una nueva página"""
        try:
            data = {
                'type': 'page',
                'title': title,
                'space': {'key': space_key},
                'body': {
                    'storage': {
                        'value': content,
                        'representation': 'storage'
                    }
                }
            }

            if parent_id:
                data['ancestors'] = [{'id': parent_id}]

            response = requests.post(
                f"{self.api_url}/content",
                auth=self.auth,
                headers=self.headers,
                json=data
            )

            if response.status_code == 200:
                page = response.json()
                print(f"[OK] Página creada: {title}")
                return page
            else:
                print(f"[ERROR] Error creando página: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Error creando página: {e}")
            return None

    def update_page(self, page_id, title, content, current_version):
        """Actualizar una página existente"""
        try:
            data = {
                'version': {'number': current_version + 1},
                'title': title,
                'type': 'page',
                'body': {
                    'storage': {
                        'value': content,
                        'representation': 'storage'
                    }
                }
            }

            response = requests.put(
                f"{self.api_url}/content/{page_id}",
                auth=self.auth,
                headers=self.headers,
                json=data
            )

            if response.status_code == 200:
                page = response.json()
                print(f"[OK] Página actualizada: {title}")
                return page
            else:
                print(f"[ERROR] Error actualizando página: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Error actualizando página: {e}")
            return None

    def create_or_update_page(self, space_key, title, content, parent_id=None):
        """Crear página si no existe, o actualizarla si existe"""
        existing_page = self.get_page_by_title(space_key, title)

        if existing_page:
            # Actualizar página existente
            page_id = existing_page['id']
            current_version = existing_page['version']['number']
            return self.update_page(page_id, title, content, current_version)
        else:
            # Crear nueva página
            return self.create_page(space_key, title, content, parent_id)


def markdown_to_confluence(markdown_text):
    """Convertir Markdown a formato Confluence (básico)"""
    # Esta es una conversión básica
    # Para conversiones más complejas, considera usar una librería como python-markdown

    html = markdown_text

    # Headers
    html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
    html = html.replace('## ', '<h2>').replace('\n', '</h2>\n', 1)
    html = html.replace('### ', '<h3>').replace('\n', '</h3>\n', 1)
    html = html.replace('#### ', '<h4>').replace('\n', '</h4>\n', 1)

    # Bold
    import re
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Code blocks
    html = re.sub(r'```(.+?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Lists
    lines = html.split('\n')
    in_list = False
    result_lines = []

    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            result_lines.append(f"<li>{line.strip()[2:]}</li>")
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            result_lines.append(line)

    if in_list:
        result_lines.append('</ul>')

    return '\n'.join(result_lines)


def main():
    """Función principal de ejemplo"""
    print("=" * 80)
    print("Confluence Integration - Cliente de Prueba")
    print("=" * 80)

    if not CONFIG_LOADED:
        print("\n[ERROR] No se pudo cargar la configuración")
        print("Crea confluence_config.py basado en confluence_config.example.py")
        return

    # Crear cliente
    client = ConfluenceClient()

    # Probar conexión
    print("\n1. Probando conexión...")
    if not client.test_connection():
        return

    # Listar espacios
    print("\n2. Obteniendo espacios disponibles...")
    spaces = client.get_spaces()
    if spaces:
        print(f"\n   Espacios encontrados ({len(spaces)}):")
        for space in spaces[:10]:  # Mostrar primeros 10
            print(f"   - {space.get('key')}: {space.get('name')}")
    else:
        print("   No se encontraron espacios")

    print("\n" + "=" * 80)
    print("Conexión establecida. Puedes usar el cliente para leer/escribir.")
    print("=" * 80)


if __name__ == "__main__":
    main()
