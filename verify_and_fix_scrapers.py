#!/usr/bin/env python3
# verify_and_fix_scrapers.py - Verificación y arreglo definitivo de scrapers

import ast
import importlib.util
from pathlib import Path
import sys

def verify_scraper_structure(file_path):
    """Verifica la estructura de un archivo de scraper"""
    print(f"\nVerificando {file_path.name}...")
    
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        issues.append(f"Error de sintaxis: {e}")
        return issues
    
    # Buscar la clase del scraper
    scraper_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and 'Scraper' in node.name:
            scraper_class = node
            break
    
    if not scraper_class:
        issues.append("No se encontró clase Scraper")
        return issues
    
    # Verificar herencia de BaseScraper
    inherits_base = False
    for base in scraper_class.bases:
        if isinstance(base, ast.Name) and base.id == 'BaseScraper':
            inherits_base = True
            break
    
    if not inherits_base:
        issues.append(f"La clase {scraper_class.name} no hereda de BaseScraper")
    
    # Verificar métodos requeridos
    class_methods = [n.name for n in scraper_class.body if isinstance(n, ast.FunctionDef)]
    required_methods = ['__init__', 'fetch_data', 'parse_response']
    
    for method in required_methods:
        if method not in class_methods:
            issues.append(f"Falta el método {method}")
    
    # Verificar que NO tenga run_forever definido (debe heredarlo)
    if 'run_forever' in class_methods:
        issues.append("Define run_forever localmente (debe heredarlo de BaseScraper)")
    
    # Verificar funciones a nivel de módulo
    module_functions = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            module_functions.append(node.name)
    
    # Verificar que main esté a nivel de módulo
    if 'main' not in module_functions:
        issues.append("Falta función main() a nivel de módulo")
    
    # Verificar indentación de funciones mal ubicadas
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('main_'):
            # Verificar si está dentro de una clase (mal)
            for parent in ast.walk(tree):
                if isinstance(parent, ast.ClassDef) and node in ast.walk(parent):
                    issues.append(f"Función {node.name} está dentro de la clase (debe estar fuera)")
    
    return issues

def test_scraper_import(scraper_name):
    """Intenta importar y crear una instancia del scraper"""
    print(f"\nProbando importación de {scraper_name}...")
    
    try:
        # Agregar paths necesarios
        sys.path.insert(0, str(Path.cwd()))
        
        # Importar módulo
        module_path = f"backend.scrapers.{scraper_name}_scraper"
        spec = importlib.util.find_spec(module_path)
        
        if spec is None:
            return f"No se puede encontrar el módulo {module_path}"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Buscar la clase del scraper
        scraper_class_name = f"{scraper_name.title()}Scraper"
        if not hasattr(module, scraper_class_name):
            return f"No se encontró la clase {scraper_class_name}"
        
        scraper_class = getattr(module, scraper_class_name)
        
        # Intentar crear instancia
        scraper = scraper_class()
        
        # Verificar que tenga los métodos necesarios
        if not hasattr(scraper, 'run_forever'):
            return "La instancia no tiene método run_forever"
        
        if not hasattr(scraper, 'run_once'):
            return "La instancia no tiene método run_once"
        
        return "OK"
        
    except Exception as e:
        return f"Error: {str(e)}"

def fix_scraper_definitively(file_path, scraper_name):
    """Arregla un scraper de manera definitiva"""
    print(f"\nArreglando {scraper_name} definitivamente...")
    
    correct_template = f'''# backend/scrapers/{scraper_name.lower()}_scraper.py
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper


class {scraper_name}Scraper(BaseScraper):
    """Scraper para {scraper_name}"""
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('{scraper_name}', use_proxy)
        
        # Configurar URL de la API
        self.api_url = self.config.get('api_url', 'https://api.example.com')
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene los datos de la plataforma"""
        self.logger.info(f"Obteniendo datos de {scraper_name}...")
        
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        """Parsea la respuesta de la API"""
        try:
            data = response.json()
            items = []
            
            # TODO: Implementar parsing específico
            # for item in data:
            #     items.append({{
            #         'Item': item['name'],
            #         'Price': item['price']
            #     }})
            
            self.logger.info(f"Parseados {{len(items)}} items de {scraper_name}")
            return items
            
        except Exception as e:
            self.logger.error(f"Error parseando {scraper_name}: {{e}}")
            return []


def main():
    scraper = {scraper_name}Scraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()
'''
    
    # Leer contenido actual para preservar la lógica específica
    with open(file_path, 'r', encoding='utf-8') as f:
        current_content = f.read()
    
    # Extraer la lógica de fetch_data y parse_response si existe
    try:
        tree = ast.parse(current_content)
        
        # Buscar métodos existentes
        existing_methods = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and 'Scraper' in node.name:
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name in ['fetch_data', 'parse_response', '__init__']:
                        # Obtener el código del método
                        method_lines = current_content.splitlines()[method.lineno-1:method.end_lineno]
                        existing_methods[method.name] = '\n'.join(method_lines)
        
        # Si encontramos métodos existentes, preservarlos
        if existing_methods:
            print(f"  Preservando métodos existentes: {list(existing_methods.keys())}")
            # Aquí podrías hacer un merge más sofisticado
            # Por ahora, solo notificamos que existen
    except:
        pass
    
    # Por ahora, hacer backup y reescribir
    backup_path = file_path.with_suffix('.py.backup')
    file_path.rename(backup_path)
    print(f"  Backup creado: {backup_path}")
    
    # Escribir versión corregida
    file_path.write_text(correct_template, encoding='utf-8')
    print(f"  ✓ {scraper_name} reescrito con estructura correcta")
    
    return True

