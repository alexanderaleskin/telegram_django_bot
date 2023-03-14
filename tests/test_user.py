import datetime

from telegram_django_bot.test import DJ_TestCase
from test_app.models import User
from django.conf import settings


class TestUser(DJ_TestCase):
    def setUp(self) -> None:
        user_id = settings.TELEGRAM_TEST_USER_IDS[0]
        self.user1 = User.objects.create(id=user_id, username=user_id)
        self.user2 = User.objects.create(id=1, username='1')

    def test_clear_status(self):
        self.user1.current_utrl = 'aa/bb'
        self.user1.current_utrl_context_db = '{"a": "b"}'
        self.user1.current_utrl_form_db = '{"some": "info"}'
        self.user1.save()

        self.user1.clear_status(commit=False)
        self.assertEqual('', self.user1.current_utrl)
        self.assertEqual('{}', self.user1.current_utrl_context_db)
        self.assertEqual('{}', self.user1.current_utrl_form_db)

        self.user1.refresh_from_db()
        self.assertEqual('aa/bb', self.user1.current_utrl)
        self.assertEqual('{"a": "b"}', self.user1.current_utrl_context_db)

        self.user1.clear_status()
        self.user1.refresh_from_db()
        self.assertEqual('', self.user1.current_utrl)
        self.assertEqual('{}', self.user1.current_utrl_context_db)
        self.assertEqual('{}', self.user1.current_utrl_form_db)

    def test_save_and_load_form(self):
        form_name = 'TestForm'
        cleaned_data = {
            'int': 1000,
            'float': 3.14,
            'dt': datetime.date(2000, 1, 1),
            'tm': datetime.time(10, 30),
            'dttm': datetime.datetime(2023, 1, 1, 0, 45, 10),
            'user': self.user1,
            'several_models': User.objects.all().order_by('id'),
            'string': 'abrakadabra <b> 123:00 !?',
            'list': [1, 2, 3, 'a'],
            'dict': {'1': 2, '2': 3}
        }

        self.user1.save_form_in_db(form_name, cleaned_data)
        self.assertEqual(form_name, self.user1.current_utrl_form['form_name'])

        data_for_form = cleaned_data.copy()  # for form this change is okey
        data_for_form['several_models'] = ['1', str(self.user1.pk)]
        data_for_form['user'] = self.user1.pk
        self.assertEqual(data_for_form, self.user1.current_utrl_form['form_data'])

        self.user1.save_form_in_db('TestForm2', {})
        self.assertEqual({}, self.user1.current_utrl_form['form_data'])

    def test_current_utrl_context(self):
        data = [1, 2, {'a': {'dttm': datetime.datetime(2020, 1, 1, 1)}}]
        self.user1.save_context_in_db(data)
        self.user1.save()
        self.assertEqual(data, self.user1.current_utrl_context)

        data2 = {'a': 1}
        self.user1.save_context_in_db(data2)
        self.assertEqual(data2, self.user1.current_utrl_context)

    def test_language_selection(self):
        self.assertEqual('en', self.user1.language_code)

        self.user1.telegram_language_code = 'ru'
        self.assertEqual('ru', self.user1.language_code)

        self.user1.telegram_language_code = 'de'
        self.assertEqual('de', self.user1.language_code)

        self.user1.telegram_language_code = 'fr'  # not exist in settings
        self.assertEqual('en', self.user1.language_code)
