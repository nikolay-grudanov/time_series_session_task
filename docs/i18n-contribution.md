# Руководство по вкладу в переводы (i18n)

## Добавление новых переводов

### 1. Добавление нового ключа сообщения

#### Шаг 1: Добавьте ключ в `src/i18n/constants.py`

```python
class MessageKey(str, Enum):
    # Существующие ключи...
    your_new_key = "your_new_key"
```

Правила именования ключей:
- Используйте `snake_case` (строчные буквы с подчёркиваниями)
- Группируйте связанные ключи (например, `forecast_`, `stocks_`, `status_`)
- Используйте префиксы функциональности:
  - `forecast_*` - сообщения прогноза
  - `stocks_*` - сообщения списка акций
  - `status_*` - сообщения статуса модели
  - `error_*` - сообщения об ошибках
  - `help_*` - сообщения справки

#### Шаг 2: Добавьте переводы в locale-файлы

**`locales/ru.json`:**
```json
{
  "your_new_key": "Ваш текст на русском языке",
  ...
}
```

**`locales/en.json`:**
```json
{
  "your_new_key": "Your English text here",
  ...
}
```

#### Шаг 3: Используйте сообщение в коде

```python
from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader

loader = MessageLoader()

# Получение перевода
text = loader.get(MessageKey.your_new_key, language)

# С параметрами
text = loader.get(MessageKey.your_new_key, language, param_name="value")
```

### 2. Параметры в сообщениях

Поддерживается форматирование с параметрами:

```json
{
  "greeting": "Привет, {name}!",
  "forecast_result": "Прогноз для {ticker}: {price:.2f}"
}
```

Использование:
```python
loader.get(MessageKey.greeting, "ru", name="Алексей")
# Результат: "Привет, Алексей!"

loader.get(MessageKey.forecast_result, "ru", ticker="AAPL", price=150.25)
# Результат: "Прогноз для AAPL: 150.25"
```

### 3. Многострочные сообщения

Используйте `\n` для переноса строк:

```json
{
  "help_text": "Строка 1\nСтрока 2\nСтрока 3"
}
```

### 4. Markdown-разметка

Сообщения могут содержать Markdown:

```json
{
  "bold_text": "*Жирный текст*",
  "code_example": "`/forecast AAPL 1000`"
}
```

### 5. Эмодзи

Эмодзи поддерживаются и приветствуются для улучшения UX:

```json
{
  "success": "✅ Операция выполнена успешно",
  "error": "❌ Произошла ошибка",
  "loading": "🔄 Загрузка..."
}
```

## Проверка качества переводов

### Автоматическая проверка

```bash
# Проверка синхронизации ключей
pytest tests/unit/test_i18n.py::TestJsonFileSynchronization -v

# Проверка всех ключей
pytest tests/unit/test_i18n.py::TestMessageLoaderIntegration::test_all_keys_return_valid_messages -v

# Полный набор тестов i18n
pytest tests/unit/test_i18n.py tests/integration/test_language_flow.py -v
```

### Ручная проверка

1. Оба locale-файла должны иметь одинаковый набор ключей
2. Все сообщения должны быть непустыми
3. Сообщения не должны содержать смешение языков (русский + английский в одном сообщении)
4. Параметры `{param}` должны присутствовать во всех языковых версиях

## Структура сообщений по категориям

### Языковой интерфейс
- `welcome` - приветствие при выборе языка
- `select_lang_prompt` - приглашение выбрать язык
- `lang_selected_ru` / `lang_selected_en` - подтверждение выбора
- `settings_title` - заголовок настроек
- `current_lang` - текущий язык

### Ошибки
- `error_generic` - общая ошибка
- `error_invalid_input` - неверный ввод
- `error_invalid_ticker` - неверный тикер
- `error_invalid_amount` - неверная сумма

### Прогноз
- `forecast_downloading` - загрузка данных
- `forecast_generating` - генерация прогноза
- `forecast_result_caption` - заголовок результата
- `forecast_expected_change` - ожидаемое изменение
- `forecast_best_model` - лучшая модель

### Акции
- `stocks_title` - заголовок списка
- `stocks_empty` - список пуст
- `stocks_showing` - информация о странице
- `stocks_tap_to_use` - инструкция по использованию

### Статус модели
- `model_status_title` - заголовок
- `status_scheduler_enabled` - планировщик включен
- `status_retraining_in_progress` - переобучение
- `status_error` - ошибка

## Рекомендации

1. **Краткость**: Сообщения должны быть лаконичными
2. **Ясность**: Избегайте двусмысленности
3. **Консистентность**: Используйте одинаковую терминологию
4. **Полнота**: Все сообщения должны быть переведены на оба языка
5. **Тестирование**: Проверяйте сообщения в контексте использования

## Обратная связь

При проблемах с переводами создавайте issue с пометкой `i18n`.
