Telegram Django Bot Bridge
============================

This library provides a Python interface for creating Telegram Bots. It standardizes coding approach in the best
practice of the web development. The library combines `Django <https://www.djangoproject.com/>`_ and `Python-Telegram-Bot <https://python-telegram-bot.org/>`_.
and provides extra powerful utilities based on this libraries.


Normally, Python-Telegram-Bot gives next opportunities for bot creating:

* Python Interface for communication with Telegram API;
* Web-sevice for get updates from telegram;

and Django:

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
similar way as `Django rest framework Viewset <https://www.django-rest-framework.org/api-guide/viewsets/>`_.
TelegaViewSet provides logic to manage ORM model from Telegram through bot interface. By default, TelegaViewSet has
5 methods:

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


See this **example** for great understanding.




Deep in details
------------------

В этой главе разберем как все работает под капотом. Так как основная задача библиотеки унифицировать написания кода и
предоставить часто используемые функции для бота, то достаточно много логики базируются на ресурсах и парадигмах
Django <https://www.djangoproject.com/>`_  и `Python-Telegram-Bot <https://python-telegram-bot.org/>`_ . Разберем
ключевые моменты библиотеки на примере `Telegram django bot template <https://github.com/alexanderaleskin/telergam_django_bot_template>`_ .


Так как Боты в Телеграме спроектированы как инструмент для ответов на запросы пользователей, то написания бота начинается
с обработчика запросов пользователей. Для этого используются стандартные инструменты библиотеки Python-Telegram-Bot ﹣
``telegram.ext.Update``:

.. code:: python

    from telegram.ext import Updater

    ...

    def main():
        ...

        updater = Updater(bot=TG_DJ_Bot(TELEGRAM_TOKEN))
        add_handlers(updater)
        updater.start_polling()
        updater.idle()

    if __name__ == '__main__':
        main()


Как и указано в примере, для запуска бота (Update) необходимо указать несколько вещей (стандарт библиотеки ``Python-Telegram-Bot``):

1. экземляр модели ``telegram.Bot`` с указанным API токеном. В данном случае, используется потомок класса ``telegram.Bot``
``telegram_django_bot.tg_dj_bot.TG_DJ_Bot``, который имеет дополнительный функционал для удобства (к нему вернемся позже);
2. Обработчики, которые будут вызываться в ответ на запросы пользователей.


В примере перечень обработчиков указывается в функции ``add_handlers``:



.. code:: python

    from telegram_django_bot.routing import RouterCallbackMessageCommandHandler

    ...

    def add_handlers(updater: Updater):
        dp = updater.dispatcher
        dp.add_handler(RouterCallbackMessageCommandHandler())


В примере добавляется 1 супер обработчик ``RouterCallbackMessageCommandHandler``, который позволяет писать обработчики
в стиле обработки запросов ссылок в ``Django``. ``RouterCallbackMessageCommandHandler`` позволяет обрабатывать
сообщения, команды пользоваетелей и нажатия на кнопки пользователями. То есть заменяет собой хендлеры
``MessageHandler, CommandHandler, CallbackQueryHandler`` . Так как библиотека ``Telegram Django Bot Bridge`` является расширением
возможностей, то она не запрещает использовать в качестве обработчиков и стандартные обработчики библиотеки ``Python-Telegram-Bot``
(иногда это просто необходимо, например если нужно обрабатывать ответы на опросы (необходимо использовать PollAnswerHandler)).

`Django нотация <https://docs.djangoproject.com/en/4.1/topics/http/urls/>`_ описания обработчиков заключается в том, что в отдельном файле или файлах описываются пути до обработчиков.
Как и в стандарте ``Django`` в настройках проекта указывается указывается главный файл (корень), где храняться пути до обработчиков или пути к отдельным группам обработчиков.
Для указанания пути к файлу используется атрибут ``TELEGRAM_ROOT_UTRLCONF``. В шаблоне-примере имеем следующие настройки:


``bot_conf.settings.py``:

.. code:: python

    TELEGRAM_ROOT_UTRLCONF = 'bot_conf.utrls'


``bot_conf.utrls.py``:

