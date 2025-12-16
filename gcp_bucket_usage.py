#!/usr/bin/env python3
"""
Mostrar ocupación de buckets en GCP
"""

from gcp_integration import GCPClient
from datetime import datetime


def format_size(bytes_size):
    """Formatear tamaño en bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def get_bucket_usage():
    """Obtener uso de todos los buckets"""

    print("="*80)
    print("OCUPACION DE BUCKETS - GCP")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    client = GCPClient()

    # Listar todos los buckets
    print("Obteniendo lista de buckets...")
    buckets = client.list_buckets()

    if not buckets:
        print("No se encontraron buckets")
        return

    print(f"Total de buckets: {len(buckets)}\n")
    print("Calculando tamaños (esto puede tardar unos minutos)...\n")

    # Recopilar información de cada bucket
    bucket_info = []
    total_size = 0
    total_files = 0

    for idx, bucket in enumerate(buckets, 1):
        bucket_name = bucket.name
        print(f"[{idx}/{len(buckets)}] Procesando: {bucket_name}...", end=' ')

        try:
            size_info = client.get_bucket_size(bucket_name)

            if size_info:
                bucket_info.append({
                    'name': bucket_name,
                    'location': bucket.location,
                    'size_bytes': size_info['total_bytes'],
                    'size_gb': size_info['total_gb'],
                    'file_count': size_info['file_count']
                })

                total_size += size_info['total_bytes']
                total_files += size_info['file_count']

                print(f"{format_size(size_info['total_bytes'])} ({size_info['file_count']} archivos)")
            else:
                bucket_info.append({
                    'name': bucket_name,
                    'location': bucket.location,
                    'size_bytes': 0,
                    'size_gb': 0,
                    'file_count': 0
                })
                print("0 B (0 archivos)")

        except Exception as e:
            print(f"Error: {e}")
            bucket_info.append({
                'name': bucket_name,
                'location': bucket.location,
                'size_bytes': 0,
                'size_gb': 0,
                'file_count': 0
            })

    # Ordenar por tamaño (mayor a menor)
    bucket_info.sort(key=lambda x: x['size_bytes'], reverse=True)

    # Mostrar resumen
    print("\n" + "="*80)
    print("RESUMEN DE OCUPACION")
    print("="*80)
    print(f"\n{'Bucket':<50} {'Tamaño':<15} {'Archivos':<12} {'Ubicación':<20}")
    print("-"*100)

    for info in bucket_info:
        size_str = format_size(info['size_bytes'])
        print(f"{info['name']:<50} {size_str:<15} {info['file_count']:<12} {info['location']:<20}")

    print("-"*100)
    print(f"{'TOTAL':<50} {format_size(total_size):<15} {total_files:<12}")

    # Mostrar top 5 más grandes
    print("\n" + "="*80)
    print("TOP 5 BUCKETS MAS GRANDES")
    print("="*80)

    for idx, info in enumerate(bucket_info[:5], 1):
        percentage = (info['size_bytes'] / total_size * 100) if total_size > 0 else 0
        print(f"{idx}. {info['name']}")
        print(f"   Tamaño: {format_size(info['size_bytes'])} ({info['size_gb']:.2f} GB)")
        print(f"   Archivos: {info['file_count']:,}")
        print(f"   Porcentaje del total: {percentage:.2f}%")
        print()

    # Estadísticas generales
    print("="*80)
    print("ESTADISTICAS GENERALES")
    print("="*80)
    print(f"Total de buckets: {len(buckets)}")
    print(f"Espacio total usado: {format_size(total_size)} ({total_size / (1024**3):.2f} GB)")
    print(f"Total de archivos: {total_files:,}")
    print(f"Tamaño promedio por bucket: {format_size(total_size / len(buckets)) if len(buckets) > 0 else '0 B'}")
    print(f"Archivos promedio por bucket: {total_files // len(buckets) if len(buckets) > 0 else 0:,}")
    print("="*80)

    return bucket_info


if __name__ == "__main__":
    get_bucket_usage()
