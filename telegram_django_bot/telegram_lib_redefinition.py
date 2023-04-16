import json
from telegram import (
    # TelegramObject,
    Bot,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
)


try:
    # version 20.x +
    from telegram import ReplyKeyboardMarkup as ReplyMarkup
except ImportError:
    # old version
    from telegram import ReplyMarkup


def dj_translate_obj_2_string(obj):
    if issubclass(type(obj), object) and obj.__class__.__name__ == '__proxy__':
        return str(obj)

    elif hasattr(obj, '__call__'):
        return obj.__call__()

    return None # if it is not django translate object


class TelegramDjangoEncoder(json.JSONEncoder):
    def default(self, o):
        res = dj_translate_obj_2_string(o)
        if res is None:
            return super(TelegramDjangoEncoder, self).default(o)
        return res


class TelegramDjangoObject2Json:
    __slots__ = ()

    def to_json(self) -> str:
        # for old versions
        return json.dumps(self.to_dict(), cls=TelegramDjangoEncoder)


    def _get_attrs(self, *args, **kwargs):
        # for new 20.x+ versions

        data = super()._get_attrs(*args, **kwargs)
        for key, o in data.items():
            res = dj_translate_obj_2_string(o)
            if res is not None:
                data[key] = res
        return data



class InlineKeyboardMarkupDJ(TelegramDjangoObject2Json, InlineKeyboardMarkup):
    pass


class InlineKeyboardButtonDJ(TelegramDjangoObject2Json, InlineKeyboardButton):
    pass


class ReplyMarkupDJ(TelegramDjangoObject2Json, ReplyMarkup):
    pass


class KeyboardButtonDJ(TelegramDjangoObject2Json, KeyboardButton):
    pass


class BotDJ(TelegramDjangoObject2Json, Bot):
    def _check_django_localization(self, data):
        '''
        check 'text', 'caption' attributes for translation
        :param data:
        :return:
        '''
        for field in ['text', 'caption']:
            if field in data and hasattr(data[field], '__call__'):
                data[field] = data[field].__call__()
            elif data.get(field):
                data[field] = str(data[field])
        return data


    def _message(
            self,
            endpoint: str,
            data,
            *args,
            **kwargs
    ):
        """
        this method used in old versions.

        """

        data = self._check_django_localization(data)

        return super()._message(
            endpoint,
            data,
            *args,
            **kwargs
        )

    async def _do_post(
        self,
        endpoint: str,
        data,
        *args,
        **kwargs,
    ):
        """
        this method used in new 20.x+ versions.

        """

        data = self._check_django_localization(data)
        return await super()._do_post(endpoint, data, *args, **kwargs)

