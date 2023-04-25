# Telegram Django Bot Template

This template was created to develop Telegram bots based on the library
[Telegram Django Bot](https://github.com/alexanderaleskin/telegram_django_bot_bridge) (Django + python-telegram-bot) which allows you to use
ViewSet and other useful Django tools in bot development.

> This template is designed to use the synchronous version of Python-Telegram-Bot (13.x). You need to make some changes 
> on your own to use 20.x versions.

This template loads everything you need to develop a Telegram bot and use it inside docker
(as well as docker-compose). The template is a bundle:

* PostgreSQL;
* Telegram-Django-Bot:
   * Django:
     * Celery (+ Redis);
   * Python-Telegram-Bot;
* *nginx;
* Docker Compose.

## How to use

To run the bot locally, you need:

1. Create a `.env` file at the root of the project with variables as in the `.env.example` example.
2. Run containers in terminal via [Docker-Compose](https://docs.docker.com/compose/): `docker-compose up`.

After that, the base template (6 containers) will be launched:

1. Bot in Telegram will respond to commands;
2. Django will be launched on port 8001, and the admin panel can be accessed using the following path:
    [http://127.0.0.1:8001/admin/](http://127.0.0.1:8001/admin/)


> An administrator to access the Django panel can be created with the following command in terminal:
> `docker-compose exec web python manage.py createsuperuser`.


Docker-compose files are configured for the development environment, including using `nodemon` in the bot container, which allows
automatically reload the bot when the code changes. When using in production, don't forget to specify `DJANGO_DEBUG=False` in the environment.

When running containers (settings in docker-compose.yml), a `mounts` folder is created in the folder one level up, in which
logs and auxiliary files are stored.

## Details

### Template structure

The template has the following folders and items:

1. `base` - the main directory with business logic of the bot. You could create other Django apps (folders);
2. `bot_conf` - settings for launching Django and Telegram Django Bot bridge;
3. `configs` - files for running docker containers;
4. `locale` - translation for supporting localization;
5. `run_bot.py` - this is the file that starts the bot;
6. `common.yml, docker-compose.yml, docker-entrypoint.sh, Dockerfile` - files for running docker.


### Library tools

For learning Telegram-Django-Bot tools you can look at
[documentation](https://github.com/alexanderaleskin/telegram_django_bot_bridge/blob/master/README.rst) or
see the use of tools on the example of the bot 
[@Disk_Drive_Bot](https://t.me/Disk_Drive_Bot) and its [repository](https://github.com/alexanderaleskin/drive_bot).


### Using docker-compose in production

In production, you can also use docker-compose to deploy the solution.
It's not the best way, but it's quick and easy. To deploy, you need:

1. Have a server with:
   1. docker-compose installed ([Install Docker Engine guide](https://docs.docker.com/engine/install/ubuntu/))
   2. web server to access the admin panel (you can use [Nginx](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04) with [https connection](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04)).
    In the web server you need to forward traffic to port 7501 (`proxy_pass http://127.0.0.1:7501`)

2. Make changes to the configuration files:
    1. comment out the line `- ./:/webapp` in the file `./common.yml`;
    2. specify variables in .env, including don't forget to specify `DJANGO_DEBUG=False`;
    3. Uncomment the nginx service in the docker-compose.yml file on lines 85-94;
3. Download containers or build them on the server, then run: `$ docker-compose up -d`;


### Localization

Localization uses Django tools. In the standard, you need to make small changes to `settings.py`
file (specify languages in `LANGUAGES`) and use 3 commands:

* Create a folder with translations for a specific language: `django-admin makemessages -l <language_code>`
* Update files for translation hints: `$ django-admin makemessages -a`;
* Compile translations: `$ django-admin compilemessages`.


> If you are not setting up a environment outside Docker, then the command must be prefixed with `docker-compose exec web <command-above>`.
 
> Changes in the text translations files do not automatically restart the process, so you need manually restart the process (it is enough to add space in any .py file).

More details in the documentation [Telegram-Django-Bot](https://github.com/alexanderaleskin/telegram_django_bot_bridge#localization) .


