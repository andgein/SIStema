SIStema
=======

Web service for easy Summer Informatic School creation

Most relevant issues are [here](https://github.com/andgein/SIStema/milestone/2)

Start from reading [wiki](https://github.com/andgein/SIStema/wiki)

## Install

    $ git clone git@github.com:andgein/SIStema.git
    $ cd SIStema/
    $ virtualenv -p python3 venv
    $ source ./venv/bin/activate
    $ pip install -Ur src/requirements.txt
    
Or (`pip install -Ur src/requirements.mysql.txt` if you want to use MySQL backend)

Ask someone to make you a database dump of the main SIStema instance:

    $ python src/web/manage.py dumpdata --exclude default.usersocialauth > db.json

> If you have django-reversion >= 2.0.0, remove lines containing "object_id_int" or "manager_slug" from the dump.

Then load it locally:

    $ python src/web/manage.py migrate
    $ src/web/manage.py sqlflush | sqlite3 db.sqlite3
    $ python src/web/manage.py loaddata db.json
