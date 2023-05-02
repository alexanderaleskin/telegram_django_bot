Telegram Django Bot
============================

This library provides a Python high-level interface for creating Telegram Bots. It standardizes the coding in the best
practice of the web development. The library is based on `Django <https://www.djangoproject.com/>`_ and `Python-Telegram-Bot <https://python-telegram-bot.org/>`_.
It also provides viewset interface for managing data with.

If you start a new project, you could use `Telegram django bot template <https://github.com/alexanderaleskin/telergam_django_bot_template>`_ with preconfigured settings.

Install
------------

You can install via ``pip``:

.. code-block:: shell

    $ pip install telegram_django_bot


Then you can configure it in your app:


1. Add "telegram_django_bot" to your INSTALLED_APPS setting like this:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'telegram_django_bot',
        'django_json_widget', # needed for django admin site
    ]


If you are planning to use Django in asynchronous mode, then you need to set ``DJANGO_ALLOW_ASYNC_UNSAFE = True`` (otherwise DB writings will be failed).


2. Run ``python manage.py migrate`` to create the telegram_django_bot models (checked that the ``AUTH_USER_MODEL`` selected
in settings).


3. Set up constants in Django settings file:

* ``TELEGRAM_ROOT_UTRLCONF`` -  (same as ``ROOT_URLCONF`` for WEB) for using django notation in callback (routing) (strongly recommended)

  Not necessary, but useful settings:

* ``TELEGRAM_TOKEN`` - for adding "triggers",
* ``TELEGRAM_TEST_USER_IDS`` - for adding tests for your bot,
* Make sure, that ``LANGUAGE_CODE``, ``LANGUAGE_CODE``, ``USE_I18N`` are also used in the library for language localization.


4. This step connects ``Telegram Django Bot`` with ``Python-Telegram-Bot``. Add ``RouterCallbackMessageCommandHandler`` in handlers for using TELEGRAM_ROOT_UTRLCONF :

.. code-block:: python

    updater = Updater(bot=TG_DJ_Bot(settings.TELEGRAM_TOKEN))
    updater.dispatcher.add_handler(RouterCallbackMessageCommandHandler())

or in 20.x version :

.. code-block:: python

    bot = TG_DJ_Bot(settings.TELEGRAM_TOKEN)
    application = ApplicationBuilder().bot(bot).build()
    application.add_handler(RouterCallbackMessageCommandHandler())

    



Quick start
------------


Normally, Python-Telegram-Bot gives the next opportunities for bot creation:

* Python Interface for communication with Telegram API;
* Web service to get updates from telegram;

and Django:

* Django ORM  (communication with Database);
* Administration panel for management.


Telegram Django Bot provides next special opportunities:

* using Viewsets (typical action with model (create, update, list, delete));
* using Django localization.
* using function routing like urls routing in Django.
* creating general menu items with no-coding (through Django Admin Panel);
* collecting stats from user actions in the bot;
* other useful staff.


The key feature of the lib is ``TelegramViewSet`` - a class for managing Django ORM model. It is designed in a
similar way as `Django rest framework Viewset <https://www.django-rest-framework.org/api-guide/viewsets/>`_ , but has
a significant difference: while DRF Viewset provides a response in serializable format (usually in json format) to frontend app, TelegramViewSet
provides a response to the user in telegram interface in message format with buttons. So, you will manage data and receive
responses in human format by executing TelegramViewSet method. The methods use some kind of templates for generating human
responses (it is possible to overwrite these templates). By default, TelegramViewSet has 5 methods:

* ``create`` - create a new instance of the specified ORM model;
* ``change`` - update instance fields of specified ORM model;
* ``show_elem`` - show fields of the element and buttons with actions of this instance;
* ``show_list`` - show list of model elements (with pagination);
* ``delete`` - delete the instance


So, if, for example, you have a model of some *request* in your project:

.. code-block:: python

    from django.db import models

    class Request(models.Model):
        text = models.TextField()
        importance_level = models.PositiveSmallIntegerField()  # for example it will be integer field
        project = models.ForeignKey('Project', on_delete=models.CASCADE)
        tags = models.ManyToManyField('Tags')


The next piece of code gives the opportunity for full managing (create, update, show, delete) of this model from Telegram:

