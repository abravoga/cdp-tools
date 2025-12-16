# CDP Tools - Sistema de Análisis y Predicción de Consumo

Sistema completo para análisis, visualización y predicción de consumo de créditos CDP en Elasticsearch/Kibana.

## 📋 Características

### ✅ Ingesta de Datos
- Obtención automática de datos de consumo CDP (últimos 30 días)
- Indexación en Elasticsearch con eliminación de duplicados
- Campos enriquecidos con información temporal y patrones de uso

### ✅ Visualizaciones y Dashboards
- 8+ dashboards temáticos en Kibana
- 30+ visualizaciones especializadas
- Análisis por cluster, entorno, tipo de instancia, etc.

### ✅ Predicciones con Machine Learning
- Predicciones de consumo para los próximos 7 días
- Análisis por cluster individual
- Bandas de confianza (límites superior e inferior)

## 🚀 Scripts Disponibles

### Scripts Batch (.bat)

1. **0_Actualizar_TODO.bat** ⭐
   - Actualización completa del sistema
   - Ejecuta: ingesta de datos + predicciones ML
   - **Recomendado para uso diario**

2. **1_Generar_Dashboard_HTML.bat**
   - Genera dashboard HTML estático
   - Útil para reportes offline

3. **2_Actualizar_Elasticsearch.bat**
   - Solo actualiza datos en Elasticsearch
   - Últimos 30 días de consumo CDP

4. **3_Actualizar_Dashboards_Kibana.bat**
   - Recrea/actualiza dashboards en Kibana
   - Útil después de cambios en estructura

5. **4_Actualizar_Predicciones_ML.bat**
   - Solo genera predicciones ML
   - Próximos 7 días de forecast

### Scripts Python

- `cdp_to_elasticsearch.py` - Ingesta de datos CDP
- `forecast_with_prophet.py` - Generación de predicciones ML
- `create_kibana_dashboard.py` - Creación de dashboards
- `verify_labels.py` - Verificación de datos
- `compare_quantities.py` - Comparación CDP vs Elasticsearch

## 📊 Dashboards en Kibana

### Dashboards Principales

1. **CDP - Análisis de Consumo** (Completo)
   - Vista general con todas las métricas
   - Gráficos temporales, distribuciones y tablas

2. **CDP - Dashboard Ejecutivo**
   - KPIs principales
   - Vista de alto nivel para management

3. **CDP - Análisis Temporal**
   - Tendencias en el tiempo
   - Patrones diarios, semanales

4. **CDP - Análisis de Costos**
   - Desglose detallado de créditos
   - Por cluster, entorno, tipo de instancia

5. **CDP - Distribuciones**
   - Gráficos circulares (donuts/pies)
   - Distribución de recursos

6. **CDP - Eficiencia y Patrones**
   - Fin de semana vs semana
   - Nocturno vs diurno
   - Franjas horarias

7. **CDP - Tendencias por Cluster** 🆕
   - Tendencias individuales de top 5 clusters
   - Comparación visual entre clusters

8. **CDP - Evolución de Horas por Cluster** 🆕
   - Horas computadas por cluster
   - Gráficos de área

9. **CDP - Predicciones de Consumo (ML)** 🆕
   - Predicciones para próximos 7 días
   - Datos históricos + forecast

## 📈 Predicciones ML

### Cómo funciona

El sistema utiliza **regresión lineal** (o Prophet si está instalado) para predecir:

- **Consumo total diario** para los próximos 7 días
- **Consumo por cluster** para clusters principales
- **Bandas de confianza** (±10% por defecto)

### Ejemplo de Predicción

```
Fecha        Créditos  Rango
2025-12-17   1,165.93  (1,049.34 - 1,282.52)
2025-12-18   1,160.66  (1,044.59 - 1,276.72)
2025-12-19   1,155.39  (1,039.85 - 1,270.93)
...
Total 7 días: ~8,050 créditos
```

### Clusters con Predicción Individual

