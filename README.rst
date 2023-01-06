Telegram Django Bot Bridge
============================

This library provides a Python interface for creating Telegram Bots. The library combines
`Django <https://www.djangoproject.com/>`_ and `Python-Telegram-Bot <https://python-telegram-bot.org/>`_.
and provides extra powerful utilities based on this libraries.


By simple combining of  `Django <https://www.djangoproject.com/>`_ and `Python-Telegram-Bot <https://python-telegram-bot.org/>`_
you will get next opportunities:

Python-Telegram-Bot:

* Python Interface for communication with Telegram API;
* Web-sevice for get updates from telegram;

Django:

* Django ORM  (communication with Database);
* Administration panel for management.


Telegram Django Bot Bridge provides next special opportunities:

* using Django Forms;
* using Viewsets (typical action with model (create, update, list, delete));
* using Django localization;
* using function routing like urls routing in Django;
* creating tests;
* creating general menu items with no-coding (through Django Admin Panel);
* extra high-level Bot functions, such as wrapper for send delayed (or scheduled) messages;
* collecting stats from user actions in the bot;
* creating user triggers;
* commonly used utilities.




Install
------------

.. code:: shell

    $ pip install telergam_django_bot




Quick start
------------


1. Add "telegram_django_bot" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'telegram_django_bot',
    ]



2. Run ``python manage.py migrate`` to create the polls models.

3. Add TELEGRAM_TOKEN, TELEGRAM_TEST_USER_IDS, TELEGRAM_ROOT_UTRLCONF in settings for full use all library advantages.