.. code-block:: python

    from telegram_django_bot import forms as td_forms
    from telegram_django_bot.td_viewset import TelegramViewSet


    class RequestForm(td_forms.TelegramModelForm):
        class Meta:
            model = Request
            fields = ['text', 'importance_level', 'project', 'tags']


    class RequestViewSet(TelegramViewSet):
        model_form = RequestForm
        queryset = Request.objects.all()
        viewset_name = 'Request'


If you need, you can add extra actions to RequestViewSet for managing (see details information below) or change existing functions.
There are several parameters and secondary functions in TelegramViewSet for customizing logic if it is necessary.

In this example, ``TelegramModelForm`` was used. TelegramModelForm is a descendant of Django ModelForm. So, you could use
labels, clean functions and other parameters and functions for managing logic and displaying.


TelegramViewSet is designed to answer next user actions: clicking buttons and sometimes sending messages. The library imposes
`Django URL notation <https://docs.djangoproject.com/en/4.1/topics/http/urls/>`_ for mapping user actions to TelegramViewSet methods (or usual handlers).
Usually, for correct mapping you just need to set ``TELEGRAM_ROOT_UTRLCONF`` and use ``RouterCallbackMessageCommandHandler`` in
dispatcher as it is mentioned above in the *Install paragraph*.

For correct mapping *RequestViewSet*  you should write in the TELEGRAM_ROOT_UTRLCONF file something like this:

.. code-block:: python

    from django.urls import re_path
    from .views import RequestViewSet

    urlpatterns = [
        re_path(r"^rv/", RequestViewSet, name='RequestViewSet'),
    ]

From this point, you can use buttons with callback data "rv/<function_code>" for function calling. For example:

* "rv/cr" - RequestViewSet.create method;
* "rv/sl" - RequestViewSet.show_list;


See these examples for great understanding:


1. `Telegram django bot template <https://github.com/alexanderaleskin/telergam_django_bot_template>`_
2. `Drive Bot <https://github.com/alexanderaleskin/drive_bot>`_


Deep in details
------------------

In this chapter, we will analyze how everything works. The main task of the library is to unify the code and
provide frequently used functions for developing a bot, that is why a lot of logic is based on resources and paradigms
of Django <https://www.djangoproject.com/>`_ and `Python-Telegram-Bot <https://python-telegram-bot.org/>`_ . Let's analyze
key features of the library on the example of `Telegram django bot template <https://github.com/alexanderaleskin/telergam_django_bot_template>`_ .

.. important::

    The template is based on 13.x Python-Telegram-Bot version (synchronous version). So, the next examples is suitable for that version. For use with 20.x versions you need to do some modification.


Since Telegram bots are designed as a tool for responding to user requests, writing a bot begins
from the user request handler. For this, the standard tools of the Python-Telegram-Bot library are used ﹣
``telegram.ext.Update``:

.. code-block:: python

     from telegram.ext import Updater

     def main():
         ...

         updater = Updater(bot=TG_DJ_Bot(TELEGRAM_TOKEN))
         add_handlers(updater)
         updater.start_polling()
         updater.idle()

     if __name__ == '__main__':
         main()


As indicated in the example, to run the bot (Update) you need to specify a few things (the ``Python-Telegram-Bot`` library standard):

1. an instance of the ``telegram.Bot`` model with the specified API token. In this case, a descendant ``telegram_django_bot.tg_dj_bot.TG_DJ_Bot``
of the ``telegram.Bot`` class is used. It has additional functionality for convenience (we will return to it later);
2. Handlers that will be called in response to user requests.

In the example, the list of handlers is specified in the ``add_handlers`` function:



.. code-block:: python

     from telegram_django_bot.routing import RouterCallbackMessageCommandHandler

     ...

     def add_handlers(updater: Updater):
         dp=updater.dispatcher
         dp.add_handler(RouterCallbackMessageCommandHandler())


