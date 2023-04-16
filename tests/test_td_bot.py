from telegram_django_bot.test import TD_TestCase
from telegram_django_bot.telegram_lib_redefinition import InlineKeyboardButtonDJ, InlineKeyboardMarkupDJ
from telegram_django_bot.models import BotMenuElem, BotMenuElemAttrText, MESSAGE_FORMAT
from django.conf import settings

from test_app.models import User

import unittest
import telegram


@unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
class Test_TG_DJ_BOT(TD_TestCase):

    def setUp(self) -> None:
        user_id = settings.TELEGRAM_TEST_USER_IDS[0]
        self.user1 = User.objects.create(id=user_id, username=user_id)

        self.user2 = User.objects.create(id=1, username=1)


    def test_send_format_message(self):
        bot = self.test_callback_context.bot
        user_id = settings.TELEGRAM_TEST_USER_IDS[0]

        message, __ = bot.send_format_message(
            text='simple message',
            chat_id=user_id
        )

        callback_params = {'data': 'just_for_update'}
        update = self.create_update({'message_id': message.message_id}, callback_params)

        message, __ = bot.send_format_message(
            text='simple <b> message',  # without closed </b> -- checked that parse_mode is changed
            update=update,
            reply_markup=InlineKeyboardMarkupDJ([[InlineKeyboardButtonDJ('test', callback_data='test')]]),
            disable_web_page_preview=True,
            parse_mode='Markdown'
        )

        photo1 = open('media/pic1.png', 'rb')
        update = self.create_update(message.to_dict(), callback_params)
        message, __ = bot.send_format_message(
            message_format=MESSAGE_FORMAT.PHOTO,
            media_files_list=[photo1],
            update=update,
        )

        # photo1 = InputMediaPhoto(open('media/pic1.png', 'rb'))
        # photo2 = InputMediaPhoto(open('media/pic2.jpg', 'rb'))
        # update = self.create_update(message.to_dict(), callback_params)
        # message, __ = bot.send_format_message(
        #     message_format=MESSAGE_FORMAT.GROUP_MEDIA,
        #     media_files_list=[photo1, photo2],
        #     update=update,
        # )

        doc = open('media/game.gif', 'rb')
        message, __ = bot.send_format_message(
            text='test',
            chat_id=user_id,
            message_format=MESSAGE_FORMAT.DOCUMENT,
            media_files_list=[doc],
            disable_web_page_preview=True,
        )

        # todo: add check for all formats

    def test_send_botmenuelem(self):
        bme = BotMenuElem.objects.create(
            message_format=MESSAGE_FORMAT.PHOTO,
            message='bme send test',
            buttons_db='[[{"text":"button", "url": "google.com"}]]',
            media='media/pic1.png'
        )
        BotMenuElemAttrText.objects.filter(
            bot_menu_elem=bme,
            default_text='bme send test',
            language_code='ru'
        ).update(translated_text='bme отправленное сообщение')

        bot = self.test_callback_context.bot

        message = bot.send_botmenuelem(None, self.user1, None)
        self.assertEqual(
            'Oops! It seems that an error has occurred, please write to support (contact in bio)!',
            message.text,
        )
        self.assertIsNone(bme.telegram_file_code)

        message = bot.send_botmenuelem(None, self.user1, bme)
        self.assertEqual(
            'bme send test',
            message.caption,
        )
        self.assertIsNotNone(bme.telegram_file_code)

        self.user1.telegram_language_code = 'ru'
        self.user1.save()
        update = self.create_update(message.to_dict(), {'data': 'just_for_update'})
        message = bot.send_botmenuelem(update, self.user1, bme)
        self.assertEqual(
            'bme отправленное сообщение',
            message.caption,
        )

        bme.refresh_from_db()



    def test_edit_or_send(self):
        bot = self.test_callback_context.bot
        user_id = settings.TELEGRAM_TEST_USER_IDS[0]

        message = bot.edit_or_send(
            None,
            'test mess',
            chat_id=user_id
        )

        callback_params = {'data': 'just_for_update'}

        update = self.create_update(message.to_dict(), callback_params)
        message = bot.edit_or_send(
            update,
            'test mess 2',
            buttons=[],
        )

        update = self.create_update(message.to_dict(), callback_params)
        message = bot.edit_or_send(
            update,
            'test mess 3',
            buttons=[
                [InlineKeyboardButtonDJ('button 1', url='google.com')],
                [
                    InlineKeyboardButtonDJ('button 2', callback_data='aaa'),
                    InlineKeyboardButtonDJ('button 3 😄', callback_data='bbb'),
                ]
            ],
        )

        update = self.create_update(message.to_dict())
        message = bot.edit_or_send(
            update,
            'test mess 4',
            reply_to_message_id=message.message_id,
        )


        update = self.create_update(message.to_dict(), callback_params)
        message = bot.edit_or_send(
            update,
            'test mess <b> 5',
            disable_notification=True,
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=20,
            only_send=True,
        )

    def test_task_send_message_handler(self):
        bot = self.test_callback_context.bot

        func_args = []
        func_kwargs = {
            'text': 'test',
            'chat_id': self.user1.id,
        }

        is_sent, res_mess = bot.task_send_message_handler(
            self.user1,
            bot.send_format_message,
            func_args,
            func_kwargs,
        )
        self.assertTrue(is_sent)

        func_kwargs['chat_id'] = self.user2.id
        is_sent, res_mess = bot.task_send_message_handler(
            self.user2,
            bot.send_format_message,
            func_args,
            func_kwargs,
        )
        self.assertFalse(is_sent)
        self.assertFalse(self.user2.is_active)


        # add translation check