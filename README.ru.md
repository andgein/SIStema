# SIStema

[![Build Status](https://travis-ci.org/andgein/SIStema.svg?branch=master)](https://travis-ci.org/andgein/SIStema)

Веб-сервис для автоматизации организации [ЛКШ](http://lksh.ru). Сейчас он
покрывает вступительную работу и сбор информации о школьниках. В будущем мы
также хотим автоматизировать остальные процессы.

Начните с чтения вики [вики](https://github.com/andgein/SIStema/wiki).

## Установка (Linux)

```bash
    # Склонируйте себе репозиторий
    git clone git@github.com:andgein/SIStema.git
    cd SIStema/

    # Создайте виртуальное окружение с Python >= 3.8
    virtualenv -p python3 venv
    source ./venv/bin/activate

    # Установите зависимости
    # SQLite
    pip install -Ur src/requirements.txt
    # MySQL
    pip install -Ur src/requirements.mysql.txt
    # PostgreSQL
    pip install -Ur src/requirements.postgres.txt
```

## База данных

У нас пока нет тестовой базы данных, но вы можете взяться за эту задачу:
[#109](https://github.com/andgein/SIStema/issues/109) :)

Если вы один из организаторов ЛКШ, вы можете попросить
[Артёма](https://github.com/citxx) или [Андрея](https://github.com/andgein)
сделать вам дамп боевой базы:

```bash
    # Создание дампа
    python src/web/manage.py dumpdata > db.json

    # Загрузка
    python src/web/manage.py migrate
    src/web/manage.py sqlflush | sqlite3 db.sqlite3
    python src/web/manage.py loaddata db.json
```
