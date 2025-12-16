#!/usr/bin/env python3
"""
Ejemplos de uso de Jira Integration
"""

from jira_integration import JiraClient
import json


def example_search_my_issues():
    """Buscar mis issues asignados"""
    print("\n" + "="*80)
    print("EJEMPLO 1: Buscar mis issues asignados")
    print("="*80)

    client = JiraClient()

    # JQL: Jira Query Language
    jql = "assignee = currentUser() AND resolution = Unresolved ORDER BY created DESC"

    results = client.search_issues(jql, max_results=10)

    if results:
        issues = results.get('issues', [])
        print(f"\nTotal de issues encontrados: {results.get('total', 0)}")
        print(f"Mostrando: {len(issues)}\n")

        for issue in issues:
            key = issue.get('key')
            fields = issue.get('fields', {})
            summary = fields.get('summary', 'Sin titulo')
            status = fields.get('status', {}).get('name', 'Sin estado')
            project = fields.get('project', {}).get('key', 'N/A')

            print(f"  [{key}] {summary}")
            print(f"    Proyecto: {project} | Estado: {status}")
            print()


def example_search_by_project(project_key):
    """Buscar issues de un proyecto específico"""
    print("\n" + "="*80)
    print(f"EJEMPLO 2: Buscar issues del proyecto {project_key}")
    print("="*80)

    client = JiraClient()

    jql = f"project = {project_key} ORDER BY created DESC"

    results = client.search_issues(jql, max_results=10)

    if results:
        issues = results.get('issues', [])
        print(f"\nTotal de issues en {project_key}: {results.get('total', 0)}")
        print(f"Mostrando: {len(issues)}\n")

        for issue in issues:
            key = issue.get('key')
            fields = issue.get('fields', {})
            summary = fields.get('summary', 'Sin titulo')
            status = fields.get('status', {}).get('name', 'Sin estado')
            issue_type = fields.get('issuetype', {}).get('name', 'N/A')

            print(f"  [{key}] {summary}")
            print(f"    Tipo: {issue_type} | Estado: {status}")
            print()


def example_get_issue_details(issue_key):
    """Obtener detalles completos de un issue"""
    print("\n" + "="*80)
    print(f"EJEMPLO 3: Detalles del issue {issue_key}")
    print("="*80)

    client = JiraClient()

    issue = client.get_issue(issue_key)

    if issue:
        fields = issue.get('fields', {})

        print(f"\nKey: {issue.get('key')}")
        print(f"Summary: {fields.get('summary')}")
        print(f"Status: {fields.get('status', {}).get('name')}")
        print(f"Type: {fields.get('issuetype', {}).get('name')}")
        print(f"Priority: {fields.get('priority', {}).get('name', 'N/A')}")
        print(f"Reporter: {fields.get('reporter', {}).get('displayName', 'N/A')}")
        print(f"Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}")
        print(f"Created: {fields.get('created')}")
        print(f"Updated: {fields.get('updated')}")

        # Descripción
        description_content = fields.get('description', {})
        if description_content:
            print(f"\nDescription:")
            # La descripción viene en formato Atlassian Document Format
            print("  [Ver en Jira para formato completo]")

        # Comentarios
        comments = fields.get('comment', {}).get('comments', [])
        if comments:
            print(f"\nComentarios: {len(comments)}")
            for comment in comments[:3]:  # Mostrar primeros 3
                author = comment.get('author', {}).get('displayName', 'Unknown')
                created = comment.get('created', '')
                print(f"  - {author} ({created[:10]})")


def example_search_recent_bugs():
    """Buscar bugs recientes"""
    print("\n" + "="*80)
    print("EJEMPLO 4: Buscar bugs recientes")
    print("="*80)

    client = JiraClient()

    jql = "type = Bug AND created >= -30d ORDER BY created DESC"

    results = client.search_issues(jql, max_results=10)

    if results:
        issues = results.get('issues', [])
        print(f"\nBugs creados en los ultimos 30 dias: {results.get('total', 0)}")
        print(f"Mostrando: {len(issues)}\n")

        for issue in issues:
            key = issue.get('key')
            fields = issue.get('fields', {})
            summary = fields.get('summary', 'Sin titulo')
            status = fields.get('status', {}).get('name', 'Sin estado')
            project = fields.get('project', {}).get('key', 'N/A')
            created = fields.get('created', '')[:10]

            print(f"  [{key}] {summary}")
            print(f"    Proyecto: {project} | Estado: {status} | Creado: {created}")
            print()


def example_list_projects():
    """Listar todos los proyectos disponibles"""
    print("\n" + "="*80)
    print("EJEMPLO 5: Listar proyectos")
    print("="*80)

    client = JiraClient()

    projects = client.get_projects()

    if projects:
        print(f"\nTotal de proyectos: {len(projects)}\n")

        # Agrupar por letra inicial
        projects_by_letter = {}
        for project in projects:
            key = project.get('key', '')
            if key:
                first_letter = key[0].upper()
                if first_letter not in projects_by_letter:
                    projects_by_letter[first_letter] = []
                projects_by_letter[first_letter].append(project)

        # Mostrar primeras 5 letras
        for letter in sorted(projects_by_letter.keys())[:5]:
            print(f"\n{letter}:")
            for project in projects_by_letter[letter][:5]:
                print(f"  - {project.get('key')}: {project.get('name')}")


def main():
    """Ejecutar ejemplos"""
    print("="*80)
    print("JIRA INTEGRATION - EJEMPLOS DE USO")
    print("="*80)

    # Ejemplo 1: Mis issues
    example_search_my_issues()

    # Ejemplo 2: Issues de un proyecto específico
    # (Descomentar y cambiar por un proyecto que tengas)
    # example_search_by_project('DATAD')

    # Ejemplo 3: Detalles de un issue
    # (Descomentar y cambiar por un issue específico)
    # example_get_issue_details('DATAD-123')

    # Ejemplo 4: Bugs recientes
    example_search_recent_bugs()

    # Ejemplo 5: Listar proyectos
    example_list_projects()

    print("\n" + "="*80)
    print("EJEMPLOS COMPLETADOS")
    print("="*80)
    print("\nPuedes modificar este script para probar otras consultas JQL")
    print("Documentacion JQL: https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jira-query-language-jql/")


if __name__ == "__main__":
    main()
