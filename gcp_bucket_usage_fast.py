#!/usr/bin/env python3
"""
Mostrar ocupación de buckets en GCP (versión rápida usando métricas)
"""

from gcp_integration import GCPClient
from datetime import datetime
from google.cloud import monitoring_v3
from google.protobuf import timestamp_pb2
import time


def format_size(bytes_size):
    """Formatear tamaño en bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def get_bucket_usage_fast():
    """Obtener uso de buckets usando Cloud Monitoring (mucho más rápido)"""

    print("="*80)
    print("OCUPACION DE BUCKETS - GCP (Version Rapida)")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    client = GCPClient()
    project_id = client.project_id

    # Listar todos los buckets
    print("Obteniendo lista de buckets...")
    buckets = client.list_buckets()

    if not buckets:
        print("No se encontraron buckets")
        return

    print(f"Total de buckets: {len(buckets)}\n")
    print("Obteniendo metricas de uso...\n")

    # Crear cliente de monitoring
    monitoring_client = monitoring_v3.MetricServiceClient(credentials=client.credentials)

    # Configurar tiempo (últimas 24 horas)
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)
    interval = monitoring_v3.TimeInterval({
        "end_time": {"seconds": seconds, "nanos": nanos},
        "start_time": {"seconds": (seconds - 86400), "nanos": nanos},  # 24h atrás
    })

    bucket_info = []
    total_size = 0

    for idx, bucket in enumerate(buckets, 1):
        bucket_name = bucket.name
        print(f"[{idx}/{len(buckets)}] {bucket_name}...", end=' ')

        try:
            # Query para obtener el tamaño del bucket
            results = monitoring_client.list_time_series(
                request={
                    "name": f"projects/{project_id}",
                    "filter": f'metric.type="storage.googleapis.com/storage/total_bytes" '
                              f'AND resource.labels.bucket_name="{bucket_name}"',
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                }
            )

            # Obtener el último valor
            size_bytes = 0
            for result in results:
                if result.points:
                    size_bytes = result.points[0].value.double_value
                    break

            bucket_info.append({
                'name': bucket_name,
                'location': bucket.location,
                'size_bytes': int(size_bytes),
                'size_gb': size_bytes / (1024**3)
            })

            total_size += size_bytes
            print(f"{format_size(size_bytes)}")

        except Exception as e:
            print(f"Error obteniendo métricas: {e}")
            # Si falla, intentar contar archivos (limitado)
            try:
                blobs = client.list_blobs(bucket_name, max_results=1000)
                if blobs:
                    sample_size = sum(blob.size for blob in blobs)
                    bucket_info.append({
                        'name': bucket_name,
                        'location': bucket.location,
                        'size_bytes': sample_size,
                        'size_gb': sample_size / (1024**3)
                    })
                    total_size += sample_size
                    print(f"~{format_size(sample_size)} (estimado)")
                else:
                    bucket_info.append({
                        'name': bucket_name,
                        'location': bucket.location,
                        'size_bytes': 0,
                        'size_gb': 0
                    })
                    print("0 B")
            except:
                bucket_info.append({
                    'name': bucket_name,
                    'location': bucket.location,
                    'size_bytes': 0,
                    'size_gb': 0
                })
                print("No disponible")

    # Ordenar por tamaño (mayor a menor)
    bucket_info.sort(key=lambda x: x['size_bytes'], reverse=True)

    # Mostrar resumen
    print("\n" + "="*80)
    print("RESUMEN DE OCUPACION")
    print("="*80)
    print(f"\n{'Bucket':<50} {'Tamaño':<15} {'GB':<12} {'Ubicación':<20}")
    print("-"*100)

    for info in bucket_info:
        size_str = format_size(info['size_bytes'])
        print(f"{info['name']:<50} {size_str:<15} {info['size_gb']:<12.2f} {info['location']:<20}")

    print("-"*100)
    print(f"{'TOTAL':<50} {format_size(total_size):<15} {total_size / (1024**3):<12.2f}")

    # Mostrar top 5 más grandes
    print("\n" + "="*80)
    print("TOP 5 BUCKETS MAS GRANDES")
    print("="*80)

    for idx, info in enumerate(bucket_info[:5], 1):
        percentage = (info['size_bytes'] / total_size * 100) if total_size > 0 else 0
        print(f"{idx}. {info['name']}")
        print(f"   Tamaño: {format_size(info['size_bytes'])} ({info['size_gb']:.2f} GB)")
        print(f"   Porcentaje del total: {percentage:.2f}%")
        print()

    # Estadísticas generales
    print("="*80)
    print("ESTADISTICAS GENERALES")
    print("="*80)
    print(f"Total de buckets: {len(buckets)}")
    print(f"Espacio total usado: {format_size(total_size)} ({total_size / (1024**3):.2f} GB)")
    print(f"Tamaño promedio por bucket: {format_size(total_size / len(buckets)) if len(buckets) > 0 else '0 B'}")
    print("="*80)

    return bucket_info


if __name__ == "__main__":
    get_bucket_usage_fast()
