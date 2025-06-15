# fix_database_service.py
from pathlib import Path

def fix_database_service():
    """Arregla el error de run_count en database_service.py"""
    db_service_file = Path("backend/services/database_service.py")
    
    if db_service_file.exists():
        content = db_service_file.read_text(encoding='utf-8')
        
        # Buscar la línea problemática
        old_line = "scraper_status.run_count += 1"
        new_lines = """if scraper_status.run_count is None:
                scraper_status.run_count = 1
            else:
                scraper_status.run_count += 1"""
        
        if old_line in content and "if scraper_status.run_count is None:" not in content:
            content = content.replace(old_line, new_lines)
            db_service_file.write_text(content, encoding='utf-8')
            print("✓ database_service.py arreglado")
        else:
            print("✓ database_service.py ya está arreglado")
    else:
        print("⚠️ No se encontró database_service.py")

if __name__ == "__main__":
    fix_database_service()
