Telegram Django Bot Bridge
============================

This library provides a Python interface for creating Telegram Bots. This library is created as a decision for
development medшum or big bots (where there a lot of logic) on Python. It standardizes coding approach in the best
practice of the web development.


The library combines `Django <https://www.djangoproject.com/>`_ and `Python-Telegram-Bot <https://python-telegram-bot.org/>`_.
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

You can install via ``pip``:

.. code:: shell

    $ pip install telegram_django_bot


Then you can configurate it in your app:


1. Add "telegram_django_bot" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'telegram_django_bot',
    ]



2. Run ``python manage.py migrate`` to create the telegram_django_bot models (checked that the ``AUTH_USER_MODEL`` selected
in settings).


3. Set:

* ``TELEGRAM_ROOT_UTRLCONF`` -  for use django notation in callback (strongly recommended)
* ``TELEGRAM_TOKEN`` - for adding triggers,
* ``TELEGRAM_TEST_USER_IDS`` - for adding tests for your bot,
* Make sure, that ``LANGUAGE_CODE``, ``LANGUAGE_CODE``, ``USE_I18N`` are also used in the library for language localization.


4. Add ``RouterCallbackMessageCommandHandler`` in handlers for using TELEGRAM_ROOT_UTRLCONF ::

    updater = Updater(bot=TG_DJ_Bot(settings.TELEGRAM_TOKEN))
    updater.dispatcher.add_handler(RouterCallbackMessageCommandHandler())


If you start a new project, you could use `Telegram django bot template <https://github.com/alexanderaleskin/telergam_django_bot_template>`_ with preconfigured settings.


Quick start
------------



The key feature of the lib is ``TelegaViewSet`` - class for manage Django ORM model. It is designed in the
similar way as `Django rest framework Viewset <https://www.django-rest-framework.org/api-guide/viewsets/>`_ is made.
TelegaViewSet provides logic to manage ORM model from Telegram through bot interface. By default, TelegaViewSet has
5 base methods:

* ``create`` - create a new instance of specified ORM model;
* ``change`` - update instance fields of specified ORM model;
* ``show_elem`` - show fields of the instance and buttons with actions of this instance;
* ``show_list`` - show list of model instance (with pagination);
* ``delete`` - delete the instance


So, if, for example, you have a model of some *request* in your project:

.. code:: python

    from django.db import models

    class Request(models.Model):
        text = models.TextField()
        importance_level = models.PositiveSmallIntegerField()  # for example it will be integer field
        project = models.ForeignKey('Project', on_delete=models.CASCADE)
        tags = models.ManyToManyField('Tags')


The next piece of code gives opportunity for full managing (create, update, show, delete) of this model from Telegram:

.. code:: python

    from telegram_django_bot import forms as td_forms
    from telegram_django_bot.td_viewset import TelegaViewSet


    class RequestForm(td_forms.TelegaModelForm):
        class Meta:
            model = Request
            fields = ['text', 'importance_level', 'project', 'tags']


    class RequestViewSet(TelegaViewSet):
        telega_form = RequestForm
        queryset = Request.objects.all()
        viewset_name = 'Request'


If you need, you can add extra actions to RequestViewSet for managing (see details information below) or change existed functions.
There are several parameters and secondary functions in TelegaViewSet for customizing logic if it is necessary.

In this example, ``TelegaModelForm`` was used. TelegaModelForm is a descendant of Django ModelForm. So, you could use
labels, clean and other parameters and functions for manage logic and displaying.


TelegaViewSet is designed to answer next user actions: clicking buttons and sometimes sending messages. The library imposes
`Django URL notation <https://docs.djangoproject.com/en/4.1/topics/http/urls/>`_ for mapping user actions and TelegaViewSet (or usual handlers).
Usually, for correct mapping you just need to set ``TELEGRAM_ROOT_UTRLCONF`` and use ``RouterCallbackMessageCommandHandler`` in
dispatcher as it is mentioned above in the *Install paragraph*.

For correct mapping *RequestViewSet*  you should write in the TELEGRAM_ROOT_UTRLCONF file something like this:

.. code:: python

    from django.urls import re_path
    from .views import RequestViewSet

    urlpatterns = [
        re_path(r"^rv/", RequestViewSet, name='RequestViewSet'),
    ]

From this point, you can use buttons with callback data "rv/<function_code>" for function calling. For example:

* "rv/cr" - RequestViewSet.create method;
* "rv/sl" - RequestViewSet.show_list;

There is next default function mapping in TelegaViewSet:

* "cr" - create;
* "up" - change;
* "de" - delete;
* "se" - show_elem;
* "sl" - show_list;


See this **example** for great understanding.




Deep in details
------------------




TelegaViewSet features
~~~~~~~~~~~~~~~~~~~~~~~~
url attributes

filters, queryset,

permissions.py



Mapping details
~~~~~~~~~~~~~~~~~

telega_resolve
telega_reverse
RouterCallbackMessageCommandHandler


The `telega_resolve` (which is a descendant of Django resolve), makes possible to do this mapping. In general, you do not
need to use this functions, as ``RouterCallbackMessageCommandHandler`` is used it. So, you just need to set
``TELEGRAM_ROOT_UTRLCONF`` with path to file with callback mapping and use ``RouterCallbackMessageCommandHandler`` in
dispatcher as it is outlined above in the Install paragraph in points 3 and 4.


handler_decor
~~~~~~~~~~~~~~~~



Localization
~~~~~~~~~~~~~~~~


telegram_lib_redefinition.py


Extra lib features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


models.py
************


tg_dj_bot.py
***************

Utils
**********

add_log_action
CalendarPagination
UserViewSet



test.py
***********

tasks.py
***********






