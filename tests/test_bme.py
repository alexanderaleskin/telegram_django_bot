import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram_django_bot.test import TD_TestCase
from telegram_django_bot.models import BotMenuElem, BotMenuElemAttrText
from telegram_django_bot.routing import all_command_bme_handler, all_callback_bme_handler
from test_app.models import User
from django.conf import settings
import unittest


class BMEInitData:
    def setup_data(self, with_users=False, with_translation=False):
        self.bme_start = BotMenuElem.objects.create(
            command='start',
            callbacks_db='["start"]',
            message='Aloha, world!',
            buttons_db='[[{"text": "start", "callback_data": "start"}]]'
        )
        self.bme_2 = BotMenuElem.objects.create(
            command='second',
            callbacks_db='["second"]',
            message='Some message',
            buttons_db='['
                       '[{"text": "button 1", "callback_data": "button1"}],'
                       '[{"text": "button 2", "callback_data": "button2"}]'
                       ']'
        )
        if with_users:
            user_id = settings.TELEGRAM_TEST_USER_IDS[0]
            self.user = User.objects.create(id=user_id, username=user_id)

        if with_translation:
            BotMenuElemAttrText.objects.filter(
                bot_menu_elem=self.bme_start,
                language_code='ru',
                default_text='Aloha, world!'
            ).update(translated_text='Алоха, мир!')

            BotMenuElemAttrText.objects.filter(
                bot_menu_elem=self.bme_start,
                language_code='ru',
                default_text='start'
            ).update(translated_text='старт')


class TestBMEModels(TD_TestCase, BMEInitData):

    def setUp(self) -> None:
        self.setup_data()

    def test_translation_creating(self):
        self.assertEqual(10, BotMenuElemAttrText.objects.count())  # german + russian
        self.assertEqual(5, BotMenuElemAttrText.objects.filter(language_code='ru').count())
        self.assertEqual(4, BotMenuElemAttrText.objects.filter(bot_menu_elem=self.bme_start).count())
        self.assertEqual(6, BotMenuElemAttrText.objects.filter(bot_menu_elem=self.bme_2).count())

        self.bme_2.message = 'new message'
        self.bme_2.save()
        self.assertEqual(8, BotMenuElemAttrText.objects.filter(bot_menu_elem=self.bme_2).count())

        self.bme_2.save()
        self.assertEqual(8, BotMenuElemAttrText.objects.filter(bot_menu_elem=self.bme_2).count())

        BotMenuElemAttrText.objects.filter(bot_menu_elem=self.bme_2).delete()
        self.bme_2.save()
        self.assertEqual(6, BotMenuElemAttrText.objects.filter(bot_menu_elem=self.bme_2).count())

        self.bme_2.delete()
        self.assertEqual(4, BotMenuElemAttrText.objects.count())

    def test_translation_getting(self):
        self.assertEqual('Aloha, world!', self.bme_start.get_message())
        self.assertEqual('Some message', self.bme_2.get_message())

        should_be = InlineKeyboardMarkup([[InlineKeyboardButton('start', callback_data='start')]])
        self.assertEqual(should_be.to_dict(), InlineKeyboardMarkup(self.bme_start.get_buttons()).to_dict())

        self.assertEqual('Aloha, world!', self.bme_start.get_message('ru'))
        self.assertEqual(should_be.to_dict(), InlineKeyboardMarkup(self.bme_start.get_buttons('ru')).to_dict())

        should_be = InlineKeyboardMarkup([
            [InlineKeyboardButton('button 1', callback_data='button1')],
            [InlineKeyboardButton('button 2', callback_data='button2')],
        ])
        self.assertEqual(should_be,  InlineKeyboardMarkup(self.bme_2.get_buttons()))


        BotMenuElemAttrText.objects.filter(
            bot_menu_elem=self.bme_start,
            language_code='ru',
            default_text='Aloha, world!'
        ).update(translated_text='Алоха, мир!')

        BotMenuElemAttrText.objects.filter(
            bot_menu_elem=self.bme_start,
            language_code='ru',
            default_text='start'
        ).update(translated_text='старт')

        self.assertEqual('Алоха, мир!', self.bme_start.get_message('ru'))
        should_be = InlineKeyboardMarkup([[InlineKeyboardButton('старт', callback_data='start')]])
        self.assertEqual(should_be.to_dict(), InlineKeyboardMarkup(self.bme_start.get_buttons('ru')).to_dict())

        self.assertEqual('Aloha, world!', self.bme_start.get_message('de'))
        should_be = InlineKeyboardMarkup([[InlineKeyboardButton('start', callback_data='start')]])
        self.assertEqual(should_be.to_dict(), InlineKeyboardMarkup(self.bme_start.get_buttons('de')).to_dict())


@unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
class TestBMEHandlers(TD_TestCase, BMEInitData):
    def setUp(self) -> None:
        self.setup_data(True, True)

    def test_command_handler(self):
        message = all_command_bme_handler(self.create_update({'text': '/start'}), self.test_callback_context)
        self.assertEqual('Aloha, world!', message.text)

        message = all_command_bme_handler(self.create_update({'text': '/second'}), self.test_callback_context)
        self.assertEqual('Some message', message.text)

        self.user.telegram_language_code = 'ru'
        self.user.save()
        message = all_command_bme_handler(self.create_update({'text': '/start'}), self.test_callback_context)
        self.assertEqual('Алоха, мир!', message.text)

        self.user.telegram_language_code = 'de'
        self.user.save()
        message = all_command_bme_handler(self.create_update({'text': '/start'}), self.test_callback_context)
        self.assertEqual('Aloha, world!', message.text)

    def test_command_handler_special_start(self):
        message = all_command_bme_handler(self.create_update({'text': '/start special'}), self.test_callback_context)
        self.assertEqual('Aloha, world!', message.text)

        self.bme_extra = BotMenuElem.objects.create(
            command='start special',
            callbacks_db='[]',
            message='extra start',
            buttons_db='[[{"text": "start", "callback_data": "start"}]]'
        )

        message = all_command_bme_handler(self.create_update({'text': '/start special'}), self.test_callback_context)
        self.assertEqual('extra start', message.text)

    def test_command_handler_no_command(self):
        message = all_command_bme_handler(self.create_update({'text': '/not_exist'}), self.test_callback_context)
        self.assertEqual(
            'Oops! It seems that an error has occurred, please write to support (contact in bio)!',
            message.text
        )

    def test_callback_handler(self):
        message = self.test_callback_context.bot.send_message(self.user.id, 'for test')
        message_params = {'message_id': message.message_id}
        callback_params = {'data': 'start'}

        message = all_callback_bme_handler(
            self.create_update(message_params, callback_params),
            self.test_callback_context
        )
        self.assertEqual('Aloha, world!', message.text)