The example adds 1 super handler ``RouterCallbackMessageCommandHandler``, which allows you to write handlers
in the style of handling link requests in the same way as it is done in ``Django``. ``RouterCallbackMessageCommandHandler`` allows you to handle
messages, user commands and button clicks by users. In other words, it replaces the handlers
``MessageHandler, CommandHandler, CallbackQueryHandler`` . Since the ``Telegram Django Bot`` library is an extension,
it does not prohibit the use of standard handlers of the ``Python-Telegram-Bot`` library for handle user requests.
(sometimes it is simply necessary, for example, if you need to process responses to surveys (you need to use PollAnswerHandler)).

`Django notation <https://docs.djangoproject.com/en/4.1/topics/http/urls/>`_ of routing handlers is that paths to handlers are described in a separate file or files.
As in the ``Django`` standard, the main file (root) for routing is specified in the project settings, where paths to handlers or paths to groups of handlers are stored.
The ``TELEGRAM_ROOT_UTRLCONF`` (same as ``ROOT_URLCONF`` for WEB) attribute is used to specify the path to the file. In the example template, we have the following settings:


``bot_conf.settings.py``:

.. code-block:: python

     TELEGRAM_ROOT_UTRLCONF = 'bot_conf.utrls'


``bot_conf.utrls.py``:

.. code-block:: python

     from django.urls import re_path, include

     urlpatterns = [
         re_path('', include(('base.utrls', 'base'), namespace='base')),
     ]


That is, only 1 group of handlers is connected in the file (which corresponds to the ``base`` application at the conceptual level). You can
add several groups as well, this can be convenient if you create several folders (applications) for storing code.
As you can see ``Django`` functions are imported without any redefinition.

There is following code in the specified included file ``base.utrls.py`` :


.. code-block:: python

    from django.urls import re_path
    from django.conf import settings
    from telegram_django_bot.user_viewset import UserViewSet
    from .views import start, BotMenuElemViewSet, some_debug_func


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

So, the end handlers (which are defined in the ``base.views.py`` file) are specified here. Thus, if
user in the bot writes the command ``/start``, then ``Updater`` receives a message about the user's action and selects
the appropriate for the request handler ``RouterCallbackMessageCommandHandler`` from a set of handlers. Then the
handler ``RouterCallbackMessageCommandHandler`` searches the appropriate for string ``/start`` path in ``utrls`` and
finds a suitable path ``'' + 'start'``, and then executes corresponding start function.

This distribution of handlers allows you to group part of the handlers into modules and quickly connect or
change them, while not being afraid of confusion which handlers need to be called, as it can be if all paths from
different modules to handlers are described in one place as required by ``Python-Telegram-Bot``.

In this example file ``base.utrls.py`` also ViewSets are used in addition to simple handler functions like ``def start`` and ``def some_debug_func``.
ViewSet is an aggregator of several functions. The concept of it is that you quite often need to apply
the same operations for a dataset, such as create, update, show, delete an example of dataset.
There is the class ``telegram_django_bot.td_viewset.TelegramViewSet`` in the library  for such purposes. The class manages
the Django ORM database model. ``TelegramViewSet`` has 5 functions for managing the model:


========= ======== ===========================
 Метод     UTRL      Description
--------- -------- ---------------------------
create     cr       Create model
change     up       Change model attributes
delete     de       Deleting a model
show_elem  se       Display a model
show_list  sl       Display a list of models
========= ======== ===========================

Thus, if we want to call the ``BotMenuElemViewSet.create`` method to create an element, we need to use
path 'sb/cr', whereby the first part of the path 'sb/'  the router ``RouterCallbackMessageCommandHandler`` will execute
the ``BotMenuElemViewSet`` class, namely the ``TelegramViewSet.dispatch`` method, which in turn will call  the ``create`` method by analyzing the second part of the path
``cr``.

To sum up the scheme of handlers routing, there are following key points:

1. ``telegram.ext.Update`` is used as a receiver of messages from Telegram;
2. Standard handlers of the ``Python-Telegram-Bot`` library can be used as handlers. For convenient use Django's path scheme and ``TelegramViewSet`` you need to use ``RouterCallbackMessageCommandHandler``.
3. ``TelegramViewSet`` aggregates a set of standard functions for managing data, what is made possible to group code associated with one type of data type in one class (place).



TelegramViewSet features
~~~~~~~~~~~~~~~~~~~~~~~~

