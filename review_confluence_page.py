#!/usr/bin/env python3
"""
Revisar contenido de la página de Confluence
"""

from confluence_integration import ConfluenceClient
import re

def review_page(page_id):
    """Revisar y mostrar contenido de la página"""

    client = ConfluenceClient()
    page = client.get_page_content(page_id)

    if not page:
        print("[ERROR] No se pudo obtener la página")
        return

    print("=" * 80)
    print(f"PÁGINA: {page.get('title', 'N/A')}")
    print("=" * 80)
    print(f"ID: {page.get('id')}")
    print(f"Versión: {page.get('version', {}).get('number')}")
    print(f"Espacio: {page.get('space', {}).get('name')}")

    # URL
    space_key = page.get('space', {}).get('key')
    page_id = page.get('id')
    page_url = f"{client.base_url}/wiki/spaces/{space_key}/pages/{page_id}"
    print(f"URL: {page_url}")
    print("=" * 80)

    # Obtener contenido
    content = page.get('body', {}).get('storage', {}).get('value', '')

    print(f"\nLongitud del contenido: {len(content)} caracteres")

    # Extraer secciones principales
    print("\n" + "=" * 80)
    print("ESTRUCTURA DE LA PÁGINA")
    print("=" * 80)

    # Buscar todos los h1, h2, h3
    headers = re.findall(r'<h([123])>(.*?)</h\1>', content)

    current_h1 = ""
    current_h2 = ""

    for level, title in headers:
        # Limpiar emojis y caracteres especiales
        title_clean = re.sub(r'[^\w\s\-áéíóúñÁÉÍÓÚÑ]', '', title).strip()

        if level == '1':
            current_h1 = title_clean
            print(f"\n### {title_clean}")
        elif level == '2':
            current_h2 = title_clean
            print(f"  ## {title_clean}")
        elif level == '3':
            print(f"    # {title_clean}")

    # Buscar bloques de código
    print("\n" + "=" * 80)
    print("BLOQUES DE CÓDIGO ENCONTRADOS")
    print("=" * 80)

    code_blocks = re.findall(r'<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body>', content, re.DOTALL)
    for i, code in enumerate(code_blocks, 1):
        print(f"\nBloque {i}:")
        print(code[:200] if len(code) > 200 else code)
        if len(code) > 200:
            print("...")

    # Buscar enlaces
    print("\n" + "=" * 80)
    print("ENLACES ENCONTRADOS")
    print("=" * 80)

    links = re.findall(r'<a href="([^"]+)">([^<]*)</a>', content)
    for url, text in links[:10]:  # Mostrar primeros 10
        print(f"  - [{text}] -> {url}")

    if len(links) > 10:
        print(f"  ... y {len(links) - 10} enlaces más")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"  Secciones principales (h1): {len([h for h in headers if h[0] == '1'])}")
    print(f"  Subsecciones (h2): {len([h for h in headers if h[0] == '2'])}")
    print(f"  Sub-subsecciones (h3): {len([h for h in headers if h[0] == '3'])}")
    print(f"  Bloques de código: {len(code_blocks)}")
    print(f"  Enlaces: {len(links)}")
    print("=" * 80)

    # Guardar en archivo
    output_file = "confluence_page_content.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n[OK] Contenido completo guardado en: {output_file}")
    print("     Puedes abrirlo con un navegador para ver el formato completo")

if __name__ == "__main__":
    # ID de la página CDP Tools
    page_id = "726008509"
    review_page(page_id)
