
import subprocess
import sys

from typing import Dict, Any
from alembic.config import Config
from alembic import command


from pathlib import Path

def get_alembic_config():
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent  # auth_pro/
    
    alembic_ini_path = project_root / "alembic.ini"
    
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"Alembic config not found at: {alembic_ini_path}")
    
    return Config(str(alembic_ini_path))

def migrate():
    """Применяет все миграции"""
    config = get_alembic_config()
    command.upgrade(config, "head")
    return "Migrations applied successfully"

def downgrade(revision: str = "-1"):
    """Откатывает миграцию"""
    config = get_alembic_config()
    command.downgrade(config, revision)
    return f"Downgraded to revision: {revision}"

def revision(message: str):
    """Создает новую миграцию"""
    config = get_alembic_config()
    command.revision(config, message=message, autogenerate=True)
    return f"Revision created with message: '{message}'"

def stamp(revision: str = "head"):
    """Помечает базу данных как обновленную до указанной ревизии"""
    config = get_alembic_config()
    command.stamp(config, revision)
    return f"Database stamped to revision: {revision}"

def get_current() -> Dict[str, Any]:
    """Получить текущую примененную ревизию"""
    try:
        config = get_alembic_config()
        
        # Используем subprocess для получения читаемого вывода
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            cwd=config.get_main_option("here"),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        
        return {
            "success": result.returncode == 0,
            "current": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_history() -> Dict[str, Any]:
    """Получить историю миграций"""
    try:
        config = get_alembic_config()
        
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "history"],
            cwd=config.get_main_option("here"),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }
        
        # Парсим вывод
        migrations = []
        current_section = {}
        
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Определяем ревизию (начинается с хэша)
            if line.startswith('<') and '>' in line:
                if current_section:
                    migrations.append(current_section)
                
                # Извлекаем ревизию
                revision_start = line.find('<') + 1
                revision_end = line.find('>')
                revision = line[revision_start:revision_end]
                
                # Извлекаем сообщение
                message_start = line.find('(', revision_end)
                message_end = line.find(')', message_start)
                message = line[message_start+1:message_end] if message_start != -1 else ""
                
                current_section = {
                    "revision": revision.strip(),
                    "message": message.strip(),
                    "details": []
                }
            elif current_section and line:
                current_section["details"].append(line)
        
        if current_section:
            migrations.append(current_section)
        
        return {
            "success": True,
            "migrations": migrations,
            "count": len(migrations),
            "raw_output": result.stdout.strip()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }