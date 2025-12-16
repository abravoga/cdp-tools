#!/usr/bin/env python3
"""
Actualizar página principal GCP Knowledge Base
"""

from confluence_integration import ConfluenceClient
from datetime import datetime

GCP_KB_PAGE_ID = "162433680"

CATEGORIES = [
    ("724730780", "Gestion y Acceso", "Gestion de usuarios, accesos, entornos y formacion", 4),
    ("725058414", "Servicios Cloudera", "Instalacion, configuracion y uso de servicios Cloudera", 6),
    ("726073900", "Bases de Datos y Conectores", "Configuracion y uso de BD y conectores", 2),
    ("725582641", "Troubleshooting", "Errores conocidos y soluciones", 4),
    ("723552127", "Migraciones y Upgrades", "Procesos de migracion y actualizacion", 4),
    ("725418739", "Almacenamiento", "Gestion de buckets, HDFS y almacenamiento", 2),
    ("725942847", "Rendimiento y Optimizacion", "Optimizacion y best practices", 3),
    ("724894560", "Documentacion y Checklists", "Checklists y guias de referencia", 2),
    ("725156729", "Analisis y Prediccion", "Herramientas de analisis y prediccion", 1)
]


def main():
    print("="*80)
    print("REORGANIZACION - PASO 3: ACTUALIZAR PAGINA PRINCIPAL")
    print("="*80)

    client = ConfluenceClient()

    # Contenido HTML
    content = f"""
<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="bgColor">#deebff</ac:parameter>
    <ac:rich-text-body>
        <h1>GCP Knowledge Base</h1>
        <p>Base de conocimiento completa sobre Google Cloud Platform y Cloudera CDP</p>
        <p><em>Ultima actualizacion: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
    </ac:rich-text-body>
</ac:structured-macro>

<h2>Categorias de Documentacion</h2>

<p>La documentacion esta organizada en las siguientes categorias tematicas:</p>

<table>
    <tr>
        <th>Categoria</th>
        <th>Descripcion</th>
        <th>Paginas</th>
    </tr>
"""

    for cat_id, cat_name, cat_desc, page_count in CATEGORIES:
        link = f'<a href="/wiki/spaces/ITBIGD/pages/{cat_id}">GCP - {cat_name}</a>'
        content += f"""
    <tr>
        <td><strong>{link}</strong></td>
        <td>{cat_desc}</td>
        <td>{page_count}</td>
    </tr>
"""

    total_pages = sum(c[3] for c in CATEGORIES)

    content += f"""
</table>

<hr/>

<h2>Estadisticas</h2>

<ul>
    <li><strong>Total de categorias:</strong> {len(CATEGORIES)}</li>
    <li><strong>Total de paginas:</strong> {total_pages}</li>
    <li><strong>Ultima reorganizacion:</strong> {datetime.now().strftime('%Y-%m-%d')}</li>
</ul>

<hr/>

<h2>Navegacion Rapida</h2>

<ac:structured-macro ac:name="children" ac:schema-version="2" data-layout="default">
    <ac:parameter ac:name="depth">1</ac:parameter>
    <ac:parameter ac:name="all">true</ac:parameter>
    <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>

<hr/>

<ac:structured-macro ac:name="tip">
    <ac:rich-text-body>
        <p><strong>Consejo:</strong> Usa el buscador de Confluence o navega por las categorias para encontrar la documentacion que necesitas.</p>
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
            print("[OK] Pagina principal actualizada")
            print(f"\nURL: https://si-cognitio.atlassian.net/wiki/spaces/ITBIGD/pages/{GCP_KB_PAGE_ID}")
            return True
        else:
            print("[ERROR] Fallo la actualizacion")
            return False
    else:
        print("[ERROR] No se pudo obtener la pagina principal")
        return False


if __name__ == "__main__":
    main()
