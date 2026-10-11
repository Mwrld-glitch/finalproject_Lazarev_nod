"""Проверка Parser Service."""

from valutatrade_hub.parser_service.updater import RatesUpdater

result = RatesUpdater().run_update()
print("Получено курсов:", len(result))
for pair, rate in result.items():
    print(f"  {pair}: {rate}")
