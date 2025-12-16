#!/usr/bin/env python3
"""
Configuración para Confluence

INSTRUCCIONES:
1. Copia este archivo y renómbralo a 'confluence_config.py'
2. Actualiza los valores con tu información de Confluence
3. NUNCA subas confluence_config.py a GitHub (está en .gitignore)
"""

# Configuración de Confluence
CONFLUENCE_URL = 'https://tu-empresa.atlassian.net/wiki'  # O tu URL de Confluence
CONFLUENCE_USERNAME = 'tu-email@empresa.com'  # Tu email de Atlassian
CONFLUENCE_API_TOKEN = 'tu-api-token-aqui'  # Crear en: https://id.atlassian.com/manage-profile/security/api-tokens

# Configuración de espacios
CONFLUENCE_SPACE_KEY = 'CDP'  # La clave del espacio donde trabajar (ej: 'IT', 'TECH', 'CDP')

# Configuración de páginas del proyecto CDP
CDP_PARENT_PAGE_TITLE = 'CDP Tools - Documentación'  # Página padre para toda la documentación
CDP_PARENT_PAGE_ID = None  # Si conoces el ID, ponlo aquí. Si no, déjalo en None

# Configuración de sincronización
AUTO_SYNC = False  # Si True, actualiza automáticamente cuando se ejecutan scripts
CREATE_IF_NOT_EXISTS = True  # Si True, crea páginas nuevas si no existen
