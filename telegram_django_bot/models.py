import logging

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core import validators
import random
from django.utils import timezone
import json
from django.conf import settings
from django.db.models import QuerySet
from django.core.serializers.json import DjangoJSONEncoder
import datetime
from django.utils.translation import gettext_lazy as _
from telegram import InlineKeyboardButton  # no lazy text so standart possible to use


class TelegramDjangoJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super(TelegramDjangoJsonDecoder, self).__init__(*args, object_hook=self.object_hook_decoder, **kwargs)

    def object_hook_decoder(self, sub_dict, *args, **kwargs):
        # so it works only for dictionary data (if datetime is in list it will not be worked)
        for key in sub_dict.keys():
            value = sub_dict[key]
            dt_object = None
            if type(value) == str:
                try:
                    dt_object = datetime.time.fromisoformat(value)
                except ValueError:
                    try:
                        dt_object = datetime.date.fromisoformat(value)
                    except ValueError:
                        try:
                            dt_object = datetime.datetime.fromisoformat(value)
                        except ValueError:
                            pass

                if dt_object:
                    sub_dict[key] = dt_object

        return sub_dict


class MESSAGE_FORMAT:
    TEXT = 'T'
    PHOTO = 'P'
    DOCUMENT = 'D'
    AUDIO = 'A'
    VIDEO = 'V'
    GIF = 'G'
    VOICE = 'TV'
    VIDEO_NOTE = 'VN'
    STICKER = 'S'
    LOCATION = 'L'
    GROUP_MEDIA = 'GM'

    MESSAGE_FORMATS = (
        (TEXT, _('Text')),
        (PHOTO, _('Image')),
        (DOCUMENT, _('Document')),
        (AUDIO, _('Audio')),
        (VIDEO, _('Video')),
        (GIF, _('GIF/animation')),
        (VOICE, _('Voice')),
        (VIDEO_NOTE, _('Video note')),
        (STICKER, _('Sticker')),
        (LOCATION, _('Location')),
        (GROUP_MEDIA, _('Media Group')),
    )

    ALL_FORMATS = (elem[0] for elem in MESSAGE_FORMATS)


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
    telegram_language_code = models.CharField(max_length=16, default='en')  # could be with dialects

    timezone = models.DurationField(default=timezone.timedelta(hours=3))

    current_utrl = models.CharField(max_length=64, default='', blank=True) # todo: add verify comparisson current_utrl and current_utrl_context_db/current_utrl_form_db
    current_utrl_code_dttm = models.DateTimeField(null=True, blank=True)
    current_utrl_context_db = models.CharField(max_length=4096, default='{}', blank=True)

    # form structure {'form_name': '', 'form_data': {}}
    current_utrl_form_db = models.CharField(max_length=4096, default='{}', blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"U({self.id}, {self.telegram_username or '-'}, {self.first_name or '-'})"

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

        for key, value in form_data.items():
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
        }, cls=DjangoJSONEncoder)
        if do_save:
            self.save()

        if hasattr(self, '_current_utrl_form'):
            delattr(self, '_current_utrl_form')

    def save_context_in_db(self, context, do_save=True):
        self.current_utrl_context_db = json.dumps(context, cls=DjangoJSONEncoder)
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

        for attr in ['_current_utrl_context', '_current_utrl_form']:
            if hasattr(self, attr):
                delattr(self, attr)


    @property
    def language_code(self):
        if self.telegram_language_code in map(lambda x: x[0], settings.LANGUAGES):
            return self.telegram_language_code
        return settings.LANGUAGE_CODE

    def save(self, *args, **kwargs):
        if self.id is None and self.is_staff:
            id_num = 1
            while self.__class__.objects.filter(id=id_num).count():
                id_num += 1

            self.id = id_num

            logging.warning(f"Try to save user without ID. For staff the smallest unused ID will be used: {id_num}")

        return super(TelegramUser, self).save(*args, **kwargs)
            

class TeleDeepLink(models.Model):
    title = models.CharField(max_length=64, default='', blank=True)
    price = models.FloatField(null=True, blank=True)
    link = models.CharField(max_length=64, validators=[validators.RegexValidator(
        '^[a-zA-Z0-9_-]+$',
        _('Telegram is only accepted letters, numbers and signs - _'),
    )])
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def __str__(self):
        return f'TDL({self.id}, {self.link})'

class ActionLog(models.Model):
    """
    User actions logs
    """

    dttm = models.DateTimeField(auto_now_add=True, db_index=True)
    type = models.CharField(max_length=64)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return 'AL({}, {}, {})'.format(self.user_id, self.dttm, self.type)


