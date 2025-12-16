# 📊 CDP Consumption Analytics & ML Forecasting

Sistema completo de análisis, visualización y predicción de consumo de créditos CDP (Cloudera Data Platform) con Machine Learning, integrado con Elasticsearch y Kibana.

## 🚀 Características

### ✅ Ingesta de Datos
- Obtención automática de datos de consumo CDP
- Indexación en Elasticsearch con eliminación automática de duplicados
- Campos enriquecidos con información temporal y patrones de uso
- Etiquetas legibles en español (fin de semana, nocturno, etc.)

### ✅ Visualizaciones y Dashboards
- **10 dashboards temáticos** en Kibana
- **40+ visualizaciones especializadas**
- Análisis por cluster, entorno, tipo de instancia
- Patrones de uso (fin de semana vs semana, nocturno vs diurno)

### ✅ Predicciones con Machine Learning
- **Predicciones automáticas** para los próximos 7 días
- Análisis global y por cluster individual
- **Bandas de confianza** (límites superior e inferior)
- Soporte para Prophet (Facebook) o regresión lineal

## 📋 Requisitos

### Software Necesario
- Python 3.8+
- Acceso a Elasticsearch/Kibana (Elastic Cloud)
- Cloudera CDP CLI configurado

### Librerías Python
```bash
pip install elasticsearch pandas numpy requests urllib3
```

### Opcional (para mejores predicciones)
```bash
pip install prophet
```

## 🔧 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/cdp-tools.git
cd cdp-tools
```

### 2. Configurar credenciales
```bash
# Copiar el archivo de ejemplo
cp config.example.py config.py

# Editar config.py con tus credenciales
# IMPORTANTE: config.py está en .gitignore y NO se subirá a GitHub
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar actualización inicial
```bash
# Windows
MENU.bat

# O directamente
0_Actualizar_TODO.bat
```

## 📊 Dashboards en Kibana

### Dashboards Principales
1. **CDP - Dashboard Ejecutivo** - KPIs principales
2. **CDP - Análisis de Consumo** - Vista general completa
3. **CDP - Análisis Temporal** - Tendencias temporales
4. **CDP - Análisis de Costos** - Desglose de créditos
5. **CDP - Distribuciones** - Gráficos circulares
6. **CDP - Eficiencia y Patrones** - Patrones de uso
7. **CDP - Tendencias por Cluster** - Tendencias individuales
8. **CDP - Evolución de Horas** - Horas computadas

### Dashboards de Predicciones ML 🆕
9. **CDP - Predicciones de Consumo (ML)** - Dashboard básico
10. **CDP - Predicciones ML Completo** ⭐ - Dashboard completo con:
   - Métricas de resumen
   - Gráfico histórico + predicciones
   - Tabla detallada por cluster
   - Predicciones individuales

## 🎯 Uso

### Opción 1: Menú Interactivo (Recomendado)
```batch
MENU.bat
```

Opciones disponibles:
- **[0]** Actualizar TODO (Datos + Predicciones) ⭐
- **[1]** Actualizar solo Datos
- **[2]** Actualizar solo Predicciones ML
- **[3]** Actualizar Dashboards Principales
- **[4]** Actualizar Dashboards de Predicciones
- **[5]** Verificar Dashboards
- **[9]** Abrir Kibana

### Opción 2: Scripts Individuales

#### Actualización completa
```batch
0_Actualizar_TODO.bat
```

#### Solo datos
```batch
2_Actualizar_Elasticsearch.bat
```

#### Solo predicciones
```batch
4_Actualizar_Predicciones_ML.bat
```

### Opción 3: Scripts Python
```bash
# Ingestar datos
python cdp_to_elasticsearch.py

# Generar predicciones
python forecast_with_prophet.py

# Crear dashboards
python create_kibana_dashboard.py
python create_complete_forecast_dashboard.py

# Verificar
python verify_kibana_dashboards.py
python compare_quantities.py
```

