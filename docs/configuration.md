# Руководство по конфигурации

## Обзор

Этот документ объясняет, как настроить Telegram-бота для прогнозирования акций, включая переменные окружения, настройки и возможности настройки.

## Переменные окружения

### Обязательные переменные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота, полученный от BotFather | `123456789:ABCdefGhIjKLMNopQrsTUVwxyZ` |

### Необязательные переменные

| Переменная | Описание | По умолчанию | Пример |
|------------|----------|--------------|--------|
| `MODEL_TRAINING_TIMEOUT` | Максимальное время (в секундах) для обучения модели | `300` | `600` |
| `FORECAST_DAYS` | Количество дней для прогноза | `30` | `60` |
| `MIN_INVESTMENT_AMOUNT` | Минимально разрешенная инвестиция | `1` | `10` |
| `MAX_INVESTMENT_AMOUNT` | Максимально разрешенная инвестиция | `1000000` | `500000` |
| `HISTORICAL_YEARS` | Количество лет исторических данных для использования | `2` | `5` |
| `REQUEST_LOG_FILE` | Путь к файлу журнала запросов | `logs/requests.log` | `logs/bot_requests.log` |

### Создание файла .env

Создайте файл `.env` в корне проекта:

```
TELEGRAM_BOT_TOKEN=ваш_токен_бота_здесь
MODEL_TRAINING_TIMEOUT=300
FORECAST_DAYS=30
MIN_INVESTMENT_AMOUNT=1
MAX_INVESTMENT_AMOUNT=1000000
HISTORICAL_YEARS=2
REQUEST_LOG_FILE=logs/requests.log
```

## Конфигурация настроек

### Расположение

Настройки определены в `src/config/settings.py`:

```python
# Конфигурация Telegram-бота
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Конфигурация данных
DATA_DIR = "data"
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(DATA_DIR, "models")

# Конфигурация логирования
LOGS_DIR = "logs"
REQUEST_LOG_FILE = os.path.join(LOGS_DIR, "requests.log")

# Конфигурация моделей
MODEL_TRAINING_TIMEOUT = 300  # 5 минут в секундах
FORECAST_DAYS = 30
MIN_INVESTMENT_AMOUNT = 1
MAX_INVESTMENT_AMOUNT = 1_000_000

# Конфигурация данных акций
HISTORICAL_YEARS = 2
API_RATE_LIMIT_DELAY = 1  # секунды между вызовами API
```

### Настройка параметров

Чтобы настроить параметры, измените значения в `src/config/settings.py` или переопределите их с помощью переменных окружения.

## Конфигурация моделей

### Нейронные сети

Гиперпараметры нейронной сети можно настроить в `src/models/neural_networks.py`:

```python
# Значения по умолчанию
DEFAULT_INPUT_SIZE = 1
DEFAULT_HIDDEN_SIZE = 50
DEFAULT_NUM_LAYERS = 2
DEFAULT_OUTPUT_SIZE = 1
DEFAULT_EPOCHS = 50
DEFAULT_SEQUENCE_LENGTH = 60
```

### Статистические модели

Параметры статистических моделей можно настроить в `src/models/statistical.py`:

```python
# Значения ARIMA по умолчанию
DEFAULT_ARIMA_ORDER = (1, 1, 1)

# Значения ETS по умолчанию
DEFAULT_ERROR_TYPE = 'add'
DEFAULT_TREND_TYPE = 'add'
DEFAULT_SEASONAL_TYPE = 'add'

# Значения Prophet по умолчанию
DEFAULT_CHANGEPOINT_PRIOR_SCALE = 0.05
DEFAULT_SEASONALITY_PRIOR_SCALE = 10.0
```

## Конфигурация логирования

### Ротация файлов логов

Система использует настраиваемую стратегию ротации логов:

- **Формат лога**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Стратегия ротации**: На основе размера с настраиваемым максимальным количеством байтов
- **Количество резервных копий**: Количество старых файлов логов для хранения
- **Период хранения**: Настроен в параметрах ротации

### Настройка параметров логирования

Измените конфигурацию логирования в `src/utils/logging_config.py`:

```python
def setup_logging_with_rotation(
    log_file: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 МБ
    backup_count: int = 5,
    level: int = logging.INFO
):
```

## Конфигурация данных

### Структура каталогов

Приложение ожидает следующую структуру каталогов данных:

```
data/
├── raw/                    # Необработанные загруженные данные акций (CSV формат)
├── processed/              # Обработанные данные, готовые для обучения моделей (CSV формат)
└── models/                 # Сохраненные обученные модели (если необходимо)
```

### Настройка путей к данным

Измените пути к данным в `src/config/settings.py`:

```python
DATA_DIR = "data"  # Изменить на пользовательский каталог
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(DATA_DIR, "models")
```

## Конфигурация производительности

### Настройки таймаута

Настройте таймауты обучения моделей в `src/config/settings.py`:

```python
MODEL_TRAINING_TIMEOUT = 300  # 5 минут в секундах
```

