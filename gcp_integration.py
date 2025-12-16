#!/usr/bin/env python3
"""
Integración con Google Cloud Platform - Compute Engine y Cloud Storage
Usa Application Default Credentials (tu cuenta de Google)
"""

from google.cloud import compute_v1
from google.cloud import storage
import google.auth
import os


class GCPClient:
    """Cliente para interactuar con GCP Compute Engine y Cloud Storage"""

    def __init__(self, project_id=None):
        """
        Inicializar cliente GCP usando tu cuenta de Google

        Args:
            project_id: ID del proyecto GCP (opcional, se puede autodetectar)
        """
        # Obtener credenciales de tu cuenta (vía gcloud auth login)
        try:
            credentials, detected_project = google.auth.default()
            self.credentials = credentials
            self.project_id = project_id or detected_project

            if not self.project_id:
                # Intentar cargar de config
                try:
                    from gcp_config import GCP_PROJECT_ID
                    self.project_id = GCP_PROJECT_ID
                except ImportError:
                    raise ValueError(
                        "No se pudo detectar el proyecto. "
                        "Ejecuta: gcloud config set project TU_PROYECTO_ID"
                    )

        except Exception as e:
            raise ValueError(
                f"Error cargando credenciales: {e}\n\n"
                "Pasos para autenticarte:\n"
                "1. Instala gcloud CLI si no lo tienes\n"
                "2. Ejecuta: gcloud auth application-default login\n"
                "3. Ejecuta: gcloud config set project TU_PROYECTO_ID"
            )

        # Inicializar clientes
        self.compute_client = compute_v1.InstancesClient(credentials=self.credentials)
        self.zones_client = compute_v1.ZonesClient(credentials=self.credentials)
        self.storage_client = storage.Client(credentials=self.credentials, project=self.project_id)

    def test_connection(self):
        """Probar conexión a GCP"""
        try:
            # Intentar listar zonas
            zones = list(self.zones_client.list(project=self.project_id))
            print(f"[OK] Conexion exitosa a GCP")
            print(f"  Proyecto: {self.project_id}")
            print(f"  Zonas disponibles: {len(zones)}")
            return True

        except Exception as e:
            print(f"[ERROR] Error de conexion: {e}")
            return False

    # ========== COMPUTE ENGINE ==========

    def list_instances(self, zone=None, region=None):
        """
        Listar instancias de Compute Engine

        Args:
            zone: Zona específica (None = todas las zonas de la región)
            region: Región para filtrar (por defecto: todas)

        Returns:
            dict con instancias por zona
        """
        try:
            if zone:
                zones = [zone]
            else:
                # Listar todas las zonas
                zones_list = list(self.zones_client.list(project=self.project_id))
                if region:
                    zones = [z.name for z in zones_list if z.name.startswith(region)]
                else:
                    zones = [z.name for z in zones_list]

            instances_by_zone = {}

            for zone_name in zones:
                try:
                    instances = list(self.compute_client.list(
                        project=self.project_id,
                        zone=zone_name
                    ))
                    if instances:
                        instances_by_zone[zone_name] = instances
                except Exception as e:
                    # Silenciar errores de zonas sin instancias
                    pass

            return instances_by_zone

        except Exception as e:
            print(f"[ERROR] Error listando instancias: {e}")
            return None

    def get_instance(self, instance_name, zone):
        """
        Obtener detalles de una instancia específica

        Args:
            instance_name: Nombre de la instancia
            zone: Zona de la instancia

        Returns:
            Objeto Instance
        """
        try:
            instance = self.compute_client.get(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            return instance

        except Exception as e:
            print(f"[ERROR] Error obteniendo instancia {instance_name}: {e}")
            return None

    def start_instance(self, instance_name, zone):
        """Iniciar una instancia"""
        try:
            operation = self.compute_client.start(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            print(f"[OK] Iniciando instancia {instance_name}...")
            return operation

        except Exception as e:
            print(f"[ERROR] Error iniciando instancia: {e}")
            return None

    def stop_instance(self, instance_name, zone):
        """Detener una instancia"""
        try:
            operation = self.compute_client.stop(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            print(f"[OK] Deteniendo instancia {instance_name}...")
            return operation

        except Exception as e:
            print(f"[ERROR] Error deteniendo instancia: {e}")
            return None

    def reset_instance(self, instance_name, zone):
        """Reiniciar una instancia"""
        try:
            operation = self.compute_client.reset(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            print(f"[OK] Reiniciando instancia {instance_name}...")
            return operation

        except Exception as e:
            print(f"[ERROR] Error reiniciando instancia: {e}")
            return None

    # ========== CLOUD STORAGE ==========

    def list_buckets(self):
        """Listar todos los buckets"""
        try:
            buckets = list(self.storage_client.list_buckets())
            return buckets

        except Exception as e:
            print(f"[ERROR] Error listando buckets: {e}")
            return None

    def get_bucket(self, bucket_name):
        """Obtener un bucket específico"""
        try:
            bucket = self.storage_client.bucket(bucket_name)
            if bucket.exists():
                return bucket
            else:
                print(f"[ERROR] Bucket {bucket_name} no existe")
                return None

        except Exception as e:
            print(f"[ERROR] Error obteniendo bucket: {e}")
            return None

    def list_blobs(self, bucket_name, prefix=None, max_results=100):
        """
        Listar archivos (blobs) en un bucket

        Args:
            bucket_name: Nombre del bucket
            prefix: Prefijo/carpeta para filtrar
            max_results: Máximo número de resultados

        Returns:
            Lista de blobs
        """
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blobs = list(bucket.list_blobs(prefix=prefix, max_results=max_results))
            return blobs

        except Exception as e:
            print(f"[ERROR] Error listando blobs: {e}")
            return None

    def download_blob(self, bucket_name, source_blob_name, destination_file_name):
        """
        Descargar un archivo del bucket

        Args:
            bucket_name: Nombre del bucket
            source_blob_name: Nombre del archivo en el bucket
            destination_file_name: Ruta local donde guardar
        """
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)
            print(f"[OK] Archivo descargado: {destination_file_name}")
            return True

        except Exception as e:
            print(f"[ERROR] Error descargando archivo: {e}")
            return False

    def upload_blob(self, bucket_name, source_file_name, destination_blob_name):
        """
        Subir un archivo al bucket

        Args:
            bucket_name: Nombre del bucket
            source_file_name: Ruta local del archivo
            destination_blob_name: Nombre en el bucket
        """
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name)
            print(f"[OK] Archivo subido: {destination_blob_name}")
            return True

        except Exception as e:
            print(f"[ERROR] Error subiendo archivo: {e}")
            return False

    def delete_blob(self, bucket_name, blob_name):
        """Eliminar un archivo del bucket"""
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            print(f"[OK] Archivo eliminado: {blob_name}")
            return True

        except Exception as e:
            print(f"[ERROR] Error eliminando archivo: {e}")
            return False

    def get_bucket_size(self, bucket_name, prefix=None):
        """Obtener tamaño total de un bucket o prefijo"""
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)

            total_size = 0
            file_count = 0

            for blob in blobs:
                total_size += blob.size
                file_count += 1

            # Convertir a GB
            size_gb = total_size / (1024**3)

            return {
                'total_bytes': total_size,
                'total_gb': round(size_gb, 2),
                'file_count': file_count
            }

        except Exception as e:
            print(f"[ERROR] Error calculando tamaño: {e}")
            return None


if __name__ == "__main__":
    # Ejemplo de uso
    print("="*80)
    print("GCP CLIENT - TEST")
    print("="*80)

    try:
        client = GCPClient()
        client.test_connection()

        print("\n" + "="*80)
        print("BUCKETS DISPONIBLES")
        print("="*80)

        buckets = client.list_buckets()
        if buckets:
            print(f"\nTotal de buckets: {len(buckets)}")
            for bucket in buckets[:10]:  # Mostrar primeros 10
                print(f"  - {bucket.name} ({bucket.location})")

        print("\n" + "="*80)
        print("INSTANCIAS COMPUTE ENGINE")
        print("="*80)

        instances = client.list_instances()
        if instances:
            total = sum(len(insts) for insts in instances.values())
            print(f"\nTotal de instancias: {total}")
            for zone, zone_instances in instances.items():
                print(f"\nZona: {zone}")
                for instance in zone_instances:
                    print(f"  - {instance.name} ({instance.status})")
        else:
            print("\nNo se encontraron instancias")

    except Exception as e:
        print(f"\n[ERROR] {e}")