class BotMenuElem(models.Model):
    """

    """

    command = models.TextField(  # for multichoice start
        null=True, blank=True,  # todo: add manual check
        help_text=_('Bot command that can call this menu block. Add 1 command per row')
    )

    empty_block = models.BooleanField(
        default=False,
        help_text=_('This block will be shown if there is no catching callback')
    )
    is_visable = models.BooleanField(
        default=True,
        help_text=_('Whether to display this menu block to users (can be hidden and not deleted for convenience)')
    )

    callbacks_db = models.TextField(
        default='[]',
        help_text=_(
            'List of regular expressions (so far only an explicit list) for callbacks that call this menu block. '
            'For example, list ["data", "callback2"] will catch the clicking InlineKeyboardButtons with callback_data "data" or "callback2"'
        )
    )

    forward_message_id = models.IntegerField(null=True, blank=True)
    forward_chat_id = models.IntegerField(null=True, blank=True)

    message_format = models.CharField(max_length=2, choices=MESSAGE_FORMAT.MESSAGE_FORMATS, default=MESSAGE_FORMAT.TEXT)
    message = models.TextField(help_text=_('Text message'))
    buttons_db = models.TextField(
        default='[]',
        help_text=_(
            'InlineKeyboardMarkup buttons structure (double list of dict), where each button(dict) has next format: '
            '{"text": "text", "url": "google.com"} or {"text":"text", "callback_data": "data"})'
        )
    )
    media = models.FileField(help_text=_('File attachment to the message'), null=True, blank=True)
    telegram_file_code = models.CharField(
        max_length=512, null=True, blank=True,
        help_text=_('File code in telegram (must be deleted when replacing file)')
    )

    def __str__(self):
        return f"BME({self.id}, { self.command[:32] if self.command else self.message[:32]})"

    def save(self, *args, **kwargs):
        # bot = telegram.Bot(TELEGRAM_TOKEN)
        
        super(BotMenuElem, self).save(*args, **kwargs)

        # check and create new models for translation
        if settings.USE_I18N and len(settings.LANGUAGES):
            language_codes = set(map(lambda x: x[0], settings.LANGUAGES))
            if settings.LANGUAGE_CODE in language_codes:
                language_codes.remove(settings.LANGUAGE_CODE)

            get_existed_language_codes = lambda text: set(BotMenuElemAttrText.objects.filter(
                language_code__in=language_codes,
                bot_menu_elem_id=self.id,
                default_text=text,
            ).values_list('language_code', flat=True))

            BotMenuElemAttrText.objects.bulk_create([
                BotMenuElemAttrText(language_code=language_code, default_text=self.message, bot_menu_elem_id=self.id)
                for language_code in language_codes - get_existed_language_codes(self.message)
            ])

            for row_elem in self.buttons:
                for elem in row_elem:
                    if text := elem.get('text'):
                        BotMenuElemAttrText.objects.bulk_create([
                            BotMenuElemAttrText(language_code=language_code, default_text=text, bot_menu_elem_id=self.id)
                            for language_code in language_codes - get_existed_language_codes(text)
                        ])

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

    def get_message(self, language='en'):
        get_translate_model = None
        if language != settings.LANGUAGE_CODE:
            get_translate_model = BotMenuElemAttrText.objects.filter(
                language_code=language,
                bot_menu_elem_id=self.id,
                default_text=self.message,
                translated_text__isnull=False,
            ).first()
        text = get_translate_model.translated_text if get_translate_model else self.message
        return text

    def get_buttons(self, language='en'):
        # todo: rewrite with 1 request to db (default_text__in=...)

        get_translate_model = lambda text: BotMenuElemAttrText.objects.filter(
            language_code=language,
            bot_menu_elem_id=self.id,
            default_text=text,
            translated_text__isnull=False,
        ).first()

        need_translation = language != settings.LANGUAGE_CODE and settings.USE_I18N
        buttons = []

        for row_elem in self.buttons:
            row_buttons = []
            for item_in_row in row_elem:
                elem = dict(item_in_row)
                if elem.get('text') and need_translation and (translate_model := get_translate_model(elem['text'])):
                    elem['text'] = translate_model.translated_text
                row_buttons.append(InlineKeyboardButton(**elem))

            buttons.append(row_buttons)
        return buttons


class BotMenuElemAttrText(models.Model):
    class Meta:
        unique_together = [['bot_menu_elem', 'language_code', 'default_text']]
        index_together = [['bot_menu_elem', 'language_code', 'default_text']]

    dttm_added = models.DateTimeField(default=timezone.now)
    bot_menu_elem = models.ForeignKey(BotMenuElem, null=False, on_delete=models.CASCADE)

    language_code = models.CharField(max_length=16)
    default_text = models.TextField(
        help_text=_('The text which should be translate')
    )
    translated_text = models.TextField(null=True, help_text=_('Default_text Translation'))


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

    min_duration = models.DurationField(
        help_text=_('the minimum period in which there can be 1 notification for a user of this type')
    )
    priority = models.IntegerField(default=1, help_text=_('the more topics will be executed first'))

    botmenuelem = models.ForeignKey(
        BotMenuElem, on_delete=models.PROTECT,
        help_text=_('which trigger message to show')
    )

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
                hours = float(part.replace('h', ''))
            else:
                raise ValueError(f'unknown format {part}')

        return timezone.timedelta(days=days, hours=hours)

    def __str__(self):
        return f"T({self.id}, {self.name})"


class UserTrigger(TelegramAbstractActiveModel):
    trigger = models.ForeignKey(Trigger, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    is_sent = models.BooleanField(default=False)