### Конфигурация прогноза

Настройте параметры прогноза:

```python
FORECAST_DAYS = 30  # Количество дней для прогноза
HISTORICAL_YEARS = 2  # Количество лет исторических данных для использования
```

## Ограничения по вызовам API

### Yahoo Finance API

Система реализует ограничение частоты вызовов Yahoo Finance API:

```python
API_RATE_LIMIT_DELAY = 1  # секунды между вызовами API
```

Увеличьте это значение, если вы сталкиваетесь с проблемами ограничения частоты.

## Пользовательские правила валидации

### Валидация тикеров

Настройте правила валидации тикеров в `src/utils/validators.py`:

```python
def validate_ticker(ticker: str) -> bool:
    # Измените шаблон валидации по мере необходимости
    pattern = r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$'
    return bool(re.match(pattern, ticker.strip()))
```

### Валидация суммы инвестиций

Настройте правила валидации инвестиций в `src/utils/validators.py`:

```python
def validate_investment_amount(amount: Union[int, float, str]) -> tuple[bool, str]:
    try:
        amount = float(amount)
        if amount < MIN_INVESTMENT_AMOUNT:  # Использовать настраиваемое значение
            return False, f"Сумма инвестиций должна быть не менее ${MIN_INVESTMENT_AMOUNT}, получено ${amount}"
        elif amount > MAX_INVESTMENT_AMOUNT:  # Использовать настраиваемое значение
            return False, f"Сумма инвестиций не должна превышать ${MAX_INVESTMENT_AMOUNT}, получено ${amount}"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Неверный формат суммы инвестиций: {amount}"
```

## Пользовательские настройки визуализации

### Конфигурация диаграмм

Измените настройки визуализации в `src/utils/visualizer.py`:

```python
def create_forecast_visualization(
    historical_data: pd.Series,
    forecast_data: np.ndarray,
    confidence_intervals: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    title: str = "Прогноз цены акции"
):
    # Размер диаграммы, цвета и другие визуальные свойства
    fig, ax = plt.subplots(figsize=(12, 6))  # Настроить размер фигуры
```

## Конфигурация сервисов

### Настройки загрузчика данных

Настройте поведение загрузки данных в `src/services/data_loader.py`:

```python
class DataLoaderService:
    def __init__(self):
        self.rate_limit_delay = API_RATE_LIMIT_DELAY  # Настраиваемая задержка
```

### Настройки сервиса прогнозирования

Настройте параметры прогнозирования в `src/services/forecasting.py`:

```python
class ForecastingService:
    def __init__(self, forecast_days: int = 30):  # Настраиваемое количество дней прогноза
        self.forecast_days = forecast_days
```

## Конфигурация оценки моделей

### Хранение метрик

Настройте, где хранятся метрики производительности моделей в `src/services/model_evaluation.py`:

```python
class ModelEvaluationService:
    def __init__(self, metrics_file_path: str = "data/model_performance.csv"):  # Настраиваемый путь
        self.metrics_file_path = metrics_file_path
```

## Конфигурация тестирования

### Настройки тестов

При запуске тестов вы можете использовать разные конфигурации:

```python
# В файлах тестов вы можете временно переопределить настройки
import src.config.settings as settings

# Переопределить настройки для тестирования
settings.MODEL_TRAINING_TIMEOUT = 30  # Более короткий таймаут для тестов
settings.FORECAST_DAYS = 5  # Меньше дней для более быстрых тестов
```

## Конфигурация для продакшена

### Рекомендуемые настройки для продакшена

Для продакшен-развертывания рассмотрите следующие настройки:

```env
MODEL_TRAINING_TIMEOUT=600
FORECAST_DAYS=30
MIN_INVESTMENT_AMOUNT=1
MAX_INVESTMENT_AMOUNT=1000000
HISTORICAL_YEARS=5
REQUEST_LOG_FILE=/var/log/stock-forecast-bot/requests.log
API_RATE_LIMIT_DELAY=2
```

### Рекомендации по безопасности

- Никогда не коммитьте файлы `.env` в систему контроля версий
- Используйте надежные, уникальные токены ботов
- Мониторьте использование API, чтобы оставаться в пределах ограничений
- Регулярно меняйте токены ботов
- Ограничьте доступ к файлам логов

## Устранение неполадок с конфигурацией

### Распространенные проблемы

1. **Бот не запускается**: Проверьте, что `TELEGRAM_BOT_TOKEN` установлен правильно
2. **Таймауты обучения модели**: Увеличьте значение `MODEL_TRAINING_TIMEOUT`
3. **Ограничение частоты**: Увеличьте значение `API_RATE_LIMIT_DELAY`
4. **Проблемы с файлами логов**: Убедитесь, что каталог логов существует и имеет права на запись

### Отладка конфигурации

Для отладки вы можете временно изменить уровень логирования в `src/utils/logging_config.py`:

```python
level: int = logging.DEBUG  # Изменить с INFO на DEBUG для более подробной информации
```