.. code:: python

    from django.urls import re_path, include

    urlpatterns = [
        re_path('', include(('base.utrls', 'base'), namespace='base')),
    ]


То есть, в файле подключается только 1 группа обработчиков (которая на идейнном уровне соответствует приложению ``base``). Можно
добавлять и несколько групп, такое может быть удобным, если вы создаете несколько папок (приложений) для хранения кода. Как видно из импортов
используется функции ``Django`` без какого либо переопределения.

В самом файле с группой обработчиков ``base.utrls.py`` имеем следующий код:


.. code:: python

    from django.urls import re_path
    from django.conf import settings

    from .views import start, BotMenuElemViewSet, UserViewSet, some_debug_func


    urlpatterns = [
        re_path('start', start, name='start'),
        re_path('main_menu', start, name='start'),

        re_path('sb/', BotMenuElemViewSet, name='BotMenuElemViewSet'),
        re_path('us/', UserViewSet, name='UserViewSet'),
    ]


    if settings.DEBUG:
        urlpatterns += [
            re_path('some_debug_func', some_debug_func, name='some_debug_func'),
        ]

Как видно, здесь указываются уже конечные обработчики, которые описаны в файле ``base.views.py``. Таким образом, если
пользовать в боте пишет команду ``/start``, то ``Updater`` получает сообщение о действии пользователя и из набора своих
обработчиков выбирает подходящий под запрос ``RouterCallbackMessageCommandHandler``, который в свою очередь среди
``utrls`` находит подходящий путь ``'' + 'start'`` и передает управление функции start.

Такое распределение обработчиков позволяет группировать часть обработчиков в модули и достаточно быстро подключать или
изменять их, при это не боятся, что возникнуть путаница какой обработчиков нужно вызвать, как это может быть, если все
обработчики подтягивали в одно место из разных модулей как это требует ``Python-Telegram-Bot``.

В примере, кроме функций обработчиков как ``def start`` и ``def some_debug_func``, также используются ViewSets, которые
являются аггрегаторами нескольких функций. Концепт ViewSets заключается в том, что достаточно часто надо применять
одинаковые операции для набора данных, такие как создать, изменить, показать, удалить набор данных. В библиотеки для
таких целей создан класс ``telegram_django_bot.td_viewset.TelegaViewSet``, который в качестве набора данных использует
Django ORM модель базы данных. ``TelegaViewSet`` имеет 5 функция для управления моделью:



========= ======== ===========================
 Метод     UTRL      Описание
--------- -------- ---------------------------
create     cr       Создание модели
change     up       Изменения атрибутов
delete     de       Удаление модели
show_elem  se       Отображение модели
show_list  sl       Отображение списка моделей
========= ======== ===========================

Таким образом, если мы хотим вызвать метод ``BotMenuElemViewSet.create`` для создания элемента нам необходимо использовать
следующий путь 'sb/cr' ﹣ по первой части пути 'sb/' ``RouterCallbackMessageCommandHandler`` передаст управление
классу ``BotMenuElemViewSet``, а именно методу ``TelegaViewSet.dispatch``, который внутри себя по второй части пути
``cr`` поймет, что нужно вызвать метод ``create``.

Подводя итог по схеме распределения путей для вызова обработчиков, имеем следующее:

1. В качестве приемщика сообщений от Телеграм используется ``telegram.ext.Update``;
2. В качестве обработчиков можно использовать стандартные обработчики библиотеки ``Python-Telegram-Bot``. Для использования
схемы распределения путей Django и удобного использования ``TelegaViewSet`` необходимо использовать ``RouterCallbackMessageCommandHandler``.
3. ``TelegaViewSet`` аггрегирует в себе набор стандартных функций для управления данных, что позволяет сгруппировать код,
связанный с одним типом данных в одном месте.



TelegaViewSet features
~~~~~~~~~~~~~~~~~~~~~~~~

Как раннее упомянуто, TelegaViewSet содержит стандартные функции для управления данных.
За счет таких стандартых методов обработки данных и получается в примере описать логику ``BotMenuElemViewSet`` в 40
строчках кода, при этом еще и использовать некоторую кастомизаются для красивого отображения.


