from telegram_django_bot.test import TD_TestCase
from telegram_django_bot.models import ActionLog, TeleDeepLink, BotMenuElem
from telegram_django_bot.utils import handler_decor
from django.conf import settings
from test_app.models import User

import unittest
import telegram


@handler_decor(log_type='C')
def normal_func(bot, update, user):
    return


@handler_decor(log_type='F')
def func_with_error(bot, update, user):
    raise ArithmeticError('error :(')


class TestHandlerDecor(TD_TestCase):
    def setUp(self) -> None:
        self.user_id = settings.TELEGRAM_TEST_USER_IDS[0]
        self.update = self.create_update({'text': '/start deeplink'})

    def test_user_creating(self):
        normal_func(self.update, self.test_callback_context)

        self.assertEqual(self.user_id, User.objects.filter().get().id)
        self.assertEqual(1, TeleDeepLink.objects.filter(link='deeplink').count())
        self.assertEqual(3, ActionLog.objects.count())
        self.assertEqual(1, ActionLog.objects.filter(user_id=self.user_id, type='/start deeplink').count())

    def test_for_exist_user(self):
        User.objects.create(id=self.user_id, username=self.user_id)

        normal_func(self.update, self.test_callback_context)
        self.assertEqual(0, TeleDeepLink.objects.all().count())
        self.assertEqual(2, ActionLog.objects.count())

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_error(self):
        error = None
        try:
            func_with_error(self.update, self.test_callback_context)
        except ArithmeticError as err:
            error = err

        self.assertIsNotNone(error)
        self.assertEqual(3, ActionLog.objects.count())
        self.assertEqual(1, ActionLog.objects.filter(user_id=self.user_id, type='func_with_error').count())


    # def test_language(self):
    #     # todo:
    #     pass