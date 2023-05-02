import telegram

from telegram_django_bot.routing import telegram_resolve, telegram_reverse, RouterCallbackMessageCommandHandler
from telegram_django_bot.test import TD_TestCase
from telegram_django_bot.models import BotMenuElem, ActionLog
from django.urls.exceptions import NoReverseMatch
from django.conf import settings

# import os, sys
# sys.path.append(os.path.dirname(__file__))
# print(sys.path, os.path.dirname(__file__))

from test_app.models import User, Category
from test_app.views import CategoryViewSet, EntityViewSet
from test_app.handlers import me
import unittest

class TestTelegramResolve(TD_TestCase):
    def test_exist(self):
        res = telegram_resolve('cat/se')
        self.assertEqual(CategoryViewSet, res.func)

        res = telegram_resolve('/cat/', utrl_conf='test_app.utrls')
        self.assertEqual(CategoryViewSet, res.func)

        res = telegram_resolve('cat/up&1&2&3')
        self.assertEqual(CategoryViewSet, res.func)

        res = telegram_resolve('ent/cr&some_name&cat/')
        self.assertEqual(EntityViewSet, res.func)

        res = telegram_resolve('start')
        self.assertEqual(me, res.func)


    def test_not_exist(self):
        self.assertIsNone(telegram_resolve('abracadabra'))
        self.assertIsNone(telegram_resolve('cat'))
        self.assertIsNone(telegram_resolve('startstart/'))



class TestTelegramReverse(TD_TestCase):
    def test_exist(self):
        res = telegram_reverse('CategoryViewSet')
        self.assertEqual('cat/', res)

        res = telegram_reverse('EntityViewSet')
        self.assertEqual('ent/', res)

        res = telegram_reverse('self_info')
        self.assertEqual('me', res)

    def test_not_exist(self):
        catched = False
        try:
            telegram_reverse('abracadabra')
        except NoReverseMatch:
            catched = True

        self.assertTrue(catched)



@unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
class TestRouterCallbackMessageCommandHandler(TD_TestCase):
    def setUp(self) -> None:
        self.bme = BotMenuElem.objects.create(
            message='test',
            command='command'

        )

    # 'dispatcher', 'check_result' -- unnecessary args
    def test_command(self):
        rc_mch = RouterCallbackMessageCommandHandler()
        update = self.create_update({'text': '/start'})
        self.assertTrue(rc_mch.check_update(update))

        res = rc_mch.handle_update(update, 'dispatcher', 'check_result', self.test_callback_context)
        self.assertEqual(telegram.Message, type(res))
        self.assertEqual(1, ActionLog.objects.filter(type='me').count())


    def test_bme_command(self):
        rc_mch = RouterCallbackMessageCommandHandler()
        update = self.create_update({'text': '/test'})
        self.assertTrue(rc_mch.check_update(update))

        res = rc_mch.handle_update(update, 'dispatcher', 'check_result', self.test_callback_context)
        self.assertEqual(telegram.Message, type(res))

        rc_mch = RouterCallbackMessageCommandHandler(only_utrl=True)
        self.assertFalse(rc_mch.check_update(update))
        self.assertEqual(1, ActionLog.objects.filter(type='/test').count())


    def test_command_not_exist(self):
        rc_mch = RouterCallbackMessageCommandHandler()
        update = self.create_update({'text': '/abra'})
        self.assertTrue(rc_mch.check_update(update))

        res = rc_mch.handle_update(update, 'dispatcher', 'check_result', self.test_callback_context)
        self.assertEqual(
            'Oops! It seems that an error has occurred, please write to support (contact in bio)!',
            res.text
        )
        self.assertEqual(1, ActionLog.objects.filter(type='/abra').count())


    def test_callback(self):
        rc_mch = RouterCallbackMessageCommandHandler()

        message = self.test_callback_context.bot.send_message(
            chat_id=settings.TELEGRAM_TEST_USER_IDS[0],
            text='some text'
        )
        callback_params = {'data': 'start'}

        update = self.create_update(message.to_dict(), callback_params)
        self.assertTrue(rc_mch.check_update(update))

        res = rc_mch.handle_update(update, 'dispatcher', 'check_result', self.test_callback_context)
        self.assertEqual(1, ActionLog.objects.filter(type='me').count())
        self.assertEqual(telegram.Message, type(res))

    def test_callback_viewset(self):
        rc_mch = RouterCallbackMessageCommandHandler()

        message = self.test_callback_context.bot.send_message(
            chat_id=settings.TELEGRAM_TEST_USER_IDS[0],
            text='some text'
        )
        callback_params = {'data': 'cat/cr'}

        update = self.create_update(message.to_dict(), callback_params)
        self.assertTrue(rc_mch.check_update(update))

        res = rc_mch.handle_update(update, 'dispatcher', 'check_result', self.test_callback_context)
        self.assertEqual(1, ActionLog.objects.filter(type='cat/cr').count())
        self.assertEqual(telegram.Message, type(res))

    def test_callback_user_utrl(self):
        rc_mch = RouterCallbackMessageCommandHandler()
        update = self.create_update({'text': 'category_name'})
        user_id = settings.TELEGRAM_TEST_USER_IDS[0]
        user = User.objects.create(
            id=user_id,
            username=user_id,
            current_utrl='cat/cr&name'
        )

        self.assertTrue(rc_mch.check_update(update))

        res = rc_mch.handle_update(update, 'dispatcher', 'check_result', self.test_callback_context)

        self.assertEqual(1, Category.objects.count())
        self.assertEqual(1, ActionLog.objects.filter(type='cat/cr').count())
        self.assertEqual(telegram.Message, type(res))

    def test_callback_bme(self):
        rc_mch = RouterCallbackMessageCommandHandler()

        message = self.test_callback_context.bot.send_message(
            chat_id=settings.TELEGRAM_TEST_USER_IDS[0],
            text='some text'
        )
        callback_params = {'data': 'test'}
        update = self.create_update(message.to_dict(), callback_params)
        self.assertTrue(rc_mch.check_update(update))

        res = rc_mch.handle_update(update, 'dispatcher', 'check_result', self.test_callback_context)
        self.assertEqual(1, ActionLog.objects.filter(type='test').count())
        self.assertEqual(telegram.Message, type(res))

        rc_mch = RouterCallbackMessageCommandHandler(only_utrl=True)
        self.assertFalse(rc_mch.check_update(update))
        self.assertEqual(1, ActionLog.objects.filter(type='test').count())


