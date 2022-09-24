
from .models import BotMenuElem
from .utils import handler_decor
from .td_viewset import TelegaViewSet
from django.urls import resolve, Resolver404, reverse
from django.conf import settings
from django.contrib.auth import get_user_model

import telegram
import inspect

from telegram.ext import Handler, CallbackQueryHandler, Filters


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
    def __init__(self, utrl_conf=None, **kwargs):
        kwargs['callback'] = lambda x: 'for base class'
        super().__init__(**kwargs)
        self.callback = None
        self.utrl_conf = utrl_conf

    def check_update(self, update: object):
        """
        check if callback or message (command actually is message)
        :param update:
        :return:
        """
        if isinstance(update, telegram.Update) and (update.effective_message or update.callback_query):
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

        callback_func = None
        # check if utrls
        if update.callback_query:
            callback_func = telega_resolve(update.callback_query.data, self.utrl_conf)
        elif update.message and update.message.text[0] == '/':  # is it ok? seems message couldnt be an url
            callback_func = telega_resolve(update.message.text, self.utrl_conf)

        if callback_func is None:
            # should callback_query resolved by update.callback_query.data (update.inline_query.from_user -- not supported yet)
            # if update.callback_query:
            #     user_details = update.callback_query.from_user
            # elif update.inline_query:
            #     user_details = update.inline_query.from_user
            # else:

            # update.message -- could be data or info for managing, command could not be a data, it is managing info
            if update.message and update.message.text[0] != '/':
                user_details = update.message.from_user

                user = get_user_model().objects.filter(id=user_details.id).first()
                if user:
                    print('user.current_utrl', user.current_utrl)
                    if user.current_utrl:
                        callback_func = telega_resolve(user.current_utrl, self.utrl_conf)

        if not callback_func is None:
            if inspect.isclass(callback_func.func) and issubclass(callback_func.func, TelegaViewSet):
                viewset = callback_func.func(callback_func.route)

                decorating = handler_decor(log_type='N',)

                callback_func = decorating(viewset.dispatch)

            else:
                callback_func = callback_func.func

        # check if in BME
        if callback_func is None:
            if update.callback_query:
                callback_func = all_callback_bme_handler
            else:
                callback_func = all_command_bme_handler

        self.collect_additional_context(context, update, dispatcher, check_result)
        return callback_func(update, context)

        # self.callback = callback_func
        # # super().handle_update(update, dispatcher, check_result, context)
        # self.callback = None



#
# @handler_decor(log_type='C')
# def all_command_handler(bot, update, user):
#
#     menu_elem = BotMenuElem.objects.filter(
#         command=update.message.text[1:],
#         is_visable=True,
#     ).first()
#     return bot.send_botmenuelem(update, user, menu_elem)
#
#
# class AllCommandsHandler(Handler):
#     def __init__(
#             self,
#             pass_update_queue: bool = False,
#             pass_job_queue: bool = False,
#             pass_user_data: bool = False,
#             pass_chat_data: bool = False,
#             run_async: Union[bool, DefaultValue] = DEFAULT_FALSE,
#             *args,
#             **kwargs,
#     ):
#         callback = all_command_handler
#         super().__init__(
#             callback,
#             pass_update_queue=pass_update_queue,
#             pass_job_queue=pass_job_queue,
#             pass_user_data=pass_user_data,
#             pass_chat_data=pass_chat_data,
#             run_async=run_async,
#         )
#         self.filters = Filters.update.messages
#
#     def check_update(
#         self, update: object
#     ) -> Optional[Union[bool, Tuple[List[str], Optional[Union[bool, Dict]]]]]:
#         """Determines whether an update should be passed to this handlers :attr:`callback`.
#
#         Args:
#             update (:class:`telegram.Update` | :obj:`object`): Incoming update.
#
#         Returns:
#             :obj:`list`: The list of args for the handler.
#
#         """
#
#         if isinstance(update, telegram.Update) and update.effective_message:
#             message = update.effective_message
#
#             if (
#                 message.entities
#                 and message.entities[0].type == telegram.MessageEntity.BOT_COMMAND
#                 and message.entities[0].offset == 0
#                 and message.text
#                 and message.bot
#             ):
#                 command = message.text[1 : message.entities[0].length]
#                 args = message.text.split()[1:]
#                 command_parts = command.split('@')
#                 command_parts.append(message.bot.username)
#
#                 if not (
#                     # command_parts[0].lower() in self.command and
#                     command_parts[1].lower() == message.bot.username.lower()
#                 ):
#                     return None
#
#                 filter_result = self.filters(update)
#                 if filter_result:
#                     return args, filter_result
#                 return False
#         return None
#
#
# @handler_decor(log_type='C')
# def callback_button(bot, update, user):
#     menu_elem = BotMenuElem.objects.filter(
#         callbacks_db__contains=update.callback_query.data,
#         is_visable=True,
#     ).first()
#     if menu_elem is None:
#         menu_elem = BotMenuElem.objects.filter(
#             empty_block=True,
#             is_visable=True,
#         ).first()
#     return bot.send_botmenuelem(update, user, menu_elem)
#
#
# class AllCallbackQueryHandler(CallbackQueryHandler):
#     def __init__(self, *args, **kwargs):
#         kwargs['callback'] = callback_button
#         super().__init__(*args, **kwargs)

