from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core import validators
import random
from django.utils import timezone
from model_utils import FieldTracker
import json
# from timezone_field import TimeZoneField
from django.conf import settings
from django.db.models import QuerySet
from django.core.serializers.json import DjangoJSONEncoder
import datetime


class TelegramDjangoJsonDecoder(json.JSONDecoder):
    def decode(self, s, *args, **kwargs):
        dt_object = None
        try:
            dt_object = datetime.datetime.fromisoformat(s)
        except ValueError:
            try:
                dt_object = datetime.date.fromisoformat(s)
            except ValueError:
                try:
                    dt_object = datetime.time.fromisoformat(s)
                except ValueError:
                    pass

        if dt_object is None:
            return super().decode(s, *args, **kwargs)
        else:
            return dt_object



class MESSAGE_FORMAT:
    TEXT = 'T'
    PHOTO = 'P'
    DOCUMENT = 'D'
    AUDIO = 'A'
    VIDEO = 'V'
    GIF = 'G'
    GROUP_MEDIA = 'GM'

    MESSAGE_FORMATS = (
        (TEXT, 'текст'),
        (PHOTO, 'фото'),
        (DOCUMENT, 'документ'),
        (AUDIO, 'аудио'),
        (VIDEO, 'видео'),
        (GIF, 'гифка/анимация'),
        (GROUP_MEDIA, 'группа медиа'),
    )


class ModelwithTimeManager(models.Manager):
    def bot_filter_active(self, *args, **kwargs):
        return self.filter(dttm_deleted__isnull=True, *args, **kwargs)


class AbstractActiveModel(models.Model):
    dttm_added = models.DateTimeField(default=timezone.now)
    dttm_deleted = models.DateTimeField(null=True, blank=True)

    objects = ModelwithTimeManager()

    class Meta:
        abstract = True


class TelegramAbstractActiveModel(AbstractActiveModel):
    message_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        abstract = True


def _seed_code():
    return random.randint(0, 100)


class TelegramUser(AbstractUser):
    id = models.BigIntegerField(primary_key=True)  # telegram id is id for models
    seed_code = models.IntegerField(default=_seed_code)
    telegram_username = models.CharField(max_length=64, null=True, blank=True)

    timezone = models.DurationField(default=timezone.timedelta(hours=3))

    current_utrl = models.CharField(max_length=32, default='', blank=True) # todo: add verify comparisson current_utrl and current_utrl_context_db/current_utrl_form_db
    current_utrl_code_dttm = models.DateTimeField(null=True, blank=True)
    current_utrl_context_db = models.CharField(max_length=4096, default='{}', blank=True)
    # form structure {'form_name': '', 'form_data': {}}
    current_utrl_form_db = models.CharField(max_length=4096, default='{}', blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"U({self.id} {self.telegram_username} {self.first_name})"

    @property
    def current_utrl_form(self):
        if not hasattr(self, '_current_utrl_form'):
            self._current_utrl_form = json.loads(self.current_utrl_form_db, cls=TelegramDjangoJsonDecoder)
        return self._current_utrl_form

    @property
    def current_utrl_context(self):
        if not hasattr(self, '_current_utrl_context'):
            self._current_utrl_context = json.loads(self.current_utrl_context_db, cls=TelegramDjangoJsonDecoder)
        return self._current_utrl_context

    def save_form_in_db(self, form_name, form_data, do_save=True):
        db_form_data = {}
        # import pdb;pdb.set_trace()

        for key, value in form_data.items():
            print(key, value)
            if issubclass(value.__class__, models.Model):
                db_value = value.pk
            elif (type(value) in [list, QuerySet]) and all(map(lambda x: issubclass(x.__class__, models.Model), value)):
                db_value = list([str(x.pk) for x in value])
            else:
                db_value = value

            db_form_data[key] = db_value

        self.current_utrl_form_db = json.dumps({
            'form_name': form_name,
            'form_data': db_form_data,
        })
        if do_save:
            self.save()

        if hasattr(self, '_current_utrl_context'):
            delattr(self, '_current_utrl_context')

    def clear_status(self, commit=True):
        self.current_utrl = ''
        self.current_utrl_code_dttm = None
        self.current_utrl_context_db = '{}'
        self.current_utrl_form_db = '{}'
        if commit:
            self.save()


class TeleDeepLink(models.Model):
    title = models.CharField(max_length=64, default='', blank=True)
    price = models.FloatField(null=True, blank=True)
    link = models.CharField(max_length=64, validators=[validators.RegexValidator(
        '^[a-zA-Z0-9_-]+$',
        'Телеграм принимает только буквы, цифры и знаки - _ ',
    )])
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)


