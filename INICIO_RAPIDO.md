# 🚀 INICIO RÁPIDO - Sistema CDP

## ⚡ Empezar en 3 Pasos

### 1️⃣ Ejecutar el Menú Principal
```batch
MENU.bat
```

### 2️⃣ Seleccionar Opción [0] - Actualizar TODO
Esto actualiza automáticamente:
- ✅ Datos de consumo CDP (últimos 30 días)
- ✅ Predicciones ML (próximos 7 días)

### 3️⃣ Abrir Kibana desde el Menú
Opción [A] - Abre directamente el dashboard de predicciones ML

---

## 📊 Dashboards Principales que Debes Ver

### 1. **CDP - Predicciones ML Completo** 🌟
El más completo con:
- Métricas de resumen (total, promedio, min, max)
- Gráfico histórico + predicciones futuras
- Tabla detallada por cluster
- Predicciones individuales por cluster

**URL Directa**:
https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards#/view/dashboard-cdp-forecast-complete

### 2. **CDP - Dashboard Ejecutivo**
Vista rápida con KPIs principales

### 3. **CDP - Análisis de Consumo**
Vista general completa de todo el consumo

### 4. **CDP - Tendencias por Cluster**
Tendencias individuales de cada cluster principal

---

## 📅 Uso Diario

### Recomendación: Ejecutar cada mañana
```batch
0_Actualizar_TODO.bat
```

O mejor aún, usa el **MENU.bat** y selecciona opción [0]

---

## 🎯 Datos Actuales del Sistema

### Clusters Principales
1. **gea-cem-prod** - ~595 créditos/día (predicho)
2. **gcp-prod-datahub** - ~488 créditos/día (predicho)

### Predicciones
- **Total próximos 7 días**: ~8,050 créditos
- **Promedio diario**: ~1,150 créditos

---

## 🛠️ Scripts Disponibles

### Menú Interactivo
- **MENU.bat** - Menú principal con todas las opciones

### Scripts Automáticos
- **0_Actualizar_TODO.bat** - Actualiza datos + predicciones
- **2_Actualizar_Elasticsearch.bat** - Solo datos
- **4_Actualizar_Predicciones_ML.bat** - Solo predicciones
- **5_Actualizar_Dashboards_Forecast.bat** - Recrea dashboards ML

### Scripts de Verificación
```python
python verify_kibana_dashboards.py  # Ver todos los dashboards
python compare_quantities.py        # Comparar datos CDP vs ES
```

---

## 📚 Documentación Completa

- **RESUMEN_COMPLETO.md** - Documentación completa del sistema
- **DASHBOARDS_KIBANA.md** - Listado de todos los dashboards
- **README_COMPLETO.md** - Documentación técnica detallada

---

## ✨ Lo Más Importante

### ✅ El sistema ya está 100% configurado y funcional
### ✅ Solo necesitas ejecutar MENU.bat
### ✅ Todo se actualiza automáticamente

---

## 🔗 Acceso Directo a Kibana

**Todos los Dashboards**:
https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards

**Predicciones ML Completo** (Recomendado):
https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards#/view/dashboard-cdp-forecast-complete

---

## ❓ Preguntas Frecuentes

### ¿Con qué frecuencia actualizar?
**Recomendado**: Una vez al día (cada mañana)

### ¿Qué script ejecutar?
**Recomendado**: MENU.bat → Opción [0]

### ¿Qué dashboard ver primero?
**Recomendado**: CDP - Predicciones ML Completo

### ¿Los datos son precisos?
Sí, el sistema elimina duplicados automáticamente y compara con CDP

### ¿Las predicciones son confiables?
Sí, incluyen bandas de confianza (límites superior e inferior)

---

## 🎉 ¡Listo para Usar!

El sistema está completamente funcional. Solo ejecuta:
```batch
MENU.bat
```

Y selecciona la opción que necesites.

---

**Versión**: 3.0
**Estado**: ✅ Completamente Funcional
**Última Actualización**: 2025-12-16
