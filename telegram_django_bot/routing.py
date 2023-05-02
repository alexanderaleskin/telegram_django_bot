import logging
from .models import BotMenuElem
from .utils import handler_decor
from .td_viewset import TelegramViewSet
from django.urls import resolve, Resolver404, reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from telegram import (
    Update,
)
import inspect


try:
    # version 20.x +
    from telegram.ext import BaseHandler as Handler
except ImportError:
    # old version
    from telegram.ext import Handler


def telegram_resolve(path, utrl_conf=None):
    if path[0] != '/':
        path = f'/{path}'

    if '?' in path:
        path = path.split('?')[0]

    if utrl_conf is None:
        utrl_conf = settings.TELEGRAM_ROOT_UTRLCONF

    try:
        resolver_match = resolve(path, utrl_conf)
    except Resolver404:
        resolver_match = None
    return resolver_match


def telegram_reverse(viewname, utrl_conf=None, args=None, kwargs=None, current_app=None):
    if utrl_conf is None:
        utrl_conf = settings.TELEGRAM_ROOT_UTRLCONF

    response = reverse(viewname, utrl_conf, args, kwargs, current_app)
    if response[0] == '/':
        response = response[1:]
    return response


@handler_decor(log_type='C')
def all_command_bme_handler(bot, update, user):

    if len(update.message.text[1:]) and 'start' == update.message.text[1:].split()[0]:
        menu_elem = None
        if len(update.message.text[1:]) > 6:  # 'start ' + something
            menu_elem = BotMenuElem.objects.filter(
                command__contains=update.message.text[1:],
                is_visable=True,
            ).first()

        if menu_elem is None:
            menu_elem = BotMenuElem.objects.filter(
                command='start',
                is_visable=True,
            ).first()
    else:
        menu_elem = BotMenuElem.objects.filter(
            command=update.message.text[1:],
            is_visable=True,
        ).first()
    return bot.send_botmenuelem(update, user, menu_elem)


@handler_decor(log_type='C')
def all_callback_bme_handler(bot, update, user):
    menu_elem = BotMenuElem.objects.filter(
        callbacks_db__contains=update.callback_query.data,
        is_visable=True,
    ).first()
    return bot.send_botmenuelem(update, user, menu_elem)



class RouterCallbackMessageCommandHandler(Handler):
    def __init__(self, utrl_conf=None, only_utrl=False, **kwargs):
        kwargs['callback'] = lambda x: 'for base class'
        super().__init__(**kwargs)
        self.callback = None
        self.utrl_conf = utrl_conf
        self.only_utrl = only_utrl # without BME elems

    def get_callback_utrl(self, update):
        callback_func = None
        # check if utrls
        if update.callback_query:
            callback_func = telegram_resolve(update.callback_query.data, self.utrl_conf)
        elif update.message and update.message.text and update.message.text[0] == '/':  # is it ok? seems message couldnt be an url
            callback_func = telegram_resolve(update.message.text, self.utrl_conf)

        if callback_func is None:
            # update.message -- could be data or info for managing, command could not be a data, it is managing info
            if update.message and (update.message.text is None or update.message.text[0] != '/'):
                user_details = update.message.from_user

                user = get_user_model().objects.filter(id=user_details.id).first()
                if user:
                    logging.info(f'user.current_utrl {user.current_utrl}')
                    if user.current_utrl:
                        callback_func = telegram_resolve(user.current_utrl, self.utrl_conf)
        return callback_func

    def check_update(self, update: object):
        """
        check if callback or message (command actually is message)
        :param update:
        :return:
        """
        if isinstance(update, Update) and (update.effective_message or update.callback_query):
            callback = self.get_callback_utrl(update)
            if callback:
                return True
            elif not self.only_utrl:
                if update.message and update.message.text and update.message.text[0] == '/':
                    # if it is a command then it should be  early in handlers
                    # or in BME (then return True
                    return True
                elif update.callback_query:
                    return True
        return None

    def handle_update(
        self,
        update,
        dispatcher,
        check_result: object,
        context=None,
    ):
        # todo: add flush utrl and data if viewset utrl change or error

        callback_func = self.get_callback_utrl(update)

        if not callback_func is None:
            if inspect.isclass(callback_func.func) and issubclass(callback_func.func, TelegramViewSet):
                viewset = callback_func.func(callback_func.route)

                decorating = handler_decor(log_type='N',)

                callback_func = decorating(viewset.dispatch)

            else:
                callback_func = callback_func.func

        # check if in BME (we do not need check only_utrl here, as there was a check in self.check_update)
        if callback_func is None:
            if update.callback_query:
                callback_func = all_callback_bme_handler
            else:
                callback_func = all_command_bme_handler

        self.collect_additional_context(context, update, dispatcher, check_result)
        return callback_func(update, context)