As described above, TelegramViewSet contains standard functions for data manipulation.
Due to such standard data processing methods, it turns out in the example to describe the logic of ``BotMenuElemViewSet`` in 40
lines of code, also using some customization for beautiful data displaying.


To use all the features of the TelegramViewSet in your class, it should be inherited from it, as, for example, this is done
in the ``BotMenuElemViewSet``:


.. code-block:: python

    from telegram_django_bot.td_viewset import TelegramViewSet

    class BotMenuElemViewSet(TelegramViewSet):


In order to customize the ViewSet, you must specify 3 required attributes:

1. ``viewset_name`` - class name, used to display to telegram users
2. ``model_form`` - data form, used to specify which fields of the ORM database model to use in the viewset;
3. ``queryset`` - basic query for getting model elements.


The ``BotMenuElemViewSet`` is used the following values:

.. code-block:: python

    from telegram_django_bot import forms as td_forms
    from telegram_django_bot.models import BotMenuElem

    class BotMenuElemForm(td_forms.TelegramModelForm):
        form_name = _("Menu elem")

        class Meta:
            model = BotMenuElem
            fields = ['command', "is_visable", "callbacks_db", "message", "buttons_db"]

    class BotMenuElemViewSet(TelegramViewSet):
        viewset_name = 'BotMenuElem'
        model_form = BotMenuElemForm
        queryset = BotMenuElem.objects.all()


where ``BotMenuElemForm`` is a descendant of the ``Django ModelFrom`` class, so it has a similar structure and parameterization methods.
`` form_name ``  stands for the name of the form and is used in some messages sent to Telegram users.


TelegramViewSet has quite a lot in common with Viewset analogs tailored for WEB development (for example,
`django-rest-framework viewsets <https://www.django-rest-framework.org/api-guide/viewsets/>`_ ). However, as part of the development of Telegram bots, TelegramViewSet
has some special features:

1. An unusual way to create elements;
2. The display of information in bots is limited and most often comes down to displaying text and buttons, so the viewset in addition to business logic includes the creation of standard responses to user actions in the form of messages with buttons.



Forms
************


Since Telegram does not have the ability to create forms (in the classic Web sense) and communication between the bot and the user takes place in a chat, then
the most intuitive solution for filling out a form (creating an element) is filling the form attribute by attribute,
when the first element of the form is filled first, then the second, and so on. With this approach, it is necessary to use temporary storage for remembering
specified values in order to create an element from the form at the end. ``TelegramModelForm`` and ``TelegramForm`` are implemented just
in such way for taking over this process. The difference between these classes and the standard Django classes is precisely
in the modification of the method of filling in the form fields, otherwise they do not differ from standard forms.

``TelegramModelForm`` and ``TelegramForm`` as Django descendants of ``ModelForm`` and ``Form`` have the following parameters, which you may need to customize:

1. The clean function and other `form validation process functions <https://docs.djangoproject.com/en/4.1/ref/forms/validation/>`_ ;
2. ``labels`` - field names;
3. ``forms.HiddenInput`` - designation of hidden fields (hiding fields allows them not to be shown to the user, while using and configuring in forms or in ``TelegramViewSet``).



``TelegramViewSet`` is designed to interact with descendants of the ``TelegramModelForm`` class and allows you to use
generate forms with different fields, such as ``CharField, IntegerField`` or ``ForeignKey, ManyToManyField``. Also, it is a good idea
to use the ``prechoice_fields_values`` dictionary in ``TelegramViewSet`` descendants for improving the convenience of filling out forms for users.
It is possible to store a list of frequently used values of form fields in the ``prechoice_fields_values``.
This allows users to select the desired values by clicking buttons rather than
writing text manually. The template has an example of using this field:


.. code-block:: python

    class BotMenuElemViewSet(TelegramViewSet):
        ...

        prechoice_fields_values = {
            'is_visable': (
                (True, '👁 Visable'),
                (False, '🚫 Disabled'),
            )
        }

In this case, 2 values are specified for choosing true or false for the boolean field ``is_visable``. You can also use
``prechoice_fields_values`` for ``CharField, IntegerField`` or any other fields.
Sometimes the list of values needs to be generated dynamically, in which case you can override
``prechoice_fields_values`` as a ``@property`` function.


Key logic of TelegramViewSet
************************************************

