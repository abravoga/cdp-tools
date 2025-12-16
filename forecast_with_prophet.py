#!/usr/bin/env python3
"""
Create forecasts using Prophet (Facebook's forecasting library)
Stores predictions back in Elasticsearch for visualization
"""

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try to import Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("\n[WARNING] Prophet no esta instalado.")
    print("Para instalar: pip install prophet")
    print("Nota: Prophet requiere pystan que puede necesitar compilacion.\n")

es = Elasticsearch(
    ['https://gea-data-cloud-masorange-es.es.europe-west1.gcp.cloud.es.io'],
    basic_auth=('infra_admin', 'imdeveloperS'),
    verify_certs=True,
    request_timeout=30
)

def get_historical_data(cluster_name=None, days=30):
    """Get historical consumption data"""

    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=days)

    query = {
        "size": 10000,
        "query": {
            "range": {
                "@timestamp": {
                    "gte": from_date.isoformat(),
                    "lte": to_date.isoformat()
                }
            }
        },
        "sort": [{"@timestamp": "asc"}]
    }

    # Add cluster filter if specified
    if cluster_name:
        query["query"] = {
            "bool": {
                "must": [
                    query["query"],
                    {"term": {"cluster_name": cluster_name}}
                ]
            }
        }

    result = es.search(index="cdp-consumption-records-*", body=query)

    # Convert to DataFrame
    data = []
    for hit in result['hits']['hits']:
        source = hit['_source']
        data.append({
            'ds': pd.to_datetime(source['@timestamp']),
            'y': source.get('credits', 0),
            'cluster_name': source.get('cluster_name', 'Unknown')
        })

    df = pd.DataFrame(data)

    # Aggregate by day
    if not df.empty:
        df_daily = df.groupby(df['ds'].dt.date).agg({
            'y': 'sum',
            'cluster_name': 'first'
        }).reset_index()
        df_daily['ds'] = pd.to_datetime(df_daily['ds'])
        return df_daily
    return pd.DataFrame()

def create_simple_forecast(df, periods=7):
    """Create simple forecast using linear regression"""

    if df.empty or len(df) < 7:
        print("[WARNING] No hay suficientes datos para crear prediccion")
        return pd.DataFrame()

    # Prepare data
    df = df.copy()
    df['ds_numeric'] = (df['ds'] - df['ds'].min()).dt.days

    # Simple linear regression
    from numpy.polynomial import Polynomial

    p = Polynomial.fit(df['ds_numeric'], df['y'], 1)

    # Create future dates
    last_date = df['ds'].max()
    future_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=periods,
        freq='D'
    )

    future_df = pd.DataFrame({'ds': future_dates})
    future_df['ds_numeric'] = (future_df['ds'] - df['ds'].min()).dt.days

    # Predict
    future_df['yhat'] = p(future_df['ds_numeric'])
    future_df['yhat_lower'] = future_df['yhat'] * 0.9  # 10% lower bound
    future_df['yhat_upper'] = future_df['yhat'] * 1.1  # 10% upper bound

    return future_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def forecast_with_prophet(df, periods=7):
    """Create forecast using Prophet"""

    if not PROPHET_AVAILABLE:
        print("[INFO] Usando prediccion simple (linear regression)")
        return create_simple_forecast(df, periods)

    if df.empty or len(df) < 7:
        print("[WARNING] No hay suficientes datos")
        return pd.DataFrame()

    try:
        # Create and fit model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            interval_width=0.95
        )

        model.fit(df)

        # Create future dataframe
        future = model.make_future_dataframe(periods=periods)

        # Predict
        forecast = model.predict(future)

        # Return only future predictions
        return forecast[forecast['ds'] > df['ds'].max()][
            ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
        ]

    except Exception as e:
        print(f"[WARNING] Error con Prophet: {e}")
        print("[INFO] Usando prediccion simple")
        return create_simple_forecast(df, periods)

