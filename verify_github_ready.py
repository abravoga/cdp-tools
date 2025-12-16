#!/usr/bin/env python3
"""
Verificar que el repositorio está listo para GitHub
Verifica que no se incluyan credenciales ni archivos sensibles
"""

import os
import subprocess

def check_git_status():
    """Verificar estado de Git"""
    print("=" * 80)
    print("VERIFICACION DE REPOSITORIO PARA GITHUB")
    print("=" * 80)

    # Verificar que .git existe
    if not os.path.exists('.git'):
        print("\n[ERROR] No se encontró repositorio Git")
        print("Ejecuta: git init")
        return False

    print("\n[OK] Repositorio Git encontrado")
    return True

def check_gitignore():
    """Verificar que .gitignore existe y contiene lo necesario"""
    print("\n1. Verificando .gitignore...")

    if not os.path.exists('.gitignore'):
        print("   [ERROR] .gitignore no encontrado")
        return False

    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()

    required = ['config.py', '__pycache__', '*.pyc', '.env']
    missing = []

    for item in required:
        if item not in content:
            missing.append(item)

    if missing:
        print(f"   [WARNING] Faltan entradas en .gitignore: {missing}")
    else:
        print("   [OK] .gitignore correctamente configurado")

    return True

def check_sensitive_files():
    """Verificar que archivos sensibles no están en staging"""
    print("\n2. Verificando archivos sensibles...")

    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            capture_output=True,
            text=True
        )

        tracked_files = result.stdout.split('\n')

        sensitive = ['config.py', '.env', 'credentials.json']
        found_sensitive = []

        for file in sensitive:
            if file in tracked_files:
                found_sensitive.append(file)

        if found_sensitive:
            print(f"   [ERROR] Archivos sensibles encontrados: {found_sensitive}")
            print("   ACCION: Elimina estos archivos del repositorio")
            print("   git rm --cached config.py")
            return False
        else:
            print("   [OK] No se encontraron archivos sensibles")
            return True

    except Exception as e:
        print(f"   [ERROR] No se pudo verificar: {e}")
        return False

def check_config_example():
    """Verificar que config.example.py existe"""
    print("\n3. Verificando config.example.py...")

    if not os.path.exists('config.example.py'):
        print("   [WARNING] config.example.py no encontrado")
        print("   Crea un archivo de ejemplo sin credenciales reales")
        return False

    with open('config.example.py', 'r', encoding='utf-8') as f:
        content = f.read()

    if 'imdeveloperS' in content or 'infra_admin' in content:
        print("   [ERROR] config.example.py contiene credenciales reales")
        print("   Reemplaza con valores de ejemplo")
        return False

    print("   [OK] config.example.py encontrado y sin credenciales reales")
    return True

def check_readme():
    """Verificar que README.md existe"""
    print("\n4. Verificando README.md...")

    if not os.path.exists('README.md'):
        print("   [WARNING] README.md no encontrado")
        return False

    print("   [OK] README.md encontrado")
    return True

def check_license():
    """Verificar que LICENSE existe"""
    print("\n5. Verificando LICENSE...")

    if not os.path.exists('LICENSE'):
        print("   [WARNING] LICENSE no encontrado")
        print("   Considera agregar una licencia (MIT, Apache, etc.)")
        return False

    print("   [OK] LICENSE encontrado")
    return True

def check_requirements():
    """Verificar que requirements.txt existe"""
    print("\n6. Verificando requirements.txt...")

    if not os.path.exists('requirements.txt'):
        print("   [WARNING] requirements.txt no encontrado")
        return False

    print("   [OK] requirements.txt encontrado")
    return True

def check_commits():
    """Verificar que hay commits"""
    print("\n7. Verificando commits...")

    try:
        result = subprocess.run(
            ['git', 'log', '--oneline'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout:
            commits = result.stdout.split('\n')
            print(f"   [OK] {len([c for c in commits if c])} commit(s) encontrado(s)")
            return True
        else:
            print("   [WARNING] No hay commits")
            print("   Ejecuta: git commit -m 'Initial commit'")
            return False

    except Exception as e:
        print(f"   [WARNING] No se pudo verificar commits: {e}")
        return False

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if not check_git_status():
        return

    checks = [
        check_gitignore(),
        check_sensitive_files(),
        check_config_example(),
        check_readme(),
        check_license(),
        check_requirements(),
        check_commits()
    ]

    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)

    passed = sum(checks)
    total = len(checks)

    print(f"\nVerificaciones pasadas: {passed}/{total}")

    if passed == total:
        print("\n[OK] El repositorio está LISTO para GitHub!")
        print("\nProximos pasos:")
        print("1. Crea un repositorio en GitHub")
        print("2. git remote add origin https://github.com/TU-USUARIO/cdp-tools.git")
        print("3. git branch -M main")
        print("4. git push -u origin main")
    else:
        print("\n[WARNING] Hay verificaciones que fallaron")
        print("Revisa los mensajes arriba y corrige los problemas")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