The main function of the class, which is selected the function for managing data by the request of the user,  is ``TelegramViewSet.dispatch``.
Let's analyze its logic in more detail:

.. code-block:: python

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


Like a regular handler, the function takes 3 arguments as input: bot, update, user. After saving these arguments in class,
the determination of the current routing path is occurred. It is determined either by pressing a button in the bot (the ``callback_data`` value of the button), or
can be stored in the user attribute ``user.current_utrl``. The second option is possible if the user manually enters
some information (for example, filled in a text field of form). After that, the arguments are extracted from the path
to call a specific function. Storing and interacting with arguments in a path is similar to how ``sys.argv`` works. So,
for example, the string ``"sl&1&20"`` will be converted to the list ``['sl', '1', '20']``. The separator character between attributes
is ``&`` by default and can be changed via the ``TelegramViewSet.ARGS_SEPARATOR_SYMBOL`` variable.

When using ``TelegramViewSet`` you most likely won't have to interact with the argument string directly, since
``dispatch`` converts a string into arguments. And for creating a ``callback_data`` button string, that the user can call another method from Telegram interface, you should use
``TelegramViewSet.gm_callback_data`` function. In case you need more low-level interaction with function arguments, then
you can use the ``construct_utrl`` and ``get_utrl_params`` functions.

After receiving the utrl_args arguments and checking access rights, the managing method (action) is directly selected and called.
The first argument, which is the short name for the function, is popped from the utrl_args. All other arguments are passed as parameters
into a function. Inside the function, the necessary business logic and the data formatting for displaying to the user as a response take place.
Any such managing function in the ``TelegramViewSet`` class must return the action type ``chat_action`` and the parameters to that action ``chat_action_args``.
By default, the class has only 1 action ﹣ ``CHAT_ACTION_MESSAGE``, which means that the user will receive
a text message (possibly with buttons) as an answer for his/her action. The arguments for this action are the text of the message and a list of buttons (can be None).


After the function is processed, a response is sent to the user by ``send_answer`` function and the user's action is logged.


The methods to call in ``viewset_routing`` are the ``create, update, delete, show_elem, show_list`` methods.
You can also add your own methods. Suppose we want to add a ``def super_method(self, *args)`` method, then
you need to add the following lines in the class:

.. code-block:: python

    class SomeViewSetClass(TelegramViewSet):
        ...

        actions = ['create', 'change', 'delete', 'show_elem', 'show_list', 'super_method']

        command_routing_super_method = 'sm'


        def super_method(self, *args):
            ...


Where ``actions`` defines the list of available methods and ``command_routing_<method>`` defines the path (url; short name) of the method.

As noted above, the ``dispatch`` method performs a permissions check by calling the ``has_permissions`` method.
The check is performed by the classes specified in ``permission_classes`` and the default class is ``AllowAny``:

.. code-block:: python

    class TelegramViewSet:
        permission_classes = [AllowAny]



Additional TelegramViewSet Tools
************************************************

This section describes the following class functionality that makes it easier to write code:

1. External filters;
2. Data display setting options;
3. Helper functions for displaying data;
4. Helper functions of business logic;


External filters
+++++++++++++++++++++

Quite often, there is a situation when you need to work not with all the elements of a database table, but with some
group (for example, a group of elements with a specific foreign key). For such purposes, you should use the ``foreign_filters`` list,
which stores the values for filtering when the method is called. How exactly to use these filters is up to you, but
usually it is a good idea to use it in the ``get_queryset`` function. Thus, it is possible to pass to functions
additional arguments that do not break the key logic of standard functions. Using the template example, you can modify
``BotMenuElemViewSet`` so that if an additional parameter is specified, then the BotMenuElem list displays
only those elements that contain the specified parameter in their ``command`` attribute. To do this, you need to make the following changes to the code:


.. code-block:: python

    class BotMenuElemViewSet(TelegramViewSet):
        ...

        foreign_filter_amount = 1

        def get_queryset(self):
            queryset = super().get_queryset()
            if self.foreign_filters[0]:
                queryset = queryset.filter(command__contains=self.foreign_filters[0])
            return queryset


