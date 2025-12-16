#!/usr/bin/env python3
"""
Crear página de CDP Tools en Confluence
"""

from confluence_integration import ConfluenceClient
from confluence_config import CONFLUENCE_SPACE_KEY
from datetime import datetime

def create_cdp_tools_page():
    """Crear página completa de CDP Tools"""

    print("=" * 80)
    print("Creando Página CDP Tools en Confluence")
    print("=" * 80)

    client = ConfluenceClient()

    # ID de la página padre (GCP Knowledge Base)
    parent_page_id = "162433680"

    # Título de la nueva página
    title = "CDP Tools - Sistema de Análisis y Predicción"

    # Contenido en formato Confluence HTML
    content = f"""
<ac:structured-macro ac:name="info">
    <ac:rich-text-body>
        <p><strong>Última actualización:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p><strong>Autor:</strong> Adrian Bravo</p>
        <p><strong>Repositorio:</strong> <a href="https://github.com/abravoga/cdp-tools">github.com/abravoga/cdp-tools</a></p>
    </ac:rich-text-body>
</ac:structured-macro>

<h1>🚀 CDP Tools - Sistema de Análisis y Predicción</h1>

<p>Sistema completo de análisis, visualización y predicción de consumo de créditos CDP (Cloudera Data Platform) con Machine Learning, integrado con Elasticsearch y Kibana.</p>

<hr/>

<h2>📊 ¿Qué es CDP Tools?</h2>

<p>CDP Tools es un sistema automatizado que:</p>

<ul>
    <li><strong>Obtiene</strong> datos de consumo de CDP automáticamente</li>
    <li><strong>Analiza</strong> el consumo de créditos en Elasticsearch</li>
    <li><strong>Visualiza</strong> métricas en 10 dashboards de Kibana</li>
    <li><strong>Predice</strong> el consumo futuro usando Machine Learning</li>
</ul>

<h2>✨ Características Principales</h2>

<h3>1. Ingesta Automática de Datos</h3>
<ul>
    <li>Obtención automática de datos CDP (últimos 30 días)</li>
    <li>Indexación en Elasticsearch con eliminación de duplicados</li>
    <li>Campos enriquecidos con información temporal y patrones</li>
    <li>Etiquetas legibles en español (fin de semana, nocturno, etc.)</li>
</ul>

<h3>2. Visualizaciones en Kibana</h3>
<ul>
    <li><strong>10 dashboards temáticos</strong> con diferentes perspectivas</li>
    <li><strong>40+ visualizaciones especializadas</strong></li>
    <li>Análisis por cluster, entorno, tipo de instancia</li>
    <li>Patrones de uso (fin de semana vs semana, nocturno vs diurno)</li>
</ul>

<h3>3. Predicciones con Machine Learning</h3>
<ul>
    <li>Predicciones automáticas para los <strong>próximos 7 días</strong></li>
    <li>Análisis global y por cluster individual</li>
    <li>Bandas de confianza (límites superior e inferior)</li>
    <li>Soporte para Prophet (Facebook) o regresión lineal</li>
</ul>

<hr/>

<h2>📦 Dashboards Disponibles</h2>

<ac:structured-macro ac:name="expand">
    <ac:parameter ac:name="title">Ver lista completa de dashboards</ac:parameter>
    <ac:rich-text-body>
        <ol>
            <li><strong>CDP - Dashboard Ejecutivo</strong> - KPIs principales para management</li>
            <li><strong>CDP - Análisis de Consumo</strong> - Vista general completa</li>
            <li><strong>CDP - Análisis Temporal</strong> - Tendencias en el tiempo</li>
            <li><strong>CDP - Análisis de Costos</strong> - Desglose de créditos</li>
            <li><strong>CDP - Distribuciones</strong> - Gráficos circulares</li>
            <li><strong>CDP - Eficiencia y Patrones</strong> - Patrones de uso</li>
            <li><strong>CDP - Tendencias por Cluster</strong> - Tendencias individuales</li>
            <li><strong>CDP - Evolución de Horas</strong> - Horas computadas</li>
            <li><strong>CDP - Predicciones de Consumo (ML)</strong> - Dashboard básico</li>
            <li><strong>CDP - Predicciones ML Completo</strong> - Dashboard completo ⭐</li>
        </ol>
    </ac:rich-text-body>
</ac:structured-macro>

<hr/>

<h2>🔗 Repositorio GitHub</h2>

<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="bgColor">#deebff</ac:parameter>
    <ac:rich-text-body>
        <p><strong>URL del Repositorio:</strong></p>
        <p><a href="https://github.com/abravoga/cdp-tools">https://github.com/abravoga/cdp-tools</a></p>
        <p><strong>Licencia:</strong> MIT (Open Source)</p>
        <p><strong>Lenguaje:</strong> Python 3.8+</p>
    </ac:rich-text-body>
</ac:structured-macro>

<h2>🚀 Cómo Obtener e Instalar</h2>

<h3>Paso 1: Clonar el Repositorio</h3>

<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">bash</ac:parameter>
    <ac:plain-text-body><![CDATA[# Clonar desde GitHub
git clone https://github.com/abravoga/cdp-tools.git
cd cdp-tools]]></ac:plain-text-body>
</ac:structured-macro>

<h3>Paso 2: Instalar Dependencias</h3>

<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">bash</ac:parameter>
    <ac:plain-text-body><![CDATA[# Instalar librerías necesarias
pip install -r requirements.txt

# Librerías principales:
# - elasticsearch
# - pandas
# - numpy
# - requests]]></ac:plain-text-body>
</ac:structured-macro>

<h3>Paso 3: Configurar Credenciales</h3>

<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">bash</ac:parameter>
    <ac:plain-text-body><![CDATA[# Copiar archivo de ejemplo
cp config.example.py config.py

# Editar config.py con tus credenciales:
# - ELASTICSEARCH_URL
# - KIBANA_URL
# - USERNAME
# - PASSWORD]]></ac:plain-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="warning">
    <ac:rich-text-body>
        <p><strong>Importante:</strong> El archivo <code>config.py</code> contiene credenciales sensibles y NO debe compartirse. Ya está en .gitignore para protegerlo.</p>
    </ac:rich-text-body>
</ac:structured-macro>

<h3>Paso 4: Ejecutar Actualización</h3>

<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">bash</ac:parameter>
    <ac:plain-text-body><![CDATA[# Opción 1: Usar el menú interactivo (Windows)
MENU.bat

# Opción 2: Actualización completa automática
0_Actualizar_TODO.bat

# Opción 3: Scripts individuales
python cdp_to_elasticsearch.py      # Solo datos
python forecast_with_prophet.py     # Solo predicciones]]></ac:plain-text-body>
</ac:structured-macro>

<hr/>

<h2>📊 Estructura del Proyecto</h2>

<ac:structured-macro ac:name="expand">
    <ac:parameter ac:name="title">Ver estructura completa</ac:parameter>
    <ac:rich-text-body>
        <ac:structured-macro ac:name="code">
            <ac:plain-text-body><![CDATA[cdp-tools/
├── README.md                          # Documentación principal
├── config.example.py                  # Plantilla de configuración
├── .gitignore                         # Archivos ignorados
│
├── Scripts de Ingesta
│   ├── cdp_to_elasticsearch.py       # Ingesta de datos CDP
│   ├── compare_quantities.py         # Comparación CDP vs ES
│   └── verify_labels.py              # Verificación
│
├── Scripts de Predicciones ML
│   ├── forecast_with_prophet.py      # Predicciones
│   ├── create_forecast_visualizations.py
│   └── create_complete_forecast_dashboard.py
│
├── Scripts de Dashboards
│   ├── create_kibana_dashboard.py
│   ├── create_cluster_trends.py
│   └── verify_kibana_dashboards.py
│
├── Scripts Batch (Windows)
│   ├── MENU.bat                      # Menú interactivo ⭐
│   ├── 0_Actualizar_TODO.bat        # Actualización completa
│   ├── 2_Actualizar_Elasticsearch.bat
│   └── 4_Actualizar_Predicciones_ML.bat
│
└── Documentación
    ├── INICIO_RAPIDO.md
    ├── RESUMEN_COMPLETO.md
    └── DASHBOARDS_KIBANA.md]]></ac:plain-text-body>
        </ac:structured-macro>
    </ac:rich-text-body>
</ac:structured-macro>

<hr/>

<h2>🎯 Uso Diario Recomendado</h2>

<p>Para mantener los datos actualizados:</p>

<ol>
    <li><strong>Ejecutar cada mañana:</strong> <code>0_Actualizar_TODO.bat</code></li>
    <li><strong>Revisar dashboards en Kibana</strong></li>
    <li><strong>Analizar predicciones ML</strong> para planificación</li>
</ol>

<h3>Acceso a Kibana</h3>

<p><strong>URL:</strong> <a href="https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards">Dashboards de Kibana</a></p>

<hr/>

<h2>📈 Datos de Ejemplo</h2>

<ac:structured-macro ac:name="info">
    <ac:rich-text-body>
        <h4>Clusters Principales</h4>
        <ul>
            <li><strong>gea-cem-prod:</strong> ~595 créditos/día (predicho)</li>
            <li><strong>gcp-prod-datahub:</strong> ~488 créditos/día (predicho)</li>
        </ul>
        <h4>Predicciones Totales</h4>
        <ul>
            <li><strong>Próximos 7 días:</strong> ~8,050 créditos</li>
            <li><strong>Promedio diario:</strong> ~1,150 créditos</li>
        </ul>
    </ac:rich-text-body>
</ac:structured-macro>

<hr/>

<h2>🔧 Requisitos Técnicos</h2>

<table>
    <tr>
        <th>Componente</th>
        <th>Versión Mínima</th>
    </tr>
    <tr>
        <td>Python</td>
        <td>3.8+</td>
    </tr>
    <tr>
        <td>Elasticsearch</td>
        <td>8.0+</td>
    </tr>
    <tr>
        <td>Kibana</td>
        <td>8.0+</td>
    </tr>
    <tr>
        <td>CDP CLI</td>
        <td>Última versión</td>
    </tr>
</table>

<h3>Dependencias Python</h3>
<ul>
    <li>elasticsearch >= 8.0.0</li>
    <li>pandas >= 1.3.0</li>
    <li>numpy >= 1.20.0</li>
    <li>requests >= 2.25.0</li>
    <li>prophet (opcional, para mejores predicciones)</li>
</ul>

<hr/>

<h2>📞 Soporte y Contribución</h2>

<h3>Reportar Problemas</h3>
<p>Si encuentras problemas o tienes sugerencias:</p>
<ul>
    <li>Abre un <a href="https://github.com/abravoga/cdp-tools/issues">Issue en GitHub</a></li>
    <li>Revisa la documentación completa en el repositorio</li>
</ul>

<h3>Contribuir</h3>
<p>Las contribuciones son bienvenidas:</p>
<ol>
    <li>Fork del proyecto</li>
    <li>Crea una rama: <code>git checkout -b feature/AmazingFeature</code></li>
    <li>Commit: <code>git commit -m 'Add some AmazingFeature'</code></li>
    <li>Push: <code>git push origin feature/AmazingFeature</code></li>
    <li>Abre un Pull Request</li>
</ol>

<hr/>

<h2>📚 Documentación Adicional</h2>

<p>En el repositorio encontrarás:</p>

<ul>
    <li><strong>README.md</strong> - Documentación principal del proyecto</li>
    <li><strong>INICIO_RAPIDO.md</strong> - Guía de inicio rápido</li>
    <li><strong>RESUMEN_COMPLETO.md</strong> - Documentación técnica completa</li>
    <li><strong>DASHBOARDS_KIBANA.md</strong> - Detalles de dashboards</li>
    <li><strong>GITHUB_SETUP.md</strong> - Guía para colaborar en GitHub</li>
    <li><strong>CONFLUENCE_SETUP.md</strong> - Integración con Confluence</li>
</ul>

<hr/>

<ac:structured-macro ac:name="tip">
    <ac:rich-text-body>
        <p><strong>💡 Tip:</strong> Revisa el archivo <code>MENU.bat</code> para acceder fácilmente a todas las funcionalidades del sistema desde un menú interactivo.</p>
    </ac:rich-text-body>
</ac:structured-macro>

<p><em>Última actualización: {datetime.now().strftime('%Y-%m-%d')}</em></p>
"""

    print("\n1. Contenido preparado")
    print(f"   Título: {title}")
    print(f"   Página padre: GCP Knowledge Base (ID: {parent_page_id})")

    # Crear la página
    print("\n2. Creando página en Confluence...")

    result = client.create_page(
        space_key=CONFLUENCE_SPACE_KEY,
        title=title,
        content=content,
        parent_id=parent_page_id
    )

    if result:
        page_id = result['id']
        page_url = f"{client.base_url}/wiki/spaces/{CONFLUENCE_SPACE_KEY}/pages/{page_id}"

        print("\n" + "=" * 80)
        print("✅ PÁGINA CREADA EXITOSAMENTE")
        print("=" * 80)
        print(f"\nTítulo: {title}")
        print(f"ID: {page_id}")
        print(f"URL: {page_url}")
        print("\n" + "=" * 80)

        return result
    else:
        print("\n[ERROR] No se pudo crear la página")
        return None

if __name__ == "__main__":
    create_cdp_tools_page()
