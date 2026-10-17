# ValutaTrade Hub

Консольное приложение для симуляции торговли валютами: регистрация
пользователей, виртуальные кошельки (фиатные и крипто-валюты), покупка и
продажа по актуальным курсам, просмотр портфеля и кэша курсов.

## Структура проекта

finalproject_<фамилия>_<группа>/
  data/
    users.json              # пользователи
    portfolios.json         # портфели и кошельки
    rates.json              # кэш актуальных курсов (снимок)
    exchange_rates.json     # история всех измерений
  valutatrade_hub/
    __init__.py
    logging_config.py       # настройка логов и ротации
    decorators.py           # @log_action
    core/
      __init__.py
      currencies.py         # Currency, FiatCurrency, CryptoCurrency, реестр
      exceptions.py         # доменные исключения
      models.py             # User, Wallet, Portfolio
      usecases.py           # бизнес-логика
      utils.py              # валидации и конвертации
    infra/
      __init__.py
      settings.py           # Singleton SettingsLoader
      database.py           # Singleton DatabaseManager (JSON)
    parser_service/
      __init__.py
      config.py             # ParserConfig
      api_clients.py        # CoinGeckoClient, ExchangeRateApiClient
      updater.py            # RatesUpdater
      storage.py            # запись rates.json и exchange_rates.json
      scheduler.py          # периодическое обновление (опционально)
    cli/
      __init__.py
      interface.py          # команды CLI
  main.py
  pyproject.toml
  uv.lock
  README.md
  .gitignore

## Установка

  uv sync

## Запуск

  uv run valutatrade

Появится приглашение ">". Введите команду или exit для выхода.

## Команды CLI

Регистрация и вход:

  register --username alice --password 1234
  login --username alice --password 1234

Портфель:

  show-portfolio
  show-portfolio --base EUR

Выводит все кошельки, стоимость каждого в базовой валюте и итог.

Покупка и продажа:

  buy --currency BTC --amount 0.05
  sell --currency BTC --amount 0.01

Покупка создаёт кошелёк автоматически, если его ещё нет. Продажа требует
достаточного баланса.

Курсы:

  get-rate --from USD --to BTC
  show-rates
  show-rates --top 2
  show-rates --currency RUB

get-rate возвращает прямой и обратный курс с меткой времени.
show-rates показывает содержимое кэша.

Parser Service:

  update-rates
  update-rates --source coingecko

update-rates опрашивает внешние API, объединяет курсы и обновляет
data/rates.json и data/exchange_rates.json. При частичном сбое одного
источника обновление продолжается по данным других.

## Кэш курсов и TTL

Время жизни кэша задаётся в SettingsLoader параметром RATES_TTL_SECONDS
(по умолчанию 300 секунд). Если кэш старше TTL, get-rate пытается обновить
его через Parser Service. Если обновление не удалось — выбрасывается
ApiRequestError с предложением повторить позже или выполнить update-rates.

data/exchange_rates.json — история всех измерений (не перезаписывается,
только дополняется новыми записями; дубли по id отсекаются).

## Модель операций (упрощённая)

В проекте выбрана упрощённая модель buy/sell:

- buy увеличивает баланс покупаемой валюты и выводит оценочную
  стоимость покупки в USD;
- sell уменьшает баланс продаваемой валюты и выводит оценочную
  выручку в USD.

Списание с USD-кошелька при покупке и начисление на USD-кошелёк при продаже
НЕ выполняются — стартового баланса и команды пополнения в проекте нет.
USD участвует только в расчётах для отчёта.

## Настройка Parser Service и где хранить ключ

Parser Service обращается к двум API:

- CoinGecko — криптовалюты (BTC, ETH, SOL), ключ не нужен;
- ExchangeRate-API — фиатные валюты (EUR, GBP, RUB), нужен бесплатный ключ:
  https://www.exchangerate-api.com/

Ключ НЕ хранится в коде. Он читается из переменной окружения
EXCHANGERATE_API_KEY.

Задайте её в текущей сессии терминала:

  export EXCHANGERATE_API_KEY=ваш_ключ

Чтобы ключ был доступен всегда, добавьте строку в ~/.bashrc:

  echo 'export EXCHANGERATE_API_KEY=ваш_ключ' >> ~/.bashrc
  source ~/.bashrc

После этого команда update-rates загружает и крипто-, и фиатные курсы.

## Логирование

- logs/actions.log — операции пользователя (REGISTER, LOGIN, BUY, SELL,
  GET_RATE) через декоратор @log_action.
- logs/parser.log — работа Parser Service: старт обновления, успех/ошибка
  по каждому источнику, сохранение.

Ротация: 1 МБ, 3 архивных файла.

При выполнении update-rates логи Parser Service дополнительно выводятся в
консоль. В остальных командах — только в файл.

## Демо

Запись работы CLI: https://asciinema.org/a/UYKy853VWN0GPvUJ