Where ``foreign_filter_amount`` specifies the number of foreign filters. To call a method with a filter value, you must
specify them right after the function name in the path (utrls): ``"sb/sl&start&2"``, ``"sb/sl&start&2&1"``, ``"sb/sl&hello``.
It is worth noting that if we do not want to specify a filter, then we need to skip the argument in the path (utrls) in the next way: ``"sb/sl&&2"``.

There is no need to construct and process filters in paths (utrls) directly, since the functions ``gm_callback_data`` and ``get_utrl_params``
know how to work with them. gm_callback_data also has a parameter ``add_filters`` (default True) which defines
whether to include filters in the generated path (utrl) or not. If the value is False , then it is necessary in the function arguments
manually specify filters: ``self.gm_callback_data('show_list', 'start', add_filters=False)`` (will generate ``"sb/sl&start``).
This allows you to change the value of filters when generating paths.

A more detailed use of external filters can be seen in the example of `Drive Bot <https://github.com/alexanderaleskin/drive_bot>`_ .

Data display options
++++++++++++++++++++++++++++++++++++++++++

The ``TelegramViewSet`` has the following options for displaying model elements:

* ``updating_fields: list`` - list of fields that can be changed (displayed when showing the element (``show_elem``);
* ``show_cancel_updating_button: bool = True`` - shows a cancel button when changing fields, which leads back to the displaying element (``show_elem``);
* ``deleting_with_confirm: bool = True`` - ask the user for confirmation when deleting an element;
* ``cancel_adding_button: InlineKeyboardButtonDJ = None`` - cancel button when creating an element (``create`` method);
* ``use_name_and_id_in_elem_showing: bool = True`` - enables the use of the name and ID of the element when displaying this element (methods ``show_list`` and ``show_elem``);
* ``meta_texts_dict: dict`` - a dictionary that stores standard texts for display (texts are used in all methods).



However, these fields are not always enough and you need to redefine the logic of helper functions for a beautiful display of information.


Helper functions for displaying data
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


The ``TelegramViewSet`` class describes the following helper functions for generating a response message:


* ``def gm_no_elem`` - if no element with this ID was found;
* ``def gm_success_created`` - successful creation of the model;
* ``def gm_next_field`` - when moving to the next form attribute;
* ``def gm_next_field_choice_buttons`` - generates buttons to select options for a specific form attribute (used inside ``gm_next_field``);
* ``def gm_value_error`` - error output when adding a form attribute;
* ``def gm_self_variant`` - generates a message about the need to write the value manually by the user;
* ``def gm_show_elem_or_list_fields`` - displays model fields in the message (used in ``show_elem`` with ``full_show=True``, and in ``show_list`` ﹣with ``full_show=False``);
* ``def gm_value_str`` - generates a string displaying a specific attribute (used in ``gm_show_elem_or_list_fields``);
* ``def gm_show_elem_create_buttons`` - displays available buttons (actions) when showing a model element (calling ``show_elem``) ;
* ``def gm_show_list_button_names`` - generates the names of item buttons when displaying the list (calling ``show_list``);

Depending on the need for customization, it is necessary to redefine these functions.


Helper functions of business logic
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The ``TelegramViewSet`` class uses the following helper functions:

* ``def get_queryset`` - allows you to modify Model queries to the database (most often used to filter elements, as in the example above);
* ``def create_or_update_helper`` - main logic for ``create`` and ``update`` methods;
* ``def show_list_get_queryset`` - allows you to customize the selection of items to display in show_list;


handler_decor
~~~~~~~~~~~~~~~~

When writing your own handlers, it is recommended to use a wrapper like ``telegram_django_bot.utils.handler_decor``,
which performs the following functions:

* Getting or creating a user in the database;
* In case of an error inside the handler function, returns an error message to the user;
* Logs the handler call;
* Tracks where the user came from;
* Choice of language for sending messages to the user (in the case of localization enabled);

This handler is also used inside ``RouterCallbackMessageCommandHandler``, and as a result in calling ``TelegramViewSet`` classes.

Localization
~~~~~~~~~~~~~~~~

The library expands the `Django localization tools <https://docs.djangoproject.com/en/4.1/topics/i18n/>`_ for use in Telegram.
To support the use of different languages, the main elements of the Python-Telegram-Bot library are redefined in ``telegram_django_bot.telegram_lib_redefinition``:


1. ``telegram.Bot`` -> ``telegram_django_bot.BotDJ`` ;
2. ``telegram.ReplyMarkup`` -> ``telegram_django_bot.ReplyMarkupDJ`` ;
3. ``telegram.KeyboardButton`` -> ``telegram_django_bot.KeyboardButtonDJ`` ;
4. ``telegram.InlineKeyboardButton`` -> ``telegram_django_bot.InlineKeyboardButtonDJ`` ;
5. ``telegram.InlineKeyboardMarkup`` -> ``telegram_django_bot.InlineKeyboardMarkupDJ``.


When using these classes in code, multilingual support comes down to the following steps:


1. Specifying the necessary settings in the settings.py file: ``LANGUAGES`` - list of languages, ``LANGUAGE_CODE`` - default language;
2. Create folder with translations: ``$ django-admin makemessages -l <language_code>``
3. Necessary texts for translation are wrapped in ``gettext`` and ``gettext_lazy`` from ``django.utils.translation`` (how it works in Django `read here <https://docs.djangoproject.com/en /4.1/topics/i18n/translation/#standard-translation>`_ )
4. Run command ``$ django-admin makemessages -a`` to update texts for translation (created in locale folder)
5. Generation of translation files ``$ django-admin compilemessages``.

Only a part of the functions uses localization in the template. It is made for easy understanding. The usage of localization can be seen in the example
functions ``some_debug_func``.


Extra lib features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The library provides some additional tools for the convenience of developing and managing the bot.

Embedded ORM lib models
************************************


For the correct work of ``TelegramViewSet`` and other components the Django ORM model representing the user in Telegram must be inherited
from ``telegram_django_bot.models.TelegramUser``, as these components use its fields. ``TelegramUser`` inherited from
``django.contrib.auth.models.AbstractUser`` (which allows you to authorize users on the site if necessary) and has
the following additional fields:

* ``id`` - redefined to use user ID from telegrams;
* ``seed_code`` - arbitrary value from 1 to 100 to randomly group users for tests and analysis;
* ``telegram_username`` - username of the user in telegram;
* ``telegram_language_code`` - telegram language code (some languages have dialects and as a result the code designation is more than 2 symbols);
* ``timezone`` - the user's time zone (for determining the time);
* ``current_utrl`` - path (utrl) of the last user action (used in ``TelegramViewSet``);
* ``current_utrl_code_dttm`` - time of the last action, when saving the path;
* ``current_utrl_context_db`` - path context (utrl);
* ``current_utrl_form_db`` - intermediate data for the form. Acts as a temporary data store when filling out a form;

Fields ``current_utrl_<suffix>`` are needed for ``TelegramViewSet``, ``TelegramModelForm`` and are needed in exceptional cases
when writing code. The model also has the following methods (property) to simplify interaction with model fields:

* ``current_utrl_form`` (property) - returns the current temporarily stored path form data (utrl);
* ``current_utrl_context`` (property) - returns the current path context (utrl);
* ``save_form_in_db`` - saves the form in the ``current_utrl_form_db`` field;
* ``save_context_in_db`` - saves the context in the field ``current_utrl_context_db``;
* ``clear_status`` - clears the data associated with the used path (fields ``current_utrl_<suffix>``) ;
* ``language_code`` (property) - returns the language code in which messages should be generated for the user;


If you want, you can create your self Django ORM model representing the user, you just need to copy
``id, telegram_username, telegram_language_code, current_utrl, current_utrl_code_dttm, current_utrl_context_db, current_utrl_form_db``
and corresponding functions.


The library also describes additional models to improve the usability of the bot:

* ``ActionLog`` - stores user actions. Records help to collect analytics and make triggers that work on certain actions;
* ``TeleDeepLink`` - stores data on which links new users have clicked (to analyze input traffic);
* ``BotMenuElem`` - Quite often a bot needs messages that have only static data. These pages can be help and start messages. ``BotMenuElem`` allows you to configure such pages through the admin panel, without having to write anything in the code. In ``BotMenuElem`` there is the ability to customize pages depending on the starting deeplinks. ``BotMenuElem`` can not only add buttons to the message, but also send different files. To do this, you must specify ``media`` and the file format ``message_format``. ``BotMenuElem`` allows you to quickly change bot menu blocks without having to make changes to the code;
* ``BotMenuElemAttrText`` - helper model for ``BotMenuElem``, responsible for translating texts into other languages. The elements themselves are created depending on the specified languages in the ``LANGUAGES`` settings. You only need to fill in the translation in the ``translated_text`` field;
* ``Trigger`` - allows you to create triggers depending on certain actions. For example, remind the user that he has left incomplete order, or give a discount if it is inactive for a long time. For triggers to work, you need to add tasks from ``telegram_django_bot.tasks.create_triggers`` to CeleryBeat schedule;
* ``UserTrigger`` - helper model for ``Trigger``, controlling to whom triggers have already been sent;


Additional functions of TG_DJ_Bot
*********************************************

To improve convenience, ``TG_DJ_Bot`` has several high-level functions:

* ``send_format_message`` - Allows you to send a message of an arbitrary type (internally, depending on the ``message_format`` selects the appropriate method of the ``Python-Telegram-Bot`` library). An important feature of this function is that if the user clicks on the button, then the previous message of the bot is changed, rather than a new one being sent. If, nevertheless you need to send a new message to the user, then you need to set the parameter ``only_send=True`` ;
* ``edit_or_send`` - wrapper of the ``send_format_message`` method for sending text messages with buttons;
* ``send_botmenuelem`` - Sends a ``BotMenuElem`` to the user. The ``update`` argument can be empty;
* ``task_send_message_handler`` - created for sending messages to many users. Handles situations where the user blocked the bot, deleted or when the limit for sending messages to users is reached;


Utils
**********

The following additional functions are provided in the libraries:


* ``telegram_django_bot.utils.add_log_action`` - to create a user ActionLog;
* ``telegram_django_bot.utils.CalendarPagination`` - class for generating a calendar with buttons;
* ``telegram_django_bot.user_viewset.UserViewSet`` - telegram user class for changing language and time zone;


Routing details
********************

In this section, we will analyze the work of ``RouterCallbackMessageCommandHandler`` and ``telegram_reverse`` in a little more detail.

As described earlier ``RouterCallbackMessageCommandHandler`` is used to be able to write handlers in the style
Django. Also ``RouterCallbackMessageCommandHandler`` provides the ability to handle calls to ``BotMenuElem`` as
through commands, and through callback. This is achieved by using the functions ``all_command_bme_handler`` and
``all_callback_bme_handler``. By default, ``BotMenuElem`` call handling is enabled and handled after
no suitable path was found in the description of utrls (paths in Django notation). If there is no ``BotMenuElem`` element
match is found, the ``BotMenuElem`` is considered to be configured incorrectly and an error message is returned to the user.
You can create a class with the ``only_utrl=True`` attribute, what is disable calls to ``BotMenuElem``.

The example template contains the use of the ``telegram_reverse`` function, the essence of which is to generate a path (string) to the
handler specified in the function argument. The function is analogous to the `reverse <https://docs.djangoproject.com/en/4.1/ref/urlresolvers/#reverse>`_ Django function
and avoids errors when changing paths.



Tests
**********************

The library also extends the ``django.test.TestCase`` capabilities for use with Telegram through the ``TD_TestCase`` class.

The simplest approach for testing the bot is to generate messages that the bot expects from Telegram and
send a response to Telegram (to check that the bot's response messages are in the correct format). Class ``TD_TestCase``
has a function ``create_update`` for easy and fast creation of ``Telegram.Update`` which generates the request
telegram user. So the overall design looks like this:

1. A ``Telegram.Update`` is created for emitting a user request;
2. The ``handle_update`` lambda function, which uses ``RouterCallbackMessageCommandHandler``,  is called with created update. It does its staff and as a result sends a real message to the test user. Due to this, the correctness of the response data format  is checked by Telegram;
3. The correctness of the sent data and changes in the database is checked using the standard tools ``django.test.TestCase``.

You need to specify at least one test user ID in the ``TELEGRAM_TEST_USER_IDS`` settings section for correct tests work.
Messages will be sent to that user, so the bot needs to have permission to write to that user.

In the ``tests`` folder you could find test examples.