Для использования всех возможностей класса TelegaViewSet необходимо от него наследоваться, как например, это сделано
в шаблоне с BotMenuElemViewSet:


.. code:: python

    from telegram_django_bot.td_viewset import TelegaViewSet

    class BotMenuElemViewSet(TelegaViewSet):


Для того, чтобы кастомизировать ViewSet необходимо указать 3 обязательных атрибута:
1. ``viewset_name``  -  имя класса, используется для отображения пользователям бота
2. ``telega_form``  - форма данных, используется для указания какие поля ORM модели базы данных использовать во viewset;
3. ``queryset`` - базовый запрос для получения элементов модели.

В шаблоне используется следующие значения:

.. code:: python

    from telegram_django_bot import forms as td_forms
    from telegram_django_bot.models import BotMenuElem

    class BotMenuElemForm(td_forms.TelegaModelForm):
        form_name = _("Menu elem")

        class Meta:
            model = BotMenuElem
            fields = ['command', "is_visable", "callbacks_db", "message", "buttons_db"]

    class BotMenuElemViewSet(TelegaViewSet):
        viewset_name = 'BotMenuElem'
        telega_form = BotMenuElemForm
        queryset = BotMenuElem.objects.all()


где ``BotMenuElemForm`` является потомком класса ``Django ModelFrom``, поэтому имеет схожую структуру и способы параметризации.
`` form_name `` -- обозначает название формы и используется в некоторых сообщениях, отправляемих пользователям Телеграмма.



TelegaViewSet имеет достаточно много общего с аналогами Viewset, заточенных под WEB-разработку (например,
`django-rest-framework viewsets <https://www.django-rest-framework.org/api-guide/viewsets/>`_ ). Однако в рамках разработки Телеграм ботов TelegaViewSet
имеет ряд особенностей:

1. Особый способ создания элементов;
2. Отображение информации в ботах ограничен и чаще всего сводиться к отображению текста и кнопок, поэтому viewset
кроме бизнес логики, включает в себя конструирование и стандартных отображения данных;


Формы
************


Так как в Телеграм нет возможностей создать формы (в классическом Веб понимании) и общение между ботом и пользователем происходит в чате, то
наиболее интуитивно понятным решением для заполнения формы (создания элемента) является по элементное заполнение формы,
когда сначала заполняется первый элемент формы, затем второй и тд. При этом в каком-то временном хранилище запоминать
указанные значения, для того, чтобы в конце создать элемент из формы. ``TelegaModelForm`` и ``TelegaForm`` реализованы как раз
таким способом, чтобы взять это процесс на себя. Отличие этих классов от стандартных Django классов заключается именно
в модификации способа заполнения полей формы, в остальном они не отличаются от стандартных форм.

``TelegaModelForm`` и ``TelegaForm`` как потомки Django ``ModelForm`` и ``Form`` имеет следующие параметры, которые
достаточно часто нужно кастомизировать :
1. Функция clean и другие `функции процесса верификации форм <https://docs.djangoproject.com/en/4.1/ref/forms/validation/>`_
2. ``labels`` - название полей;
3. ``forms.HiddenInput`` - обозначение скрытых полей (скрывание полей позволяет их не показывать пользователю,
при этом использовать и настраивать в формах или в ``TelegaViewSet``)



``TelegaViewSet`` рассчитан на взаимодействие с потомками класса ``TelegaModelForm`` и позволяет использовать
генерировать формы как с простыми полями ``CharField, IntegerField`` так и с ``ForeignKey, ManyToManyField``. При этом,
принимая во внимания особенности общения с ботом в Телеграмме, для повышения удобства заполнения форм пользователями
в классе ``TelegaViewSet`` можно использовать словарь ``prechoice_fields_values``, который формирует список часто
используемых значения для определенных полей формы. Это позволяет пользователям выбирать нужные значения из кнопок, а не
вводить текст или значение вручную. В шаблоне есть пример использования этого поля:


