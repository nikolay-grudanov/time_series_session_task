# Документация по логированию и хранению данных

## Обзор

Система логирования бота реализует комплексный подход к мониторингу и хранению данных:

1. **Ротационное логирование** — автоматическая ротация файлов логов по времени
2. **CSV-логирование** — структурированное хранение сессий пользователей
3. TXT-логирование — человекочитаемый формат для быстрого анализа

## Структура директорий

```
logs/
├── requests.log          # Основной файл логов с ротацией
├── user_sessions.csv     # Сессии пользователей (CSV)
├── user_sessions.txt     # Сессии пользователей (TXT)
└── example.log           # Пример конфигурации логирования

data/
├── raw/                  # Необработанные исторические данные (CSV)
├── processed/            # Обработанные данные для обучения
└── models/               # Сохраненные обученные модели

cache/
└── models/               # Кэш моделей (при использовании ModelEvaluationService)
```

## 1. Ротационное логирование (requests.log)

### Описание

Файл `requests.log` содержит все запросы пользователей и системные события с автоматической ротацией:

- **Ротация**: ежедневно в полночь
- **Хранение**: 365 дней (настраивается)
- **Формат**: `%(asctime)s - %(levelname)s - %(message)s`

### Пример содержимого

```
2026-01-15 06:15:52,541 - request_logger - ERROR - user_id=156526102 | ticker=AAPL | error=cannot unpack non-iterable ValidationResult object
2026-01-15 06:15:52,541 - aiogram.event - INFO - Update id=47478912 is handled. Duration 73 ms by bot id=8587584103
```

### Уровни логирования

| Уровень | Описание | Пример |
|---------|----------|--------|
| `DEBUG` | Отладочная информация | Подготовка данных, параметры функций |
| `INFO` | Общая информация | Получен запрос, завершена обработка |
| `WARNING` | Предупреждения | Невалидный ввод, незначительные проблемы |
| `ERROR` | Ошибки | Сбои в обработке, проблемы с API |
| `CRITICAL` | Критические ошибки | Системные сбои |

## 2. CSV-логирование (user_sessions.csv)

### Описание

Файл `user_sessions.csv` хранит структурированные данные о сессиях пользователей в соответствии с требованием FR-016.

### Заголовок CSV

```csv
user_id,timestamp,ticker,investment_amount,best_model_name,metric_value,estimated_profit
```

### Поля

| Поле | Тип | Описание |
|------|-----|----------|
| `user_id` | int | Уникальный идентификатор пользователя Telegram |
| `timestamp` | datetime | ISO 8601 timestamp запроса |
| `ticker` | str | Символ тикера акции (AAPL, GOOGL, etc.) |
| `investment_amount` | float | Сумма инвестиций в USD |
| `best_model_name` | str | Название лучшей модели (ETS, ARIMA, LSTM, etc.) |
| `metric_value` | float | Основная метрика (MAPE или RMSE) |
| `estimated_profit` | float | Расчетная прибыль/убыток |

### Пример содержимого

```csv
user_id,timestamp,ticker,investment_amount,best_model_name,metric_value,estimated_profit
12345,2026-01-15T10:30:00,AAPL,1000.0,ETS,1.6549,51.36
12345,2026-01-15T10:35:00,V,500.0,LSTM,2.1234,25.50
67890,2026-01-15T11:00:00,GOOGL,2500.0,ARIMA,0.9876,125.75
```

### Преимущества CSV-формата

- **Структурированность**: легко импортировать в pandas, Excel, базы данных
- **Аналитика**: возможность построения отчетов и статистики
- **Машинное обучение**: использование данных для анализа паттернов

## 3. TXT-логирование (user_sessions.txt)

### Описание

Файл `user_sessions.txt` хранит сессии в человекочитаемом формате для быстрого просмотра и отладки.

### Формат

```
user_id | datetime | ticker | amount | model | metric | profit
```

### Пример содержимого

```
# User Session Log
# Format: user_id | datetime | ticker | amount | model | metric | profit
# Example: 12345 | 2026-01-15 10:30:00 | AAPL | 1000.0 | LSTM | 2.5 | 150.0

12345 | 2026-01-15T10:30:00 | AAPL | 1000.0 | ETS | 1.6549 | 51.36
12345 | 2026-01-15T10:35:00 | V | 500.0 | LSTM | 2.1234 | 25.50
67890 | 2026-01-15T11:00:00 | GOOGL | 2500.0 | ARIMA | 0.9876 | 125.75
```

## 4. Логирование обучения моделей

### Описание

При обучении моделей логируется информация о:

- Времени обучения
- Используемой модели
- Метриках качества
- Статусе (успех/ошибка)

### Формат лога обучения

```
ticker=AAPL | model=LSTM | training_time=45.23s | status=SUCCESS | metrics={'rmse': 0.1815, 'mape': 2.5, 'mae': 0.1633}
```

