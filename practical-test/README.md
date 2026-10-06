# Практический тест: решения с кодом

| Вопрос | Папка | Что внутри | Запуск |
|---|---|---|---|
| 11 | `q11_tasks_api` | REST API задач (Flask): CRUD, коды ошибок, курсорная пагинация | `python -m unittest` |
| 15 | `q15_form` | Форма даты рождения и email: frontend (`index.html`) и backend-валидация | `python -m unittest` |
| 23 | `q23_frontend_states` | Состояния loading / empty / error / partial / retry, защита от устаревших ответов | открыть `index.html` |
| 25, 30 | `q25_q30_flutter_list` | Flutter-экран списка (контроллер отдельно от UI, отмена запроса) и его тесты | `flutter test` |
| 26 | `q26_registration` | Регистрация: unit + интеграционные тесты, UI-кейсы в `UI_TESTS.md` | `python -m unittest` |
| 27 | `q27_discount` | Скидка от порога: граничные значения, округление | `python -m unittest` |
| 28 | `q28_orders` | POST /orders: остатки, транзакция, идемпотентность, гонки | `python -m unittest` |
| 29 | `q29_auth_regression` | Общая библиотека авторизации, контрактные и регрессионные тесты | `python -m unittest` |

Python 3.10+ и Flask (`pip install flask`). Для Flutter-проекта нужен Flutter SDK 3.10+.
Все Python-тесты можно запустить командой `./run_all.sh`.

Примечание: Flutter-код (25, 30) в среде, где писался проект, не запускался (там нет Flutter SDK),
поэтому перед сдачей выполните `flutter create .` и `flutter test` в папке `q25_q30_flutter_list`.