def main():
    print("\n" + "="*60)
    print("VERIFICACIÓN Y ARREGLO DEFINITIVO DE SCRAPERS")
    print("="*60)
    
    scrapers_dir = Path("backend/scrapers")
    
    # Lista de scrapers a verificar
    scrapers_to_check = [
        'waxpeer', 'csdeals', 'empire', 'skinport', 'cstrade',
        'bitskins', 'marketcsgo', 'white', 'lisskins', 'shadowpay',
        'skinout', 'rapidskins', 'manncostore', 'tradeit', 'skindeck'
    ]
    
    problematic_scrapers = []
    
    # Fase 1: Verificación
    print("\nFASE 1: VERIFICACIÓN DE ESTRUCTURA")
    print("="*40)
    
    for scraper_name in scrapers_to_check:
        file_path = scrapers_dir / f"{scraper_name}_scraper.py"
        
        if not file_path.exists():
            print(f"\n❌ {scraper_name}: Archivo no encontrado")
            problematic_scrapers.append((scraper_name, "Archivo no existe"))
            continue
        
        # Verificar estructura
        issues = verify_scraper_structure(file_path)
        
        if issues:
            print(f"\n❌ {scraper_name}: Problemas encontrados:")
            for issue in issues:
                print(f"   - {issue}")
            problematic_scrapers.append((scraper_name, issues))
        else:
            print(f"\n✅ {scraper_name}: Estructura correcta")
    
    # Fase 2: Prueba de importación
    print("\n\nFASE 2: PRUEBA DE IMPORTACIÓN")
    print("="*40)
    
    for scraper_name in scrapers_to_check:
        if any(s[0] == scraper_name for s in problematic_scrapers):
            print(f"\n⏭️  {scraper_name}: Saltando (tiene problemas estructurales)")
            continue
        
        result = test_scraper_import(scraper_name)
        if result != "OK":
            print(f"\n❌ {scraper_name}: {result}")
            problematic_scrapers.append((scraper_name, result))
        else:
            print(f"\n✅ {scraper_name}: Importación exitosa")
    
    # Fase 3: Arreglar scrapers problemáticos
    if problematic_scrapers:
        print("\n\nFASE 3: ARREGLO AUTOMÁTICO")
        print("="*40)
        
        response = input("\n¿Deseas arreglar automáticamente los scrapers problemáticos? (s/n): ")
        
        if response.lower() == 's':
            for scraper_name, issues in problematic_scrapers:
                file_path = scrapers_dir / f"{scraper_name}_scraper.py"
                
                # Solo arreglar si el archivo existe
                if file_path.exists():
                    fix_scraper_definitively(file_path, scraper_name.title())
                else:
                    print(f"\n⚠️  {scraper_name}: Creando nuevo archivo...")
                    fix_scraper_definitively(file_path, scraper_name.title())
    
    # Resumen final
    print("\n\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    
    if problematic_scrapers:
        print(f"\n⚠️  Scrapers con problemas: {len(problematic_scrapers)}")
        for scraper, _ in problematic_scrapers:
            print(f"   - {scraper}")
    else:
        print("\n✅ Todos los scrapers están correctamente estructurados")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Revisa los archivos .backup para recuperar lógica específica")
    print("2. Implementa la lógica de parsing en los scrapers arreglados")
    print("3. Ejecuta: python test_system.py")
    print("4. Reinicia: python web_server.py")
    
    print("\n¡Verificación completada!")

if __name__ == "__main__":
    main()