# Arcana Bot

Telegram бот для гаданий на картах Таро с использованием ИИ.

## Запуск через Docker Compose

1. Скопируйте `.env.example` в `.env` и заполните переменные:
```bash
cp .env.example .env
```

2. Запустите проект:
```bash
docker-compose up -d
```

3. Остановите проект:
```bash
docker-compose down
```

## Управление базой данных

### Локальная разработка:
```bash
# Инициализация БД
python db_manager.py init

# Создание миграции
python db_manager.py migrate "описание изменений"

# Применение миграций
python db_manager.py upgrade

# Сброс БД
python db_manager.py reset
```

### Docker:
```bash
# Инициализация БД в контейнере
docker-compose exec bot python db_manager.py init

# Создание миграции
docker-compose exec bot python db_manager.py migrate "описание"

# Применение миграций
docker-compose exec bot python db_manager.py upgrade
```

## Структура проекта

```
├── core/                   # Ядро системы
│   ├── bot.py             # Конфигурация бота
│   ├── logger.py          # Логирование
│   └── database.py        # Подключение к БД
├── db/                    # База данных
│   └── models.py          # Модели данных
├── handlers/              # Обработчики
│   ├── start_handler.py
│   ├── message_handler.py
│   └── callback_handler.py
├── utils/                 # Утилиты
│   └── helpers.py
├── main.py               # Точка входа
├── config.py             # Конфигурация
├── container.py          # DI контейнер
├── services.py           # Бизнес логика
├── db_manager.py         # Управление БД
├── postgresql_repository.py # Репозиторий
├── cache.py              # Кэширование
├── rate_limiter.py       # Ограничение запросов
├── validators.py         # Валидация
├── interfaces.py         # Интерфейсы
├── messages.py           # Константы сообщений
├── docker-compose.yml    # Docker Compose
├── Dockerfile           # Docker образ
├── init_db.sql          # Инициализация БД
├── alembic.ini          # Конфигурация миграций
└── README.md            # Документация
```

## Переменные окружения

- `BOT_TOKEN` - Токен Telegram бота
- `SECRET_KEY` - Секретный ключ
- `DATABASE_URL` - URL базы данных PostgreSQL
- `REDIS_URL` - URL Redis сервера
- `WEBAPP_URL` - URL веб-приложения
- `DEFAULT_BALANCE` - Начальный баланс сообщений
- `REFERRAL_BONUS` - Бонус за реферала
- `LOG_LEVEL` - Уровень логирования
