#!/usr/bin/env python3
"""Check data view configuration"""

import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KIBANA_URL = 'https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io'
USERNAME = 'infra_admin'
PASSWORD = 'imdeveloperS'

auth = HTTPBasicAuth(USERNAME, PASSWORD)
headers = {
    'kbn-xsrf': 'true',
    'Content-Type': 'application/json'
}

def list_data_views():
    """List all data views"""
    url = f"{KIBANA_URL}/api/data_views"

    try:
        response = requests.get(url, auth=auth, headers=headers, verify=True)
        if response.status_code == 200:
            data = response.json()
            print("\nData Views disponibles:")
            print("-" * 70)
            for dv in data.get('data_view', []):
                print(f"  ID: {dv['id']}")
                print(f"  Title: {dv['title']}")
                print(f"  Name: {dv.get('name', 'N/A')}")
                print()
            return data.get('data_view', [])
        else:
            print(f"Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_data_view_details(dv_id):
    """Get data view details"""
    url = f"{KIBANA_URL}/api/data_views/data_view/{dv_id}"

    try:
        response = requests.get(url, auth=auth, headers=headers, verify=True)
        if response.status_code == 200:
            data = response.json()
            dv = data.get('data_view', {})
            print(f"\nDetalles del Data View: {dv_id}")
            print("-" * 70)
            print(f"Title: {dv.get('title')}")
            print(f"Time Field: {dv.get('timeFieldName')}")

            # Check for cluster_name field
            fields = dv.get('fields', {})
            if 'cluster_name' in str(fields):
                print("✓ Campo 'cluster_name' encontrado")
            else:
                print("✗ Campo 'cluster_name' NO encontrado")

            return dv
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("=" * 70)
    print("Verificación de Data Views")
    print("=" * 70)

    dvs = list_data_views()

    # Check CDP data view
    for dv in dvs:
        if 'cdp' in dv.get('title', '').lower():
            get_data_view_details(dv['id'])

if __name__ == "__main__":
    main()
