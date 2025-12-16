#!/usr/bin/env python3
"""
Create ML jobs for forecasting CDP consumption
Uses Elasticsearch ML Anomaly Detection with forecasting
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3
from datetime import datetime, timedelta, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KIBANA_URL = 'https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io'
ES_URL = 'https://gea-data-cloud-masorange-es.es.europe-west1.gcp.cloud.es.io'
USERNAME = 'infra_admin'
PASSWORD = 'imdeveloperS'

auth = HTTPBasicAuth(USERNAME, PASSWORD)
headers = {
    'kbn-xsrf': 'true',
    'Content-Type': 'application/json'
}

def create_ml_job_total_credits():
    """Create ML job for total credits forecasting"""

    job_id = "cdp-credits-forecast"

    # Delete if exists
    try:
        url = f"{ES_URL}/_ml/anomaly_detectors/{job_id}"
        requests.delete(url, auth=auth, verify=True)
        print(f"[INFO] Job antiguo eliminado")
    except:
        pass

    # Create ML job
    job_config = {
        "description": "Forecast CDP credits consumption",
        "analysis_config": {
            "bucket_span": "1h",
            "detectors": [
                {
                    "function": "sum",
                    "field_name": "credits",
                    "detector_description": "Sum of credits"
                }
            ],
            "influencers": []
        },
        "data_description": {
            "time_field": "@timestamp",
            "time_format": "epoch_ms"
        },
        "model_plot_config": {
            "enabled": True,
            "annotations_enabled": True
        },
        "analysis_limits": {
            "model_memory_limit": "512mb"
        }
    }

    url = f"{ES_URL}/_ml/anomaly_detectors/{job_id}"

    try:
        response = requests.put(url, auth=auth, headers=headers, json=job_config, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] ML Job creado: {job_id}")
            return job_id
        else:
            print(f"[ERROR] Error creando job: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_datafeed(job_id):
    """Create datafeed for ML job"""

    datafeed_id = f"datafeed-{job_id}"

    # Delete if exists
    try:
        url = f"{ES_URL}/_ml/datafeeds/{datafeed_id}"
        requests.delete(url, auth=auth, verify=True)
    except:
        pass

    # Calculate time range (last 30 days)
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=30)

    datafeed_config = {
        "job_id": job_id,
        "indices": ["cdp-consumption-records-*"],
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                                "lte": end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                            }
                        }
                    }
                ]
            }
        },
        "scroll_size": 1000
    }

    url = f"{ES_URL}/_ml/datafeeds/{datafeed_id}"

    try:
        response = requests.put(url, auth=auth, headers=headers, json=datafeed_config, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] Datafeed creado: {datafeed_id}")
            return datafeed_id
        else:
            print(f"[ERROR] Error creando datafeed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def open_job(job_id):
    """Open ML job"""
    url = f"{ES_URL}/_ml/anomaly_detectors/{job_id}/_open"

    try:
        response = requests.post(url, auth=auth, headers=headers, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] Job abierto: {job_id}")
            return True
        else:
            print(f"[ERROR] Error abriendo job: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def start_datafeed(datafeed_id):
    """Start datafeed"""
    url = f"{ES_URL}/_ml/datafeeds/{datafeed_id}/_start"

    try:
        response = requests.post(url, auth=auth, headers=headers, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] Datafeed iniciado: {datafeed_id}")
            return True
        else:
            print(f"[ERROR] Error iniciando datafeed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def create_forecast(job_id, duration="7d"):
    """Create forecast for the job"""
    url = f"{ES_URL}/_ml/anomaly_detectors/{job_id}/_forecast"

    forecast_config = {
        "duration": duration  # Forecast for next 7 days
    }

    try:
        response = requests.post(url, auth=auth, headers=headers, json=forecast_config, verify=True)
        if response.status_code in [200, 201]:
            result = response.json()
            forecast_id = result.get('forecast_id')
            print(f"[OK] Forecast creado: {forecast_id}")
            print(f"     Prediccion para los proximos {duration}")
            return forecast_id
        else:
            print(f"[ERROR] Error creando forecast: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_ml_job_by_cluster(cluster_name):
    """Create ML job for specific cluster"""

    cluster_id = cluster_name.replace('-', '_')
    job_id = f"cdp-forecast-{cluster_id}"

    # Delete if exists
    try:
        url = f"{ES_URL}/_ml/anomaly_detectors/{job_id}"
        requests.delete(url, auth=auth, verify=True)
    except:
        pass

    # Create ML job
    job_config = {
        "description": f"Forecast credits for {cluster_name}",
        "analysis_config": {
            "bucket_span": "1h",
            "detectors": [
                {
                    "function": "sum",
                    "field_name": "credits",
                    "detector_description": f"Sum of credits for {cluster_name}"
                }
            ],
            "influencers": []
        },
        "data_description": {
            "time_field": "@timestamp",
            "time_format": "epoch_ms"
        },
        "model_plot_config": {
            "enabled": True,
            "annotations_enabled": True
        },
        "analysis_limits": {
            "model_memory_limit": "256mb"
        }
    }

    url = f"{ES_URL}/_ml/anomaly_detectors/{job_id}"

    try:
        response = requests.put(url, auth=auth, headers=headers, json=job_config, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] ML Job creado: {job_id}")

            # Create datafeed
            datafeed_id = f"datafeed-{job_id}"
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=30)

            datafeed_config = {
                "job_id": job_id,
                "indices": ["cdp-consumption-records-*"],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                                        "lte": end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                                    }
                                }
                            },
                            {
                                "term": {
                                    "cluster_name": cluster_name
                                }
                            }
                        ]
                    }
                },
                "scroll_size": 1000
            }

            url_df = f"{ES_URL}/_ml/datafeeds/{datafeed_id}"
            response_df = requests.put(url_df, auth=auth, headers=headers, json=datafeed_config, verify=True)

            if response_df.status_code in [200, 201]:
                print(f"[OK] Datafeed creado: {datafeed_id}")
                return job_id, datafeed_id

        return None, None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None, None

def main():
    print("=" * 70)
    print("Creacion de Jobs de Machine Learning para Predicciones")
    print("=" * 70)

    print("\n1. Creando ML Job para consumo total de creditos...")
    job_id = create_ml_job_total_credits()

    if job_id:
        print("\n2. Creando datafeed...")
        datafeed_id = create_datafeed(job_id)

        if datafeed_id:
            print("\n3. Abriendo job...")
            if open_job(job_id):
                print("\n4. Iniciando datafeed (esto puede tardar unos minutos)...")
                if start_datafeed(datafeed_id):
                    print("\n[INFO] Esperando a que el datafeed procese los datos...")
                    print("       Esto puede tardar 2-5 minutos dependiendo del volumen.")
                    print("\n5. Para crear el forecast, ejecuta:")
                    print(f"   curl -X POST '{ES_URL}/_ml/anomaly_detectors/{job_id}/_forecast' \\")
                    print(f"        -u '{USERNAME}:{PASSWORD}' \\")
                    print(f"        -H 'Content-Type: application/json' \\")
                    print(f"        -d '{{\"duration\": \"7d\"}}'")

    # Create jobs for top clusters
    print("\n\n6. Creando ML Jobs para clusters principales...")
    clusters = ["gea-cem-prod", "gcp-prod-datahub"]

    jobs = []
    for cluster in clusters:
        print(f"\n   Creando job para {cluster}...")
        job_id, datafeed_id = create_ml_job_by_cluster(cluster)
        if job_id and datafeed_id:
            jobs.append((job_id, datafeed_id, cluster))

    print("\n" + "=" * 70)
    print("Jobs creados exitosamente!")
    print("=" * 70)

    print("\nPROXIMOS PASOS:")
    print("1. Espera 5 minutos a que los datafeeds procesen los datos")
    print("2. Ve a Kibana -> Machine Learning -> Anomaly Detection")
    print("3. Abre cada job y crea un forecast haciendo clic en 'Forecast'")
    print("4. Las predicciones apareceran en las visualizaciones")

    print("\nJobs creados:")
    print(f"  - cdp-credits-forecast (Total)")
    for job_id, _, cluster in jobs:
        print(f"  - {job_id} ({cluster})")

    print(f"\nAcceso a ML: {KIBANA_URL}/app/ml")

if __name__ == "__main__":
    main()