class ActionLog(models.Model):
    """
    Лог активностей пользователей
    """

    dttm = models.DateTimeField(auto_now_add=True, db_index=True)
    type = models.CharField(max_length=32)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return '({}, {}, {})'.format(self.user_id, self.dttm, self.type)


class BotMenuElem(models.Model):
    """
    actually subscribe, not payment
    """

    command = models.CharField(
        max_length=32, unique=True, null=True, blank=True,
        help_text='Команда бота, по которой можно вызвать этот блок меню'
    )

    empty_block = models.BooleanField(default=False,
                                      help_text='если забыли и нет события ловяшего коллбек, то это покажет')
    is_visable = models.BooleanField(
        default=True,
        help_text='Отображать ли этот блок меню пользователям (можно скрыть и не удалять для удобства)'
    )

    callbacks_db = models.TextField(
        null=True, blank=True,
        help_text='список регулярных выражений (пока только явный список) для коллбеков, которые вызывают это блок меню'
    )

    forward_message_id = models.IntegerField(null=True, blank=True)
    forward_chat_id = models.IntegerField(null=True, blank=True)

    message_format = models.CharField(max_length=2, choices=MESSAGE_FORMAT.MESSAGE_FORMATS, default=MESSAGE_FORMAT.TEXT)
    message = models.TextField(help_text='Текстовое сообщение')
    buttons_db = models.TextField(help_text='InlineKeyboardMarkup список кнопок, ({"text": , "url" or "callback_data"})', null=True, blank=True)
    media = models.FileField(help_text='Файл приложение к сообщению', null=True, blank=True)
    telegram_file_code = models.CharField(
        max_length=512, null=True, blank=True,
        help_text='Код файла в телеграмме (удалить при замене файла)'
    )

    def __str__(self):
        return f"BME ({self.id}) - { self.command or self.message[:32]}"

    # def save(self, *args, **kwargs):
    #     bot = telegram.Bot(TELEGRAM_TOKEN)

    @property
    def buttons(self):
        if not hasattr(self, '_buttons'):
            self._buttons = json.loads(self.buttons_db)

        return self._buttons

    @property
    def callbacks(self):
        if not hasattr(self, '_callbacks'):
            self._callbacks = json.loads(self.callbacks_db)

        return self._callbacks


class Trigger(AbstractActiveModel):

    name = models.CharField(max_length=512, unique=True)
    condition_db = models.TextField(help_text='''
    {
        seeds: [1, 2, 3, 4, 5],
        'amount': [{
            'gte': 5,
            'type__contains': 'dd',  // type__in, type
            'duration': '7d'
        }]
    }
    ''')

    min_duration = models.DurationField(help_text='минимальный период, в который может быть 1 уведомление '
                                                  'для пользователя данного типа')
    priority = models.IntegerField(default=1, help_text='чем больше тем в первую очередь будут выполняться')

    botmenuelem = models.ForeignKey(BotMenuElem, on_delete=models.PROTECT, help_text='какое сообщение по тригеру показываем')

    @property
    def condition(self):
        if not hasattr(self, '_condition'):
            self._condition = json.loads(self.condition_db)

        return self._condition

    @staticmethod
    def get_timedelta(delta_string:str):
        days = 0
        hours = 0
        for part in delta_string.split():
            if 'd' in part:
                days = float(part.replace('d', ''))
            elif 'h' in part:
                days = float(part.replace('h', ''))
            else:
                raise ValueError(f'unknown format {part}')

        return timezone.timedelta(days=days, hours=hours)



class UserTrigger(TelegramAbstractActiveModel):
    trigger = models.ForeignKey(Trigger, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    is_sent = models.BooleanField(default=False)