.. code:: python

    class BotMenuElemViewSet(TelegaViewSet):
        ...

        prechoice_fields_values = {
            'is_visable': (
                (True, '👁 Visable'),
                (False, '🚫 Disabled'),
            )
        }

В данном, случае для булевского поля ``is_visable`` указаны 2 значения для выбора правда и ложь с указанием как они
отображаются пользователям. Иногда список значений надо формировать динамично, в этом случае можно переопределить
``prechoice_fields_values`` как ``@property`` функцию.


Основная логика TelegaViewSet
************************************************

Основной функций класса, которая по запросу пользователя выбирают функцию для вызова, является ``TelegaViewSet.dispatch``.
Разберем ее логику подробнее:

.. code:: python

    def dispatch(self, bot, update, user):

        self.bot = bot
        self.update = update
        self.user = user

        if update.callback_query:
            utrl = update.callback_query.data
        else:
            utrl = user.current_utrl

        self.utrl = utrl

        if settings.DEBUG:
            logging.info(f'utrl: {utrl}')

        utrl_args = self.get_utrl_params(re.sub(f'^{self.prefix}', '', self.utrl))
        if self.has_permissions(bot, update, user, utrl_args):
            chat_action, chat_action_args = self.viewset_routing[utrl_args[0]](*utrl_args[1:])
        else:
            chat_action = self.CHAT_ACTION_MESSAGE
            message = _('Sorry, you do not have permissions to this action.')
            buttons = []
            chat_action_args = (message, buttons)

        res = self.send_answer(chat_action, chat_action_args, utrl)

        utrl_path = utrl.split(self.ARGS_SEPARATOR_SYMBOL)[0]   # log without params as to much varients
        add_log_action(self.user.id, utrl_path)
        return res


Как и обычный обработчик функция на вход принимает 3 аргумента: bot, update, user. После их сохранения происходит
определение текущего пути. Он определяется либо по нажатию кнопки в боте (значение ``callback_data`` кнопки), либо
может храниться в атрибуте юзера ``user.current_utrl``. Второй вариант возможен, если пользователь вручную заносит
какую-то информацию (например заполнил текстовое поле в форме). После происходит извлечение аргументов из пути
для вызова конкретной функции. Хранение и взаимодействие с аргументами в пути схоже с работой ``sys.argv``. Так,
например строка ``"sl&1&20"`` будет преобразована в список ``['sl', '1', '20']``. Знак разделитель между атрибутами
по умолчанию выбран ``&`` и может быть изменен через переменную ``TelegaViewSet.ARGS_SEPARATOR_SYMBOL`` .

При использовании ``TelegaViewSet`` скорей всего вам не придеться взаимодействовать со строкой аргументов на прямую, так
как  ``dispatch`` преобразует строку в аргументы, а создать строку для ``callback_data`` кнопки c вызовом определенного метода и аргументов стоит исопльзовать
``TelegaViewSet.gm_callback_data``. В случае, если нужно более низкоуровневое взаимодействие с аргументами функций, то
можно воспользоваться функциями ``construct_utrl`` и ``get_utrl_params``.

После получения аргументов utrl_args и проверки прав доступа происходит непосредственно выбор и вызов функции. Первый
аргумент utrl_args является своего рода коротким названием функции. Все последующие аргументы передаются как параметры
в функцию. Внутри функции происходит необходимая бизнес логика и формирование данных для ответа пользователю. На выходе
любая функция должна возвращать тип действия ``chat_action`` и параметры к этому действию ``chat_action_args``. По
умолчани в классе ``TelegaViewSet`` есть только 1 действие ﹣ ``CHAT_ACTION_MESSAGE``, которое обозначает, что пользователю
будет возвращено текстовое сообщение (возможно с кнопками). Аргументами к тему действию являются текст сообщения и список кнопок.


После отработки функции происходит отправка ответа пользователю ``send_answer`` и логгирования действия пользователя.


В качестве метод для вызова в ``viewset_routing`` выступают методы ``create, update, delete, show_elem, show_list``.
Также могут быть добавлены свои методы. Предположим, что хотим добавить метод ``def super_method(self, *args)``, тогда
необходимо в классе добавить следующие строки:

.. code:: python

    class SomeViewSetClass(TelegaViewSet):
        ...

        actions = ['create', 'change', 'delete', 'show_elem', 'show_list', 'super_method']

        command_routing_super_method = 'sm'


        def super_method(self, *args):
            ...


Где actions определяет список доступных методов, а command_routing_<method> определяет путь (url) метода.

Как отмечалось выше метод ``dispatch`` совершает проверку прав доступа за счет вызова метода ``has_permissions``.
Проверка осуществляется за счет классов указанных в ``permission_classes`` и по умолчанию используется класс
``AllowAny``:

.. code:: python

    class TelegaViewSet:
        permission_classes = [AllowAny]



Дополнительные инструменты TelegaViewSet
************************************************

В этом разделе описаны следующие функциональные возможности класса, которые упрощает написание кода:

1. Внешние фильтры
2. Параметры настройки отображения данных;
3. Вспомогательные функции для отображения данных;
4. Вспомогательные функции бизнес логики;


Внешние фильтры
+++++++++++++++++++++

Достаточно часто возникают ситуации, когда нужно работать не со всеми элементами таблицы базы данных, а с какой-то
группой (например, группа элементов с определенным внешним ключом). Для таких целей стоит использовать список ``foreign_filters``,
который сохраняет в себе значения для фильтрации при вызове метода. Таким образом, в функции можно передавать
дополнительные аргументы, которые не рушат основную логику стандартных функций. На примере шаблона можно модифицировать
``BotMenuElemViewSet`` таким образом, что если указан дополнительный параметр, то в списке BotMenuElem отображаются
только те элементы, которые содержат в своем поле ``сommand`` указанный параметр. Для этого надо внести следующие изменения в код:

.. code:: python

    class BotMenuElemViewSet(TelegaViewSet):
        ...

        foreign_filter_amount = 1

        def get_queryset(self):
            queryset = super().get_queryset()
            if self.foreign_filters[0]:
                queryset = queryset.filter(command__contains=self.foreign_filters[0])
            return queryset


Где foreign_filter_amount определяет количество внешних фильтров. Для вызова метода с значением фильтра необходимо
их указывать сразу после названия функции в пути (utrls): ``"sb/sl&start&2"``, ``"sb/sl&start&2&1"``, ``"sb/sl&hello``.
Стоит отметить, что если не хотим указывать фильтр, то необходимо пропустить аргумент в пути (utrls): ``"sb/sl&&2"``.