1. **gea-cem-prod** - ~595 créditos/día
2. **gcp-prod-datahub** - ~488 créditos/día
3. Total general - ~1,150 créditos/día

## 🔧 Configuración

### Elasticsearch/Kibana
- URL Elasticsearch: `gea-data-cloud-masorange-es.es.europe-west1.gcp.cloud.es.io`
- URL Kibana: `gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io`
- Usuario: `infra_admin`

### Índices

**Datos de Consumo:**
- `cdp-consumption-records-YYYY.MM.DD` - Registros individuales
- `cdp-consumption-summary-YYYY.MM.DD` - Datos agregados

**Predicciones:**
- `cdp-consumption-forecast-YYYY.MM.DD` - Predicciones ML

### Campos Principales

**Métricas:**
- `credits` - Créditos consumidos (grossCharge de CDP)
- `quantity` - Horas computadas
- `hours` - Horas del periodo
- `instance_count` - Número de instancias

**Dimensiones:**
- `cluster_name` - Nombre del cluster
- `environment_name` - Entorno (prod, pre, dev)
- `cloud_provider` - Proveedor cloud (GCP)
- `instance_type` - Tipo de instancia

**Tiempo:**
- `@timestamp` - Timestamp principal
- `usage_start` / `usage_end` - Período de uso
- `hour_of_day` - Hora del día (0-23)
- `day_of_week` - Día semana (0=Lunes, 6=Domingo)
- `day_of_week_name` - Nombre del día

**Patrones:**
- `weekend_label` - "Fin de semana" / "Entre semana" ✨
- `time_of_day_label` - "Nocturno" / "Diurno" ✨
- `time_block` - Bloque 4 horas (00:00-04:00, etc.)
- `is_weekend` - Boolean
- `is_night` - Boolean

## 📅 Uso Recomendado

### Actualización Diaria
```batch
# Ejecutar cada mañana
0_Actualizar_TODO.bat
```

### Actualización Solo Datos
```batch
# Solo refrescar datos CDP
2_Actualizar_Elasticsearch.bat
```

### Actualización Solo Predicciones
```batch
# Solo regenerar predicciones
4_Actualizar_Predicciones_ML.bat
```

## 🔍 Verificación de Datos

### Comparar CDP vs Elasticsearch
```batch
python compare_quantities.py
```

### Ver campos legibles
```batch
python verify_labels.py
```

### Ver top clusters
```batch
python get_top_clusters.py
```

## 📊 Accesos Rápidos

- **Dashboards**: https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards
- **Discover**: https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/discover

## 🛠️ Mejoras Futuras

### Para mejores predicciones (Opcional)

Instalar Prophet para predicciones más precisas:
```batch
pip install prophet
```

Nota: Prophet requiere compilación y puede tardar en instalarse.

### Automatización con Task Scheduler

Crear tarea programada en Windows:
1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Trigger: Diario a las 7:00 AM
4. Acción: Ejecutar `0_Actualizar_TODO.bat`

## 📝 Notas Importantes

- Los datos se obtienen de los **últimos 30 días**
- Las predicciones son para los **próximos 7 días**
- Los índices antiguos se **eliminan automáticamente** para evitar duplicados
- Los dashboards se actualizan automáticamente al refrescar Kibana

## 🐛 Solución de Problemas

### "Connection timeout"
- Verificar conectividad a Elastic Cloud
- El puerto correcto es **443** (HTTPS)

### "Datos duplicados"
- El script elimina índices antiguos automáticamente
- Si persiste, ejecutar `2_Actualizar_Elasticsearch.bat`

### "True/false en dashboards"
- Los campos legibles ya están configurados
- Usar `weekend_label` y `time_of_day_label`

### "Error col3 en visualizaciones"
- Usar dashboards "por Cluster" que evitan este problema
- Visualizaciones individuales ya creadas

---

**Última actualización**: 2025-12-16
**Versión**: 2.0 - Con ML y Predicciones
