#!/usr/bin/env python3
import asyncio
import sys
import subprocess
from sqlalchemy.ext.asyncio import create_async_engine
from core.database import Base
from config import settings
from db import models as _models


async def init_db():
    print("Инициализация базы данных...")
    
    engine = create_async_engine(settings.database.URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("База данных инициализирована!")
    await engine.dispose()


async def reset_db():
    print("Сброс базы данных...")
    
    engine = create_async_engine(settings.database.URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    print("База данных сброшена!")
    await engine.dispose()


def create_migration(message: str):
    print(f"Создание миграции: {message}")
    subprocess.run([
        "alembic", "revision", "--autogenerate", "-m", message
    ])


def upgrade_db():
    print("Применение миграций...")
    subprocess.run(["alembic", "upgrade", "head"])


def downgrade_db():
    print("Откат миграций...")
    subprocess.run(["alembic", "downgrade", "-1"])


def show_migrations():
    print("История миграций:")
    subprocess.run(["alembic", "history"])


async def main():
    if len(sys.argv) < 2:
        print("""
Использование: python db_manager.py [команда]

Команды:
  init        - Инициализация базы данных
  reset       - Сброс базы данных
  migrate     - Создание миграции (требует сообщение)
  upgrade     - Применение миграций
  downgrade   - Откат миграций
  history     - Показать историю миграций
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        await init_db()
    elif command == "reset":
        await reset_db()
    elif command == "migrate":
        if len(sys.argv) < 3:
            print("Укажите сообщение для миграции: python db_manager.py migrate 'описание'")
            return
        message = sys.argv[2]
        create_migration(message)
    elif command == "upgrade":
        upgrade_db()
    elif command == "downgrade":
        downgrade_db()
    elif command == "history":
        show_migrations()
    else:
        print(f"Неизвестная команда: {command}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОперация отменена пользователем")
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
