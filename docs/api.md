# Документация по API

## Обзор

Этот документ описывает внутренний API Telegram-бота для прогнозирования акций, включая основные классы, методы и их использование.

## Основные модули

### 1. Основное приложение (`src/main.py`)

#### Функции
- `main()`: Точка входа для приложения
- `send_welcome(message)`: Обработчик команды /start
- `handle_forecast_request(message)`: Обработчик запросов прогноза

#### Эндпоинты
- `/start`: Приветственное сообщение и инструкции по использованию
- `Message Handler`: Обрабатывает символ тикера и сумму инвестиций

### 2. Конфигурация (`src/config/settings.py`)

#### Переменные
- `TELEGRAM_BOT_TOKEN`: Токен Telegram-бота из окружения
- `REQUEST_LOG_FILE`: Путь к файлу журнала запросов
- `MODEL_TRAINING_TIMEOUT`: Максимальное время для обучения модели (в секундах)
- `FORECAST_DAYS`: Количество дней для прогноза
- `MIN_INVESTMENT_AMOUNT`: Минимально разрешенная инвестиция
- `MAX_INVESTMENT_AMOUNT`: Максимально разрешенная инвестиция
- `HISTORICAL_YEARS`: Количество лет исторических данных для использования

### 3. Модели

#### Нейронные сети (`src/models/neural_networks.py`)

##### Классы
- `LSTMModel`: Модель нейронной сети LSTM
- `GRUModel`: Модель нейронной сети GRU
- `RNNModel`: Модель нейронной сети RNN
- `NeuralNetworkModels`: Класс-обертка для управления моделями нейронных сетей

##### Методы NeuralNetworkModels
- `prepare_data(data, sequence_length)`: Подготавливает данные для обучения нейронной сети
- `train_model(model_name, data, epochs, sequence_length)`: Обучает модель нейронной сети
- `predict(model_name, data, sequence_length, forecast_days)`: Делает прогнозы с использованием обученной модели

#### Статистические модели (`src/models/statistical.py`)

##### Классы
- `StatisticalModels`: Класс-обертка для управления статистическими моделями

##### Методы
- `prepare_prophet_data(data)`: Подготавливает данные в формате, необходимом для Prophet
- `train_arima(data, order)`: Обучает модель ARIMA
- `train_ets(data, error, trend, seasonal)`: Обучает модель ETS
- `train_prophet(data, changepoint_prior_scale, seasonality_prior_scale)`: Обучает модель Prophet
- `train_all_models(data)`: Обучает все статистические модели
- `predict_arima(steps)`: Делает прогнозы с использованием обученной модели ARIMA
- `predict_ets(steps)`: Делает прогнозы с использованием обученной модели ETS
- `predict_prophet(periods, freq)`: Делает прогнозы с использованием обученной модели Prophet

#### Выбор модели (`src/models/model_selector.py`)

##### Классы
- `ModelSelector`: Класс для выбора лучшей модели по эффективности

##### Методы
- `train_all_models(data)`: Обучает все доступные модели и сохраняет их метрики эффективности
- `select_best_model()`: Выбирает лучшую модель на основе метрик эффективности (RMSE, MAE, AUC)
- `predict(forecast_days)`: Делает прогнозы с использованием выбранной лучшей модели
- `get_model_metrics()`: Возвращает метрики эффективности для всех обученных моделей

### 4. Сервисы

#### Загрузчик данных (`src/services/data_loader.py`)

##### Классы
- `DataLoaderService`: Сервис для загрузки исторических данных акций

##### Методы
- `download_historical_data(ticker, period_years)`: Загружает исторические данные акций для заданного тикера
- `get_company_info(ticker)`: Получает информацию о компании для заданного тикера

#### Сервис прогнозирования (`src/services/forecasting.py`)

##### Классы
- `ForecastingService`: Сервис для генерации прогнозов

##### Методы
- `generate_forecast_with_volatility_adjustment(ticker, historical_data)`: Генерирует прогноз с особым подходом для чрезвычайно волатильных акций
- `assess_volatility(historical_data)`: Оценивает волатильность акции на основе исторических данных

#### Сервис торговой стратегии (`src/services/trading_strategy.py`)

##### Классы
- `TradingStrategyService`: Сервис для генерации торговых рекомендаций

##### Методы
- `identify_optimal_trades(forecast_data, historical_data, forecast_dates)`: Определяет оптимальные дни покупки/продажи на основе данных прогноза
- `generate_trading_recommendations(forecast_data, forecast_dates, investment_amount)`: Генерирует комплексные торговые рекомендации
- `calculate_potential_profits(buy_signals, sell_signals, investment_amount)`: Рассчитывает потенциальную прибыль от торговых сигналов

#### Сервис расчета прибыли (`src/services/profit_calculator.py`)

##### Классы
- `ProfitCalculatorService`: Сервис для расчета потенциальной прибыли

