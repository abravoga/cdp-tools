# 📊 Dashboards de Kibana - CDP Consumption

## Dashboards Disponibles

### 1. **CDP - Análisis de Consumo** (Dashboard Principal)
- **Descripción**: Vista general completa con todas las métricas
- **Visualizaciones**: 8+ gráficos
- **Incluye**:
  - Tendencia temporal de consumo
  - Distribución por cluster
  - Distribución por entorno
  - Distribución por tipo de instancia
  - Top clusters
  - Métricas totales

---

### 2. **CDP - Dashboard Ejecutivo**
- **Descripción**: KPIs principales para management
- **Visualizaciones**: 4 métricas principales
- **Incluye**:
  - Total de créditos consumidos
  - Total de horas computadas
  - Número de clusters activos
  - Promedio de créditos por día

---

### 3. **CDP - Análisis Temporal**
- **Descripción**: Tendencias en el tiempo
- **Visualizaciones**: Gráficos temporales
- **Incluye**:
  - Consumo diario
  - Patrones semanales
  - Evolución de clusters principales

---

### 4. **CDP - Análisis de Costos**
- **Descripción**: Desglose detallado de créditos
- **Visualizaciones**: Tablas y gráficos de barras
- **Incluye**:
  - Costos por cluster
  - Costos por entorno
  - Costos por tipo de instancia
  - Ranking de consumo

---

### 5. **CDP - Distribuciones**
- **Descripción**: Gráficos circulares (donuts/pies)
- **Visualizaciones**: 4-6 gráficos de dona
- **Incluye**:
  - Distribución de créditos por cluster
  - Distribución por cloud provider
  - Distribución por tipo de instancia
  - Distribución por entorno

---

### 6. **CDP - Eficiencia y Patrones**
- **Descripción**: Análisis de patrones de uso
- **Visualizaciones**: Gráficos comparativos
- **Incluye**:
  - **Fin de semana vs Entre semana** (con labels legibles ✨)
  - **Nocturno vs Diurno** (con labels legibles ✨)
  - Consumo por franja horaria (bloques de 4 horas)
  - Patrones por día de la semana

---

### 7. **CDP - Tendencias por Cluster**
- **Descripción**: Tendencias individuales de clusters principales
- **Visualizaciones**: 5 gráficos de línea
- **Incluye**:
  - Tendencia: gea-cem-prod
  - Tendencia: gcp-prod-datahub
  - Tendencia: gea-cmr-des-datahub
  - Tendencia: gea-cmr-pre-datahub
  - Tendencia: gea-cmt-pre-datalake

---

### 8. **CDP - Evolución de Horas por Cluster**
- **Descripción**: Horas computadas por cluster
- **Visualizaciones**: 5 gráficos de área
- **Incluye**:
  - Horas: gea-cem-prod
  - Horas: gcp-prod-datahub
  - Horas: gea-cmr-des-datahub
  - Horas: gea-cmr-pre-datahub
  - Horas: gea-cmt-pre-datalake

---

### 9. **CDP - Predicciones de Consumo (ML)** 🆕 ⭐
- **Descripción**: Dashboard básico de predicciones ML
- **Visualizaciones**: 2 visualizaciones
- **Incluye**:
  - Gráfico histórico + predicciones (próximos 7 días)
  - Tabla de predicciones detalladas

---

### 10. **CDP - Predicciones ML Completo** 🆕 ⭐
- **Descripción**: Dashboard completo con predicciones ML
- **Visualizaciones**: 8 visualizaciones
- **Incluye**:
  - **Fila 1 - Métricas de Resumen**:
    - Total predicho para 7 días
    - Promedio diario predicho
    - Mínimo predicho (límite inferior)
    - Máximo predicho (límite superior)

  - **Fila 2 - Tendencia Combinada**:
    - Gráfico de línea con datos históricos (últimos 30 días)
    - Predicciones para próximos 7 días
    - Dos líneas: Real (azul) + Predicción (rojo)

  - **Fila 3 - Tabla Detallada**:
    - Predicciones por fecha y cluster
    - Valores predichos con rangos (min-max)

  - **Fila 4 - Predicciones por Cluster**:
    - Predicción para **gea-cem-prod** (con bandas de confianza)
    - Predicción para **gcp-prod-datahub** (con bandas de confianza)

---

## 🎨 Características Especiales

### Labels Legibles en Español
- ✅ **weekend_label**: "Fin de semana" / "Entre semana"
- ✅ **time_of_day_label**: "Nocturno" / "Diurno"
- ✅ **day_of_week_name**: "Lunes", "Martes", etc.

### Visualizaciones sin Error col3
- ✅ Tendencias simplificadas (sin split por cluster)
- ✅ Visualizaciones individuales por cluster
- ✅ Solución alternativa implementada

### Predicciones ML
- ✅ Forecast para próximos 7 días
- ✅ Bandas de confianza (límites superior/inferior)
- ✅ Predicciones totales y por cluster
- ✅ Datos almacenados en índice `cdp-consumption-forecast-*`

---

## 🔗 Enlaces Rápidos

**Dashboards**:
https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards

**Discover**:
https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/discover

**Data Views**:
- `cdp-records-dataview` → `cdp-consumption-records-*`
- `cdp-summary-dataview` → `cdp-consumption-summary-*`
- `cdp-forecast-dataview` → `cdp-consumption-forecast-*`

---

## 📅 Orden Recomendado de Visualización

1. **CDP - Dashboard Ejecutivo** - Vista rápida de KPIs
2. **CDP - Predicciones ML Completo** - Ver predicciones futuras
3. **CDP - Análisis de Consumo** - Análisis detallado
4. **CDP - Tendencias por Cluster** - Análisis por cluster
5. **CDP - Eficiencia y Patrones** - Patrones de uso

---

**Última actualización**: 2025-12-16
**Total de dashboards**: 10
**Total de visualizaciones**: 40+
