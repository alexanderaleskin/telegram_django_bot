import logging
from .models import BotMenuElem
from .utils import handler_decor, telega_resolve
from .td_viewset import TelegaViewSet
from django.contrib.auth import get_user_model

from telegram import (
    Update,
)


try:
    # version 20.x +
    from telegram.ext import BaseHandler as Handler
except ImportError:
    # old version
    from telegram.ext import Handler


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
                    return telega_resolve(user.current_utrl, self.utrl_conf)
        if update.effective_message and update.effective_message.text and update.effective_message.text.startswith('/'):
            return telega_resolve(update.effective_message.text, self.utrl_conf)

    def check_update(self, update: Update):
        """
        check if callback or message (command actually is message)
        :param update:
        :return:
        """
        if isinstance(update, Update):
            resolver = self.get_callback_utrl(update)
            if resolver:                
                self.callback = resolver.func(resolver.route) \
                    if issubclass(resolver.func, TelegaViewSet) else resolver.func
                return resolver.route
            elif not self.only_utrl:
                if update.callback_query:
                    self.callback = all_callback_bme_handler
                elif update.effective_message \
                        and update.effective_message.text \
                        and update.effective_message.text.startswith('/'):
                    self.callback =  all_command_bme_handler
            else:
                self.callback = None
            return self.callback

    def collect_additional_context(self, context, update, application, check_result) -> None:
        context.args = check_result
        

