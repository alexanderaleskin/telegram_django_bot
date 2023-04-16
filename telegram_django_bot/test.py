import logging

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from telegram import Update, Message, Chat, User as TelegramAPIUser, CallbackQuery
from telegram_django_bot.routing import RouterCallbackMessageCommandHandler
# from telegram.utils.types import JSONDict, ODVInput
# from telegram.utils.helpers import DEFAULT_NONE
# from typing import Union

from .tg_dj_bot import TG_DJ_Bot
# import asyncio


test_bot = TG_DJ_Bot(token=settings.TELEGRAM_TOKEN)
if hasattr(settings, 'TELEGRAM_TEST_USER_IDS'):
    TELEGRAM_TEST_USER_IDS = settings.TELEGRAM_TEST_USER_IDS
    for user_id in TELEGRAM_TEST_USER_IDS:
        try:
            res = test_bot.send_message(user_id, 'ping')

            # if asyncio.iscoroutine(res):
            #     asyncio.run(res)

        except Exception as error:
            logging.error(
                f'the error {error} occurred while sending test message to TELEGRAM_TEST_USER_ID={user_id} '
                f'by bot {test_bot.id}. Please, check details'
            )
else:
    TELEGRAM_TEST_USER_IDS = []
    logging.warning('TELEGRAM_TEST_USER_IDS is not set in settings. Set it or specify user in each test functions')


class TestCallbackContext:
    bot = test_bot


class DJ_TestCase(TestCase):
    pass


class TD_TestCase(DJ_TestCase):
    # test_bot = test_bot
    # test_callback_context = TestCallbackContext()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.test_callback_context = TestCallbackContext()
        self.rc_mch = RouterCallbackMessageCommandHandler()
        self.handle_update = lambda update: self.rc_mch.handle_update(
            update, 'some_str', 'some_str', self.test_callback_context
        )

    def create_update(self, message_kwargs: dict = None, callback_kwargs: dict = None, user_id=None,):
        if user_id is None and len(TELEGRAM_TEST_USER_IDS):
            user_id = TELEGRAM_TEST_USER_IDS[0]

        if user_id is None:
            raise ValueError('the user_id (or TELEGRAM_TEST_USER_IDS) should be set for creating Update model')

        chat = Chat(id=user_id, type='private')
        user = TelegramAPIUser(id=user_id, first_name='test', is_bot=False)

        message_kwargs = dict(message_kwargs) if message_kwargs else {}
        message_kwargs['message_id'] = message_kwargs.get('message_id', 1)
        message_kwargs['date'] = message_kwargs.get('message_id', timezone.now())
        message_kwargs['chat'] = message_kwargs.get('chat', chat)
        message_kwargs['from_user'] = message_kwargs.get('from_user', user)
        message = Message(**message_kwargs)

        if callback_kwargs:
            callback_kwargs = dict(callback_kwargs)
            callback_kwargs['id'] = callback_kwargs.get('id', 1)
            callback_kwargs['from_user'] = callback_kwargs.get('from_user', user)
            callback_kwargs['message'] = callback_kwargs.get('message', message)
            callback_kwargs['chat_instance'] = callback_kwargs.get('chat_instance', '1')
            callback = CallbackQuery(**callback_kwargs)
        else:
            callback = None

        update_kwargs = {
            'update_id': 1
        }
        if callback:
            update_kwargs['callback_query'] = callback
        else:
            update_kwargs['message'] = message

        return Update(**update_kwargs)







