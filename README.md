# Smart City price_tags

Приложение для выведения цен на led электронных ценниках.
Состоит из административной части и страничка для отображения ценника (полка).

## Технологии

- **Python 3.12** - UI фреймворк
- **PostGre 15** - База данных для хранения конфигурации ценников

## Поддержка браузеров

Приложение поддерживает следующие браузеры и версии:

| Браузер | Минимальная версия | Платформы |
|---------|-------------------|-----------|
| **Chrome** | 100+ | Android TV 12+, Desktop, Mobile |
| **Safari** | 15+ | iOS 15+, macOS 12+ |
| **Firefox** | 100+ | Desktop, Mobile |
| **Edge** | 100+ | Windows, macOS |
| **Samsung Internet** | 15+ | Android |
| **Opera** | 86+ | Desktop, Mobile |

## Установка и запуск административной части

```bash
pip install -r requirements.txt
python3 app.py
```

Running on http://127.0.0.1:5050


## Лицензия

Private Use Only - см. [LICENSE](LICENSE)