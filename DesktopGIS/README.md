# GIS Приложение

Это простое настольное GIS-приложение, созданное на Python и PyQt5. Приложение позволяет пользователям загружать, визуализировать и манипулировать географическими данными, представленными в текстовых файлах. Пользователи могут добавлять точки, линии и полигоны на графическую карту, что делает его полезным инструментом для базовой обработки географических данных.

## Возможности

- Загрузка географических данных из текстовых файлов.
- Визуализация данных в виде точек, линий и полигонов на сетке.
- Удобный интерфейс с возможностью выбора файлов.
- Сохранение изменённых данных обратно в текстовые файлы.
- Поддержка взаимодействия с мышью для навигации и масштабирования карты.

## Требования

Для запуска этого приложения вам потребуются следующие пакеты Python:

- Python 3.12 или выше
- PyQt5
- pytest (для тестирования)
- pytest-qt (для тестирования Qt)

## Установка зависимостей
```bash
poetry install
```

## Запуск приложения
```bash
poetry run python -m src.main
```

## Запуск тестов
```bash
poetry run pytest
```