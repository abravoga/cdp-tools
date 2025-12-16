# 📚 Guía de Configuración de Confluence

Esta guía te ayudará a conectar el sistema CDP Tools con Confluence para leer y escribir documentación.

## 🎯 ¿Qué Podrás Hacer?

### ✅ Lectura
- Buscar documentación existente en Confluence
- Leer páginas específicas
- Consultar espacios y estructuras
- Usar como contexto para consultas

### ✅ Escritura
- Crear nueva documentación automáticamente
- Actualizar páginas existentes
- Sincronizar README y guías del proyecto
- Generar reportes automáticos

---

## 🔧 Configuración Paso a Paso

### Paso 1: Obtener API Token de Atlassian

1. **Ir a la página de tokens**:
   - Ve a: https://id.atlassian.com/manage-profile/security/api-tokens
   - Inicia sesión con tu cuenta de Atlassian

2. **Crear nuevo token**:
   - Click en **"Create API token"**
   - Label: `CDP Tools Integration`
   - Click en **"Create"**

3. **Copiar el token**:
   - ⚠️ **IMPORTANTE**: Copia el token AHORA (solo se muestra una vez)
   - Guárdalo temporalmente en un lugar seguro

### Paso 2: Obtener Información de tu Confluence

Necesitas saber:

1. **URL de Confluence**:
   - Si usas Confluence Cloud: `https://TU-EMPRESA.atlassian.net/wiki`
   - Si usas Confluence Server: `https://confluence.tu-empresa.com`

2. **Clave del Espacio** (Space Key):
   - Ve a tu espacio en Confluence
   - La URL será algo como: `https://empresa.atlassian.net/wiki/spaces/CDP/...`
   - La clave del espacio es `CDP` (la parte después de `/spaces/`)

3. **Tu Email** (Usuario):
   - El email con el que accedes a Confluence

### Paso 3: Configurar el Archivo

1. **Copiar el archivo de ejemplo**:
   ```bash
   cd C:\Users\abravoga\cdp-tools
   copy confluence_config.example.py confluence_config.py
   ```

2. **Editar `confluence_config.py`**:
   ```python
   # Configuración de Confluence
   CONFLUENCE_URL = 'https://tu-empresa.atlassian.net/wiki'  # Tu URL
   CONFLUENCE_USERNAME = 'tu-email@empresa.com'  # Tu email
   CONFLUENCE_API_TOKEN = 'ATATT3xFfGF0...'  # El token que copiaste

   # Configuración de espacios
   CONFLUENCE_SPACE_KEY = 'CDP'  # La clave de tu espacio
   ```

3. **Guardar el archivo**

---

## ✅ Verificar la Conexión

Ejecuta el script de prueba:

```bash
python confluence_integration.py
```

**Resultado esperado**:
```
================================================================================
Confluence Integration - Cliente de Prueba
================================================================================

1. Probando conexión...
[OK] Conexión exitosa con Confluence

2. Obteniendo espacios disponibles...

   Espacios encontrados (5):
   - CDP: CDP Platform
   - IT: IT Documentation
   - TECH: Technical Docs
   ...

================================================================================
Conexión establecida. Puedes usar el cliente para leer/escribir.
================================================================================
```

---

## 📊 Sincronizar Documentación del Proyecto

Una vez configurado, puedes sincronizar toda la documentación:

```bash
python sync_to_confluence.py
```

Esto creará/actualizará en Confluence:
- **CDP Tools - README Principal**
- **CDP Tools - Inicio Rápido**
- **CDP Tools - Resumen Completo**
- **CDP Tools - Dashboards de Kibana**

Todas bajo una página padre: **"CDP Tools - Documentación"**

---

## 🔐 Seguridad

### ⚠️ IMPORTANTE

- **confluence_config.py** contiene credenciales sensibles
- ✅ Ya está en `.gitignore` (NO se subirá a GitHub)
- ✅ Solo `confluence_config.example.py` se sube a GitHub
- ❌ NUNCA compartas tu API token

### Buenas Prácticas

1. **Revocación de tokens**:
   - Revoca tokens que no uses en: https://id.atlassian.com/manage-profile/security/api-tokens

2. **Permisos mínimos**:
   - Usa una cuenta con permisos solo en los espacios necesarios

3. **Rotación de tokens**:
   - Cambia el API token periódicamente (cada 3-6 meses)

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Leer una Página

```python
from confluence_integration import ConfluenceClient

client = ConfluenceClient()

# Buscar página por título
page = client.get_page_by_title('CDP', 'Documentación Técnica')

if page:
    print(f"Título: {page['title']}")
    print(f"Contenido: {page['body']['storage']['value']}")
```

### Ejemplo 2: Crear una Página

```python
from confluence_integration import ConfluenceClient

client = ConfluenceClient()

content = """
<h1>Mi Nueva Página</h1>
<p>Contenido de ejemplo...</p>
"""

page = client.create_page(
    space_key='CDP',
    title='Mi Documentación',
    content=content
)

print(f"Página creada: {page['id']}")
```

### Ejemplo 3: Buscar Contenido

```python
from confluence_integration import ConfluenceClient

client = ConfluenceClient()

# Buscar por texto
results = client.search_content('CDP consumption', space_key='CDP')

for result in results:
    print(f"- {result['title']}")
```

---

## 🛠️ Solución de Problemas

### Error: "401 Unauthorized"

**Causa**: API token incorrecto o expirado

**Solución**:
1. Verifica que copiaste el token completo
2. Crea un nuevo API token
3. Actualiza `confluence_config.py`

### Error: "403 Forbidden"

**Causa**: No tienes permisos en el espacio

**Solución**:
1. Verifica que tienes permisos de escritura en el espacio
2. Pide permisos al administrador de Confluence
3. Usa un espacio donde tengas permisos

### Error: "404 Not Found"

**Causa**: URL de Confluence incorrecta o espacio no existe

**Solución**:
1. Verifica la URL de Confluence
2. Verifica que el Space Key es correcto
3. Prueba accediendo manualmente a la URL

### Error: "Connection timeout"

**Causa**: Problemas de red o firewall

**Solución**:
1. Verifica conectividad de red
2. Comprueba si hay firewall bloqueando
3. Contacta IT si es necesario

---

## 📝 Scripts Disponibles

### `confluence_integration.py`
Cliente principal con todas las funciones:
- `test_connection()` - Probar conexión
- `get_spaces()` - Listar espacios
- `get_page_by_title()` - Buscar página
- `search_content()` - Buscar contenido
- `create_page()` - Crear página
- `update_page()` - Actualizar página
- `create_or_update_page()` - Crear o actualizar

### `sync_to_confluence.py`
Sincroniza documentación del proyecto automáticamente

### `confluence_config.py`
Tu configuración (credenciales) - NO se sube a GitHub

### `confluence_config.example.py`
Plantilla de configuración - SÍ se sube a GitHub

---

## 🎯 Próximos Pasos

1. ✅ Configurar credenciales
2. ✅ Probar conexión
3. ✅ Sincronizar documentación
4. 📊 Crear reportes automáticos (próximamente)
5. 🤖 Integrar con actualizaciones diarias (próximamente)

---

## 📞 Ayuda

Si tienes problemas:
1. Verifica la configuración en `confluence_config.py`
2. Ejecuta `python confluence_integration.py` para probar
3. Revisa los logs de error
4. Consulta la documentación de Confluence API:
   - https://developer.atlassian.com/cloud/confluence/rest/

---

**Versión**: 1.0
**Última actualización**: 2025-12-16