##### Методы
- `calculate_profit_from_trades(trade_signals, investment_amount, initial_price)`: Рассчитывает прибыль на основе торговых сигналов и суммы инвестиций
- `calculate_detailed_profit_analysis(buy_signals, sell_signals, investment_amount, initial_price, final_price)`: Выполняет детальный анализ прибыли с учетом как сигналов покупки/продажи, так и стратегии удержания

#### Сервис логирования (`src/services/logger_service.py`)

##### Классы
- `LoggerService`: Сервис для логирования пользовательских запросов

##### Методы
- `log_request(user_id, ticker, investment_amount, selected_model, metrics, profit_estimate, additional_params)`: Логирует пользовательский запрос со всеми ключевыми параметрами
- `log_error(user_id, ticker, error_message)`: Логирует ошибку, возникшую во время обработки запроса
- `log_model_training(ticker, model_name, training_time, success)`: Логирует информацию об обучении модели

#### Сервис оценки моделей (`src/services/model_evaluation.py`)

##### Классы
- `ModelEvaluationService`: Сервис для оценки эффективности моделей и хранения метрик

##### Методы
- `store_model_performance(ticker, model_name, metrics, training_time, data_size, notes)`: Сохраняет метрики эффективности модели в CSV-файл для сравнения и анализа
- `get_model_comparison(ticker)`: Получает метрики эффективности модели для сравнения
- `get_best_model_by_metric(ticker, metric)`: Получает лучшую модель для тикера на основе определенной метрики
- `get_overall_best_model(ticker)`: Получает лучшую модель для тикера на основе композитного скоринга
- `generate_performance_report(ticker)`: Генерирует отчет об эффективности, сравнивая все модели
- `evaluate_predictions(actual, predicted)`: Оценивает прогнозы по сравнению с фактическими значениями с использованием нескольких метрик

### 5. Утилиты

#### Валидаторы (`src/utils/validators.py`)

##### Функции
- `validate_ticker(ticker)`: Проверяет символ тикера на основе формата фондовой биржи
- `validate_investment_amount(amount)`: Проверяет, что сумма инвестиций находится в допустимом диапазоне
- `validate_stock_volatility(daily_returns)`: Проверяет, является ли акция чрезвычайно волатильной (>5% ежедневной дисперсии)

#### Вспомогательные функции (`src/utils/helpers.py`)

##### Функции
- `setup_logging(log_file, level)`: Настраивает базовую конфигурацию логирования
- `get_current_timestamp()`: Возвращает текущую метку времени в формате YYYY-MM-DD HH:MM:SS
- `dict_to_str(data, separator)`: Преобразует словарь в строковое представление
- `calculate_percentage_change(start_value, end_value)`: Рассчитывает процентное изменение между двумя значениями
- `round_if_number(value, decimals)`: Округляет значение до указанного количества знаков после запятой, если это число

#### Визуализатор (`src/utils/visualizer.py`)

##### Функции
- `create_forecast_visualization(historical_data, forecast_data, confidence_intervals, title)`: Создает визуализацию исторических и прогнозируемых цен акций с доверительными интервалами
- `calculate_confidence_intervals(forecast_data, historical_data, confidence_level)`: Рассчитывает доверительные интервалы для прогноза на основе исторической волатильности
- `create_interactive_forecast_plot(historical_data, forecast_data, confidence_intervals, title)`: Создает интерактивный график прогноза с использованием matplotlib
- `save_forecast_plot(historical_data, forecast_data, filename, confidence_intervals, title)`: Сохраняет визуализацию прогноза в файл

## Модели данных

### Валидация ввода
- Символы тикеров: 1-5 заглавных букв (например, AAPL, GOOGL, TSLA, BRK.B)
- Суммы инвестиций: От $1 до $1,000,000
- Исторические данные: Pandas Series с индексом DateTime

### Формат вывода
- Результаты прогноза: Словарь, содержащий данные прогноза, даты, доверительные интервалы, метрики и т.д.
- Торговые рекомендации: Словарь с сигналами покупки/продажи и сводкой стратегии
- Расчеты прибыли: Словарь с потенциальной прибылью, ROI и анализом

## Обработка ошибок

### Распространенные исключения
- `ValueError`: Неверные параметры ввода
- `TimeoutError`: Обучение модели превысило лимит времени
- `ConnectionError`: Не удалось загрузить исторические данные
- `ModelTrainingError`: Ошибка во время обучения модели

### Формат ответа об ошибках
Ошибки регистрируются и передаются пользователям через Telegram-бота с соответствующими сообщениями об ошибках.

## Конфигурация

### Переменные окружения
- `TELEGRAM_BOT_TOKEN`: Требуется для работы бота

### Файлы конфигурации
- `src/config/settings.py`: Содержит все настраиваемые параметры

## Логирование

### Уровни логирования
- `INFO`: Общая информация об операциях
- `WARNING`: Некритичные проблемы
- `ERROR`: Ошибки, влияющие на функциональность
- `CRITICAL`: Критические ошибки, влияющие на работу системы

### Местоположение логов
- `logs/requests.log`: Журналы пользовательских запросов с настраиваемой ротацией