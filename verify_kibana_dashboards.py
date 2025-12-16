#!/usr/bin/env python3
"""
Verify all dashboards and visualizations in Kibana
"""

import requests
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KIBANA_URL = 'https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io'
USERNAME = 'infra_admin'
PASSWORD = 'imdeveloperS'

auth = HTTPBasicAuth(USERNAME, PASSWORD)
headers = {'kbn-xsrf': 'true'}

def get_dashboards():
    """Get all CDP dashboards"""
    url = f"{KIBANA_URL}/api/saved_objects/_find?type=dashboard&search=CDP&search_fields=title&per_page=100"

    try:
        response = requests.get(url, auth=auth, headers=headers, verify=True)
        if response.status_code == 200:
            data = response.json()
            return data.get('saved_objects', [])
        else:
            print(f"Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_data_views():
    """Get all data views"""
    url = f"{KIBANA_URL}/api/saved_objects/_find?type=index-pattern&per_page=100"

    try:
        response = requests.get(url, auth=auth, headers=headers, verify=True)
        if response.status_code == 200:
            data = response.json()
            return [obj for obj in data.get('saved_objects', []) if 'cdp' in obj.get('attributes', {}).get('title', '').lower()]
        else:
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_visualizations():
    """Get all CDP visualizations"""
    url = f"{KIBANA_URL}/api/saved_objects/_find?type=lens&search=CDP&search_fields=title&per_page=200"

    try:
        response = requests.get(url, auth=auth, headers=headers, verify=True)
        if response.status_code == 200:
            data = response.json()
            return data.get('saved_objects', [])
        else:
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    print("=" * 80)
    print("VERIFICACION DE DASHBOARDS Y VISUALIZACIONES EN KIBANA")
    print("=" * 80)

    # Get data views
    print("\n1. DATA VIEWS")
    print("-" * 80)
    data_views = get_data_views()
    if data_views:
        for dv in data_views:
            title = dv.get('attributes', {}).get('title', 'N/A')
            dv_id = dv.get('id', 'N/A')
            print(f"  [OK] {title}")
            print(f"    ID: {dv_id}")
    else:
        print("  [!] No se encontraron data views")

    print(f"\n  Total: {len(data_views)} data views")

    # Get dashboards
    print("\n2. DASHBOARDS")
    print("-" * 80)
    dashboards = get_dashboards()
    if dashboards:
        for i, dash in enumerate(dashboards, 1):
            title = dash.get('attributes', {}).get('title', 'N/A')
            dash_id = dash.get('id', 'N/A')
            print(f"  {i}. {title}")
            print(f"     ID: {dash_id}")
            print(f"     URL: {KIBANA_URL}/app/dashboards#/view/{dash_id}")
    else:
        print("  [!] No se encontraron dashboards")

    print(f"\n  Total: {len(dashboards)} dashboards")

    # Get visualizations
    print("\n3. VISUALIZACIONES (LENS)")
    print("-" * 80)
    visualizations = get_visualizations()

    # Group by type
    forecast_viz = [v for v in visualizations if 'prediccion' in v.get('attributes', {}).get('title', '').lower() or 'forecast' in v.get('id', '').lower()]
    trend_viz = [v for v in visualizations if 'tendencia' in v.get('attributes', {}).get('title', '').lower()]
    other_viz = [v for v in visualizations if v not in forecast_viz and v not in trend_viz]

    print(f"\n  Predicciones ML:")
    for viz in forecast_viz:
        title = viz.get('attributes', {}).get('title', 'N/A')
        print(f"    [OK] {title}")

    print(f"\n  Tendencias:")
    for viz in trend_viz[:10]:  # Show first 10
        title = viz.get('attributes', {}).get('title', 'N/A')
        print(f"    [OK] {title}")
    if len(trend_viz) > 10:
        print(f"    ... y {len(trend_viz) - 10} más")

    print(f"\n  Otras visualizaciones:")
    for viz in other_viz[:10]:  # Show first 10
        title = viz.get('attributes', {}).get('title', 'N/A')
        print(f"    [OK] {title}")
    if len(other_viz) > 10:
        print(f"    ... y {len(other_viz) - 10} más")

    print(f"\n  Total: {len(visualizations)} visualizaciones")

    # Summary
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"  Data Views:       {len(data_views)}")
    print(f"  Dashboards:       {len(dashboards)}")
    print(f"  Visualizaciones:  {len(visualizations)}")
    print(f"    - Predicciones:  {len(forecast_viz)}")
    print(f"    - Tendencias:    {len(trend_viz)}")
    print(f"    - Otras:         {len(other_viz)}")

    print("\n" + "=" * 80)
    print("ACCESO RAPIDO")
    print("=" * 80)
    print(f"\nDashboards principales:")

    important_dashboards = [
        "CDP - Predicciones ML Completo",
        "CDP - Dashboard Ejecutivo",
        "CDP - Análisis de Consumo",
        "CDP - Tendencias por Cluster"
    ]

    for dash_name in important_dashboards:
        for dash in dashboards:
            if dash.get('attributes', {}).get('title', '') == dash_name:
                dash_id = dash.get('id', '')
                print(f"\n  - {dash_name}")
                print(f"    {KIBANA_URL}/app/dashboards#/view/{dash_id}")
                break

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
