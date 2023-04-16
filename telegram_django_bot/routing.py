import logging
from .models import BotMenuElem
from .utils import handler_decor
from .td_viewset import TelegaViewSet
from django.urls import resolve, Resolver404, reverse
from django.conf import settings
from django.contrib.auth import get_user_model

import telegram
import inspect

from telegram.ext import BaseHandler as Handler
from telegram import Update


def telega_resolve(path, utrl_conf=None):
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


def telega_reverse(viewname, utrl_conf=None, args=None, kwargs=None, current_app=None):
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
        if update.callback_query:
            return telega_resolve(update.callback_query.data, self.utrl_conf)
        else:
            user_details = update.effective_message.from_user
            user = get_user_model().objects.filter(id=user_details.id).first()
            if user:
                logging.info(f'user.current_utrl {user.current_utrl}')
                if user.current_utrl:
                    return telega_resolve(user.current_utrl, self.utrl_conf), user.current_utrl
        if update.effective_message and update.effective_message.text and update.effective_message.text.startswith('/'):
            return telega_resolve(update.effective_message.text, self.utrl_conf)

    def check_update(self, update: Update):
        if isinstance(update, Update):
            callback = self.get_callback_utrl(update)
            if type(callback) is tuple:
                callback, current_utrl = callback
                fallback_command = None if self.only_utrl or not update.message.text.startswith('/') \
                    else all_command_bme_handler
                return telega_resolve(current_utrl, self.utrl_conf) or fallback_command
            fallback_callback = None if self.only_utrl else all_callback_bme_handler
            return callback or fallback_callback

    def handle_update(self, update, dispatcher, check_result: object, context=None):
        callback_func = check_result
        self.collect_additional_context(context, update, dispatcher, check_result)
        if callback_func in [all_callback_bme_handler, all_command_bme_handler]:
            return callback_func(update, context)
        if inspect.isclass(callback_func.func) and issubclass(callback_func.func, TelegaViewSet):
            viewset = callback_func.func(callback_func.route)
            decorating = handler_decor(log_type='N', )
            callback_func = decorating(viewset.dispatch)
        else:
            callback_func = callback_func.func
        return callback_func(update, context)