## 📈 Predicciones ML

### Cómo funciona
El sistema utiliza **regresión lineal** (o Prophet si está instalado) para predecir:
- Consumo total diario para los próximos 7 días
- Consumo por cluster para clusters principales
- Bandas de confianza (±10% por defecto)

### Ejemplo de Predicción
```
Fecha        Créditos  Rango
2025-12-17   1,165.93  (1,049.34 - 1,282.52)
2025-12-18   1,160.66  (1,044.59 - 1,276.72)
...
Total 7 días: ~8,050 créditos
```

## 📁 Estructura del Proyecto

```
cdp-tools/
├── README.md                              # Este archivo
├── config.example.py                      # Plantilla de configuración
├── .gitignore                            # Archivos ignorados por Git
│
├── Scripts de Ingesta
│   ├── cdp_to_elasticsearch.py           # Ingesta de datos CDP
│   ├── compare_quantities.py             # Comparación CDP vs ES
│   └── verify_labels.py                  # Verificación de campos
│
├── Scripts de Predicciones ML
│   ├── forecast_with_prophet.py          # Generación de predicciones
│   ├── create_forecast_visualizations.py # Visualizaciones básicas
│   └── create_complete_forecast_dashboard.py # Dashboard completo
│
├── Scripts de Dashboards
│   ├── create_kibana_dashboard.py        # Dashboards principales
│   ├── create_cluster_trends.py          # Tendencias por cluster
│   └── verify_kibana_dashboards.py       # Verificación
│
├── Scripts Batch (Windows)
│   ├── MENU.bat                          # Menú interactivo
│   ├── 0_Actualizar_TODO.bat            # Actualización completa
│   ├── 2_Actualizar_Elasticsearch.bat   # Solo datos
│   ├── 4_Actualizar_Predicciones_ML.bat # Solo predicciones
│   └── 5_Actualizar_Dashboards_Forecast.bat # Dashboards ML
│
└── Documentación
    ├── INICIO_RAPIDO.md                  # Guía de inicio rápido
    ├── RESUMEN_COMPLETO.md               # Documentación completa
    ├── DASHBOARDS_KIBANA.md              # Listado de dashboards
    └── SISTEMA_COMPLETADO.txt            # Resumen del sistema
```

## 🔐 Seguridad

### Credenciales
- **NUNCA** subas el archivo `config.py` con tus credenciales
- Usa `config.example.py` como plantilla
- El archivo `config.py` está incluido en `.gitignore`

### Mejores Prácticas
- Usa variables de entorno para credenciales en producción
- Configura permisos mínimos necesarios en Elasticsearch
- Revisa logs regularmente

## 📊 Campos Principales

### Métricas
- `credits` - Créditos consumidos
- `quantity` - Horas computadas
- `hours` - Horas del período
- `instance_count` - Número de instancias

### Dimensiones
- `cluster_name` - Nombre del cluster
- `environment_name` - Entorno
- `cloud_provider` - Proveedor cloud
- `instance_type` - Tipo de instancia

### Etiquetas Legibles ✨
- `weekend_label` - "Fin de semana" / "Entre semana"
- `time_of_day_label` - "Nocturno" / "Diurno"
- `day_of_week_name` - Nombre del día

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👤 Autor

**Tu Nombre**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)

## 🙏 Agradecimientos

- Cloudera CDP por la API de consumo
- Elastic Stack (Elasticsearch/Kibana) por las capacidades de visualización
- Facebook Prophet por el modelo de forecasting

## 📞 Soporte

Si tienes problemas o preguntas:
- Abre un [Issue](https://github.com/tu-usuario/cdp-tools/issues)
- Revisa la [Documentación Completa](RESUMEN_COMPLETO.md)
- Consulta la [Guía de Inicio Rápido](INICIO_RAPIDO.md)

---

⭐ Si este proyecto te resultó útil, considera darle una estrella en GitHub!