## API LoggerService

### Основные методы

#### log_request()

Логирование запроса пользователя:

```python
logger_service.log_request(
    user_id=12345,
    ticker="AAPL",
    investment_amount=1000.0,
    selected_model="ETS",
    metrics={"rmse": 3.77, "mape": 1.65, "mae": 3.09},
    profit_estimate=51.36,
    additional_params={"volatility": "normal"}
)
```

#### log_error()

Логирование ошибки:

```python
logger_service.log_error(
    user_id=12345,
    ticker="AAPL",
    error_message="Failed to download historical data"
)
```

#### log_model_training()

Логирование обучения модели:

```python
logger_service.log_model_training(
    ticker="AAPL",
    model_name="LSTM",
    training_time=45.23,
    success=True,
    metrics={"rmse": 0.1815, "mape": 2.5, "mae": 0.1633}
)
```

#### get_session_stats()

Получение статистики по сессиям:

```python
stats = logger_service.get_session_stats()
# {
#     "total_sessions": 150,
#     "unique_users": 25,
#     "unique_tickers": 10,
#     "avg_investment": 1250.0
# }
```

#### get_session_logs()

Получение логов сессий с фильтрацией:

```python
logs = logger_service.get_session_logs(
    user_id=12345,
    ticker="AAPL",
    limit=50
)
```

## Конфигурация

### Параметры инициализации

```python
LoggerService(
    log_file_path="logs/requests.log",      # Путь к основному логу
    csv_log_path="logs/user_sessions.csv",  # Путь к CSV
    txt_log_path="logs/user_sessions.txt",  # Путь к TXT
    retention_days=365                       # Количество дней хранения
)
```

### Настройка через settings.py

```python
# src/config/settings.py

# Основной файл логов
REQUEST_LOG_FILE = "logs/requests.log"

# CSV для сессий пользователей (FR-016)
USER_SESSIONS_CSV = "logs/user_sessions.csv"

# TXT для сессий пользователей
USER_SESSIONS_TXT = "logs/user_sessions.txt"

# Период хранения логов (дней)
LOG_RETENTION_DAYS = 365
```

## Пример анализа данных

### Чтение CSV в Python

```python
import pandas as pd

# Загрузка данных сессий
df = pd.read_csv("logs/user_sessions.csv")

# Статистика по моделям
print(df.groupby("best_model_name")["estimated_profit"].mean())

# Топ тикеров
print(df["ticker"].value_counts().head(10))

# Средняя инвестиция
print(df["investment_amount"].mean())
```

### Анализ в Excel

CSV-файл можно открыть в Excel для:

- Создания сводных таблиц
- Построения графиков
- Форматирования отчетов

## Безопасность и конфиденциальность

### Рекомендации

1. **Права доступа**: ограничить доступ к директории `logs/`
2. **Ротация**: автоматическая очистка старых файлов
3. **Мониторинг**: регулярный анализ логов на предмет аномалий
4. **Резервное копирование**: периодическое копирование CSV на внешние носители

### Поля, требующие внимания

| Поле | Риск | Мера защиты |
|------|------|-------------|
| `user_id` | Утечка персональных данных | Анонимизация при публикации |
| `investment_amount` | Финансовая информация | Контроль доступа |
| `estimated_profit` | Финансовая информация | Контроль доступа |

## Устранение неполадок

### Файл логов не создается

1. Проверьте права доступа к директории `logs/`
2. Убедитесь, что директория существует: `mkdir -p logs`
3. Проверьте конфигурацию в `settings.py`

### CSV-файл пустой

1. Проверьте, что `LoggerService` инициализирован с `csv_log_path`
2. Убедитесь, что метод `log_request()` вызывается
3. Проверьте права на запись в файл

### Логи не ротируются

1. Проверьте настройки `TimedRotatingFileHandler`
2. Убедитесь, что приложение запущено с правами на запись
3. Проверьте свободное место на диске

## Интеграция с внешними системами

### ELK Stack (Elasticsearch, Logstash, Kibana)

```python
# Отправка логов в Logstash
import logging
from logging.handlers import HTTPHandler

handler = HTTPHandler(host="localhost:5044", url="/", method="POST")
logger = logging.getLogger("request_logger")
logger.addHandler(handler)
```

### Prometheus/Grafana

```python
# Метрики для Prometheus
from prometheus_client import Counter, Histogram

REQUEST_COUNTER = Counter("stock_bot_requests_total", "Total requests")
PROFIT_HISTOGRAM = Histogram("stock_bot_profit", "Profit distribution")
```

## Ссылки

- [Документация Python logging](https://docs.python.org/3/library/logging.html)
- [Руководство по настройке](docs/setup-and-usage.md)
- [Документация API](docs/api.md)