На прямую конструировать и обрабатывать фильтры в путях (utrls) нет необходимости, так как функции ``gm_callback_data`` и ``get_utrl_params``
умеют с ними работать. В gm_callback_data также есть параметр ``add_filters`` (по умолчанию True), который определяет
включать ли в генерируемый путь (utrl) фильтры или нет. Если значение стоит False , то необходимо в аргументах функции
вручную указать фильтры: ``self.gm_callback_data('show_list', 'start', add_filters=False)``  (сгенерирует ``"sb/sl&start``).
Это позволяет менять значение фильтров при генерации путей.



Параметры настройки отображения данных
++++++++++++++++++++++++++++++++++++++++++

В ``TelegaViewSet`` есть следующие параметры для отображения элементов моделей:

* ``updating_fields: list`` - список полей, которые можно поменять (отображается при демонстрации элемента (``show_elem``);
* ``show_cancel_updating_button: bool`` - показывает кнопку отмены при изменении полей, которая ведет обратно к демонстрации
элемента (``show_elem``);
* ``deleting_with_confirm: bool`` - при удалении элемента спрашивать подтверждение у пользователя;
* ``cancel_adding_button: InlineKeyboardButtonDJ`` - кнопка отмены при создании элемента (метод ``create``);
* ``use_name_and_id_in_elem_showing: bool``  - включает использование названия и ID элемента при отображении этого элемента (методы ``show_list`` и ``show_elem``);
* ``meta_texts_dict: dict`` - словарь, который хранит стандартные текста для отображения (текста используются во всех методах);



Однако, этих полей не всегда хватает и нужно переопределять логику вспомогательных функций для красивого отображения информации.


Вспомогательные функции для отображения данных
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


В классе ``TelegaViewSet`` описаны следующие вспомогательные функции для генерации ответного сообщения:


* ``def generate_message_no_elem`` - если не был найден элемент с таким ID;
* ``def generate_message_success_created`` - при успешном создании модели ;
* ``def generate_message_next_field`` - при переходе на следующий атрибут формы;
* ``def generate_message_next_field_choice_buttons`` - генерирует кнопки для выбора вариантов для определенного атрибута формы (используется внутри ``generate_message_next_field``);
* ``def generate_message_value_error`` - вывод ошибки при добавлении атрибута формы;
* ``def generate_message_self_variant`` - формирует сообщение о необходимости написать значение вручную пользователем ;
* ``def generate_show_fields`` - отображает поля модели в сообщении (используется в ``show_elem`` с параметром``full_show=True``, а в``show_list`` ﹣с ``full_show=False``);
* ``def generate_value_str`` - генерирует строку с отображением определенного атрибута (используется в ``generate_show_fields``);
* ``def generate_elem_buttons`` -  отображает доступные кнопки (действия) при демонстрации элемента модели (вызове ``show_elem``) ;
* ``def gm_show_list_button_names`` - генерирует название кнопок элементов при отображении списка (вызове ``show_list``);

В зависимости от потребности кастомизации необходимо переопределять эти функции.



Вспомогательные функции бизнес логики
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

В классе ``TelegaViewSet`` используются следующие вспомогательные функции:

* ``def get_queryset`` - позволяет конструировать запросы для всех методов (чаще всего для фильтраци элементов испоьзуется, как в примере выше);
* ``def create_or_update_helper`` - основная логика для ``create`` и ``update`` методов;
* ``def show_list_get_queryset`` - позволяет кастомизировать выбор элементов для отображения в show_list;




handler_decor
~~~~~~~~~~~~~~~~

При написании своих обработчиков рекомендуется использовать обертку в виде  ``telegram_django_bot.utils.handler_decor``,
которая берет на себя выполнение следующий функций:

* Получение или создание пользователя в базе данных;
* В случае ошибки внутри функции обработчика возвращает пользователю сообщение об ошибке;
* Логгирует вызов обработчика;
* Отслеживает откуда перешел пользователь;
* Выбор языка для отправки сообщений пользователю (в случае включенной локализации);

Данный обработчик используется и внутри ``RouterCallbackMessageCommandHandler``, то есть при вызове ``TelegaViewSet`` классов.

Localization
~~~~~~~~~~~~~~~~

В бибилотеке расширены инструменты `локализации Django <https://docs.djangoproject.com/en/4.1/topics/i18n/>`_ для использования в Телеграме.
Для поддержки использования разных языков в библиотеке в ``telegram_django_bot.telegram_lib_redefinition`` расширяются возможности основных элементов библиотеки Python-Telegram-Bot:


1. ``telegram.Bot`` -> ``telegram_django_bot.BotDJ`` ;
2. ``telegram.ReplyMarkup`` -> ``telegram_django_bot.ReplyMarkupDJ`` ;
3. ``telegram.KeyboardButton`` -> ``telegram_django_bot.KeyboardButtonDJ`` ;
4. ``telegram.InlineKeyboardButton`` -> ``telegram_django_bot.InlineKeyboardButtonDJ`` ;
5. ``telegram.InlineKeyboardMarkup`` -> ``telegram_django_bot.InlineKeyboardMarkupDJ``;



При использовании этих классов в коде поддержка нескольких языков сводиться к следующим шагам:

1. Указание необходимых настроек в settings: ``LANGUAGES`` - списка языков, ``LANGUAGE_CODE`` - язык по умолчанию;
1. Необходимые тексты для перевода обертываются в ``gettext`` и ``gettext_lazy`` из ``django.utils.translation`` (как это работает в Django `почитать тут <https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#standard-translation>`_ )
2. Выполнение команды ``$ django-admin makemessages -a`` для генерации текстов для перевода (создаются в папке locale)
3. Генерации файлов перевода ``$ django-admin compilemessages``.

Для простоты понимания в шаблоне только часть функций использует локализацию. Использование можно посмотреть на примере
функции ``some_debug_func``.





Extra lib features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

В библиотеке предоставлены некоторые дополнительные инструменты для удобства разработки и управления ботом.


Модели библиотеки
************************************


Для корректной работы ``TelegaViewSet`` и других компонентов необходимо, чтобы модель, представляющая пользователя в Телеграмме, была унаследована
от ``telegram_django_bot.models.TelegramUser``, так как эти компоненты используют ее поля. ``TelegramUser`` унаследован от
``django.contrib.auth.models.AbstractUser`` (что позволяет при необходимости авторизовывать пользователей на сайте) и имеет
следующие дополнительные поля:

* ``id`` - переопределен для того, чтобы использовать ID пользователя из телеграмм;
* ``seed_code`` -  произвольное значение от 1 до 100, чтобы случайнным образом группировать пользователей для проведения тестов и анализа;
* ``telegram_username`` - username пользователя в телеграмме;
* ``telegram_language_code`` - код языка в телеграмме (некоторые языки имеют наречия и как следствие кодовое обозначение больше чем 2 символа);
* ``timezone`` - часовой пояс пользователя (для определения времени);
* ``current_utrl`` - путь (utrl) последнего действия пользователя (используется во ``TelegaViewSet``);
* ``current_utrl_code_dttm`` - время последнего действия, при сохранении пути;
* ``current_utrl_context_db`` - контекст пути (utrl);
* ``current_utrl_form_db`` - промежуточные данные для формы. Выступает как временное хранилище данных при заполнении формы;

Поля ``current_utrl_<суффикс>`` нужны для работы ``TelegaViewSet``, ``TelegaModelForm`` и скорей всего не нужны будут
при написании кода. Также модель имеет следующие методы (property) для упрощения взаимодействия с полями модели:

* ``current_utrl_form`` (property) - возвращает текущие временно сохраненные данные формы пути(utrl);
* ``current_utrl_context`` (property) - возвращает текущие контекст пути(utrl);
* ``save_form_in_db`` - сохраняет форму в поле ``current_utrl_form_db``;
* ``save_context_in_db`` - сохраняет контекст в поле ``current_utrl_context_db``;
* ``clear_status`` - очищает данные, связанные с использованным путем (поля ``current_utrl_<суффикс>`) ;
* ``language_code`` (property) - возвращает код языка, на котором надо формировать сообщения пользователю ;


В библиотеки описаны и дополнительные модели для повышения удобства использования бота:

* ``ActionLog`` - хранит действия пользователей. Записи помогают собирать аналитику и делать триггеры, которые срабатывают при определенных действиях;
* ``TeleDeepLink`` - хранит данные по каким ссылкам перешли новые пользователи (для анализа входного трафика);
* ``BotMenuElem`` - Достаточно часто в боте нужны сообщения, которые имеют только статические данные. Такими страницами могут быть хелп и стартовые сообщения.
 ``BotMenuElem`` позволяет настраивать такие страницы через админку, при этом не надо ничего писать в коде. В ``BotMenuElem`` есть
  возможность настраивать страницы в зависимости от стартовых deeplink. ``BotMenuElem`` умеет не только добавлять кнопки в сообщение, но и отправлять
   разные файлы. Для этого необходимо указывать ``media`` и формат файла ``message_format``. ``BotMenuElem`` позволяет быстро менять блоки меню бота без необходимости вносить изменения в код;
* ``BotMenuElemAttrText`` - вспомогательная модель для ``BotMenuElem``, отвечающая за перевод текстов на другие языки.
Элементы сами создаются в зависимости от указанных языков в настройках ``LANGUAGES``. Вам необходимо лишь заполнять перевод в поле ``translated_text`` ;
* ``Trigger`` - позволяет создавать триггеры в зависимости от определенных действий. Например, напомнить пользователю, что у него осталася
недозаполненный заказ, или подарить скидку, если он бездействует долго. Для работы триггеров необходимо добавить задания из
telegram_django_bot.tasks.create_triggers в расписание CeleryBeat;
* ``UserTrigger`` - вспомогательная модель для ``Trigger``, контролирующая кому уже были отправлены триггеры;





Дополнительные функции TG_DJ_Bot
*********************************************

Для повышения удобства ``TG_DJ_Bot`` обладает несколькими высокоуровневых функциями:

* ``send_format_message`` - Позволяет отправлять сообщение произвольного типа (внутри себя в зависимости от ``message_format`` подбирает нужный метод библиотеки ``Python-Telegram-Bot``).
Важной возможностью этой функцией является то, что если пользователь нажал на кнопку, то предыдущее сообщение бота изменяется, а не отправляется новое.
Если же все-таки в этом кейсе надо отправлять новое сообщение пользователю, то необходимо установить параметр ``only_send=True`` ;
* ``edit_or_send`` - обертка метода ``send_format_message`` для отправки текстовых сообщений с кнопками;
* ``send_botmenuelem`` - отправляет элемент ``BotMenuElem`` пользователю. Аргумент ``update`` может быть пустым;
* ``task_send_message_handler`` - создан для отправки сообщений пользователей. Обрабатывает ситуации, когда пользователь
заблокировал бота, удален или когда достигнут предел по отправки сообщений пользователям;


Utils
**********

В библиотеки предоставлены следующие дополнительные функции:


* ``telegram_django_bot.utils.add_log_action`` - для создания ActionLog пользователя;
* ``telegram_django_bot.utils.CalendarPagination`` - класс для генерации календаря с кнопками;
* ``telegram_django_bot.user_viewset.UserViewSet`` - класс пользователя телеграм для изменения языка и часового пояса;


Mapping details
********************

В этом разделе чуть подробнее разберем работу ``RouterCallbackMessageCommandHandler`` и ``telega_reverse``.

Как описывалось ранее ``RouterCallbackMessageCommandHandler`` используется для возможности написать обработчики в стиле
Django. Также ``RouterCallbackMessageCommandHandler`` предоставляет возможность обрабатывать вызовы ``BotMenuElem`` как
через команды, так и через callback. Это достигается за счет использования функций ``all_command_bme_handler`` и
``all_callback_bme_handler``. По умолчанию обработка вызовов  ``BotMenuElem`` включена и обрабатывается после того, как
не было найдено подходящего пути в описании utrls (путей в Django нотации). Если среди элементов ``BotMenuElem`` не было
найдено подходящего варианта, то считается, что ``BotMenuElem`` настроены неверно. Отключить вызовы ``BotMenuElem``
можно созданием класса с атрибутом ``only_utrl=True``.

В шаблоне-примере есть использование функции ``telega_reverse``, суть которой заключается в генерации пути (строки) до
обработчика, который указан в аргументе функции. Функция является аналогом `reverse <https://docs.djangoproject.com/en/4.1/ref/urlresolvers/#reverse>`_ функции Django
и позволяет избегать ошибок при изменении путей.




Тесты
**********************

В библиотеки также расширены возможности ``django.test.TestCase`` для использования с Телеграммом за счет класса ``TD_TestCase``.

Наиболее простой подход для тестирования работы бота является генерации сообщений, которые ожидает бот от Телеграмма и
отправка ответа в Телеграм (для проверки, что ответные сообщения бота в правильном формате). Класс ``TD_TestCase``
имеет функцию ``create_update`` для простого и быстрого создания ``Telegram.Update``, который как раз и формирует запрос
пользователя телеграмма. Таким образом, общий дизайн выглядит следующим образом:

1. Создается ``Telegram.Update``, эмулирующий запрос пользователя;
2. Вызывается функция для проверки, автоматически происходит проверка отправляемых допустимых данных в Телеграм (за счет отправки сообщений тестовым пользователям);
3. Проверяется корректность отправленных данных и изменений в бд за счет стандартных инструментов ``django.test.TestCase``.


Для работы тестов необходимо указать как минимум один ID тестового пользователя в разделе настроек ``TELEGRAM_TEST_USER_IDS``.
Пользователю будут отправляться сообщения, поэтому необходимо, чтобы у бота было разрешение писать тестовому пользователю.