def save_forecast_to_es(forecast_df, cluster_name=None):
    """Save forecast to Elasticsearch"""

    if forecast_df.empty:
        return

    index_name = f"cdp-consumption-forecast-{datetime.now(timezone.utc).strftime('%Y.%m.%d')}"

    docs = []
    for _, row in forecast_df.iterrows():
        doc = {
            '_index': index_name,
            '_source': {
                '@timestamp': row['ds'].isoformat(),
                'forecast_date': row['ds'].isoformat(),
                'predicted_credits': float(row['yhat']),
                'predicted_credits_lower': float(row['yhat_lower']),
                'predicted_credits_upper': float(row['yhat_upper']),
                'cluster_name': cluster_name if cluster_name else 'Total',
                'forecast_created': datetime.now(timezone.utc).isoformat(),
                'is_forecast': True
            }
        }
        docs.append(doc)

    if docs:
        success, failed = bulk(es, docs, raise_on_error=False)
        print(f"[OK] {success} predicciones guardadas en {index_name}")
        if failed:
            print(f"[WARNING] {len(failed)} documentos fallaron")

def create_forecast_index_template():
    """Create index template for forecast data"""

    template = {
        "index_patterns": ["cdp-consumption-forecast-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "forecast_date": {"type": "date"},
                    "predicted_credits": {"type": "float"},
                    "predicted_credits_lower": {"type": "float"},
                    "predicted_credits_upper": {"type": "float"},
                    "cluster_name": {"type": "keyword"},
                    "forecast_created": {"type": "date"},
                    "is_forecast": {"type": "boolean"}
                }
            }
        }
    }

    try:
        # Delete old template if exists
        try:
            es.indices.delete_index_template(name="cdp-consumption-forecast-template")
        except:
            pass

        # Create new template
        es.indices.put_index_template(
            name="cdp-consumption-forecast-template",
            body=template
        )
        print("[OK] Template de forecast creado")
    except Exception as e:
        print(f"[WARNING] Error creando template: {e}")

def main():
    print("=" * 70)
    print("Prediccion de Consumo CDP con Machine Learning")
    print("=" * 70)

    if not PROPHET_AVAILABLE:
        print("\n[INFO] Prophet no disponible, usando regresion lineal simple")
        print("       Para mejores resultados, instala Prophet:")
        print("       pip install prophet\n")

    # Create template
    print("\n1. Creando template para indices de forecast...")
    create_forecast_index_template()

    # Forecast total consumption
    print("\n2. Obteniendo datos historicos (total)...")
    df_total = get_historical_data()
    print(f"   Registros obtenidos: {len(df_total)}")

    if not df_total.empty:
        print("\n3. Creando prediccion para los proximos 7 dias (total)...")
        forecast_total = forecast_with_prophet(df_total, periods=7)

        if not forecast_total.empty:
            print(f"   Prediccion creada: {len(forecast_total)} dias")
            print("\n   Predicciones:")
            for _, row in forecast_total.iterrows():
                print(f"     {row['ds'].strftime('%Y-%m-%d')}: "
                      f"{row['yhat']:.2f} creditos "
                      f"({row['yhat_lower']:.2f} - {row['yhat_upper']:.2f})")

            print("\n4. Guardando predicciones en Elasticsearch...")
            save_forecast_to_es(forecast_total)

    # Forecast by cluster
    clusters = ["gea-cem-prod", "gcp-prod-datahub"]

    for cluster in clusters:
        print(f"\n5. Prediccion para {cluster}...")
        df_cluster = get_historical_data(cluster_name=cluster)

        if not df_cluster.empty:
            forecast_cluster = forecast_with_prophet(df_cluster, periods=7)

            if not forecast_cluster.empty:
                print(f"   Proximos 7 dias para {cluster}:")
                total_predicted = forecast_cluster['yhat'].sum()
                print(f"   Total predicho: {total_predicted:.2f} creditos")

                save_forecast_to_es(forecast_cluster, cluster_name=cluster)

    print("\n" + "=" * 70)
    print("Predicciones completadas!")
    print("=" * 70)
    print("\nPROXIMOS PASOS:")
    print("1. Ve a Kibana -> Discover")
    print("2. Crea un Data View para 'cdp-consumption-forecast-*'")
    print("3. Crea visualizaciones combinando datos historicos + forecast")
    print("\nLos datos de forecast tienen el campo 'is_forecast: true'")
    print("para distinguirlos de los datos reales.")

if __name__ == "__main__":
    main()
