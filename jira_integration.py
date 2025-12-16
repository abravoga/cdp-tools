#!/usr/bin/env python3
"""
Integración con Jira para lectura y escritura de issues
"""

import requests
from requests.auth import HTTPBasicAuth
import json


class JiraClient:
    """Cliente para interactuar con Jira API"""

    def __init__(self, jira_url=None, username=None, api_token=None):
        """
        Inicializar cliente Jira

        Args:
            jira_url: URL base de Jira (ej: https://masorange.atlassian.net)
            username: Email del usuario
            api_token: API token de Atlassian
        """
        # Importar configuración si no se proporcionan parámetros
        if not all([jira_url, username, api_token]):
            try:
                from jira_config import JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
                jira_url = jira_url or JIRA_URL
                username = username or JIRA_USERNAME
                api_token = api_token or JIRA_API_TOKEN
            except ImportError:
                raise ValueError(
                    "Debe proporcionar credenciales o crear jira_config.py con "
                    "JIRA_URL, JIRA_USERNAME y JIRA_API_TOKEN"
                )

        self.jira_url = jira_url.rstrip('/')
        self.api_url = f"{self.jira_url}/rest/api/3"
        self.auth = HTTPBasicAuth(username, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def test_connection(self):
        """Probar conexión a Jira"""
        try:
            response = requests.get(
                f"{self.api_url}/myself",
                auth=self.auth,
                headers=self.headers
            )

            if response.status_code == 200:
                user = response.json()
                print(f"[OK] Conexion exitosa a Jira")
                print(f"  Usuario: {user.get('displayName')}")
                print(f"  Email: {user.get('emailAddress')}")
                return True
            else:
                print(f"[ERROR] Error de conexion: {response.status_code}")
                return False

        except Exception as e:
            print(f"[ERROR] Error: {e}")
            return False

    def get_projects(self):
        """Obtener lista de proyectos"""
        try:
            response = requests.get(
                f"{self.api_url}/project",
                auth=self.auth,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error obteniendo proyectos: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None

    def search_issues(self, jql, max_results=50, fields=None):
        """
        Buscar issues usando JQL

        Args:
            jql: Query en JQL (Jira Query Language)
            max_results: Número máximo de resultados
            fields: Lista de campos a incluir (None = todos)

        Returns:
            dict con resultados de la búsqueda
        """
        try:
            # Usar la nueva API v3 search/jql con POST
            payload = {
                'jql': jql,
                'maxResults': max_results
            }

            if fields:
                payload['fieldsByKeys'] = fields

            response = requests.post(
                f"{self.api_url}/search/jql",
                auth=self.auth,
                headers=self.headers,
                json=payload
            )

            if response.status_code == 200:
                result = response.json()

                # Si la respuesta tiene issues con solo IDs, necesitamos obtener los detalles
                if 'issues' in result and len(result['issues']) > 0:
                    if 'key' not in result['issues'][0]:
                        # Obtener detalles completos de cada issue
                        issue_ids = [issue['id'] for issue in result['issues']]
                        detailed_issues = []
                        for issue_id in issue_ids:
                            issue_detail = self.get_issue_by_id(issue_id)
                            if issue_detail:
                                detailed_issues.append(issue_detail)
                        result['issues'] = detailed_issues

                return result
            else:
                print(f"Error buscando issues: {response.status_code}")
                print(response.text)
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_issue_by_id(self, issue_id):
        """Obtener issue por ID numérico"""
        try:
            response = requests.get(
                f"{self.api_url}/issue/{issue_id}",
                auth=self.auth,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            return None

    def get_issue(self, issue_key):
        """
        Obtener detalles de un issue específico

        Args:
            issue_key: Key del issue (ej: PROJ-123)

        Returns:
            dict con detalles del issue
        """
        try:
            response = requests.get(
                f"{self.api_url}/issue/{issue_key}",
                auth=self.auth,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error obteniendo issue {issue_key}: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None

    def create_issue(self, project_key, summary, description, issue_type="Task", **kwargs):
        """
        Crear un nuevo issue

        Args:
            project_key: Key del proyecto (ej: PROJ)
            summary: Título del issue
            description: Descripción del issue
            issue_type: Tipo de issue (Task, Bug, Story, etc.)
            **kwargs: Campos adicionales

        Returns:
            dict con detalles del issue creado
        """
        try:
            payload = {
                "fields": {
                    "project": {
                        "key": project_key
                    },
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": description
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {
                        "name": issue_type
                    }
                }
            }

            # Agregar campos adicionales
            payload["fields"].update(kwargs)

            response = requests.post(
                f"{self.api_url}/issue",
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload)
            )

            if response.status_code == 201:
                return response.json()
            else:
                print(f"Error creando issue: {response.status_code}")
                print(response.text)
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None

    def update_issue(self, issue_key, fields):
        """
        Actualizar un issue existente

        Args:
            issue_key: Key del issue (ej: PROJ-123)
            fields: dict con campos a actualizar

        Returns:
            True si fue exitoso, False si falló
        """
        try:
            payload = {"fields": fields}

            response = requests.put(
                f"{self.api_url}/issue/{issue_key}",
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload)
            )

            if response.status_code == 204:
                return True
            else:
                print(f"Error actualizando issue: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print(f"Error: {e}")
            return False

    def add_comment(self, issue_key, comment_text):
        """
        Agregar un comentario a un issue

        Args:
            issue_key: Key del issue
            comment_text: Texto del comentario

        Returns:
            dict con detalles del comentario creado
        """
        try:
            payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment_text
                                }
                            ]
                        }
                    ]
                }
            }

            response = requests.post(
                f"{self.api_url}/issue/{issue_key}/comment",
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload)
            )

            if response.status_code == 201:
                return response.json()
            else:
                print(f"Error agregando comentario: {response.status_code}")
                print(response.text)
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_issue_transitions(self, issue_key):
        """
        Obtener transiciones disponibles para un issue

        Args:
            issue_key: Key del issue

        Returns:
            list con transiciones disponibles
        """
        try:
            response = requests.get(
                f"{self.api_url}/issue/{issue_key}/transitions",
                auth=self.auth,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json().get('transitions', [])
            else:
                print(f"Error obteniendo transiciones: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None

    def transition_issue(self, issue_key, transition_id):
        """
        Transicionar un issue (cambiar estado)

        Args:
            issue_key: Key del issue
            transition_id: ID de la transición

        Returns:
            True si fue exitoso, False si falló
        """
        try:
            payload = {
                "transition": {
                    "id": transition_id
                }
            }

            response = requests.post(
                f"{self.api_url}/issue/{issue_key}/transitions",
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload)
            )

            if response.status_code == 204:
                return True
            else:
                print(f"Error transicionando issue: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print(f"Error: {e}")
            return False


if __name__ == "__main__":
    # Ejemplo de uso
    print("="*80)
    print("JIRA CLIENT - TEST")
    print("="*80)

    client = JiraClient()
    client.test_connection()

    print("\n" + "="*80)
    print("PROYECTOS DISPONIBLES")
    print("="*80)

    projects = client.get_projects()
    if projects:
        print(f"\nTotal de proyectos: {len(projects)}")
        for project in projects[:10]:  # Mostrar primeros 10
            print(f"  - {project.get('key')}: {project.get('name')}")
