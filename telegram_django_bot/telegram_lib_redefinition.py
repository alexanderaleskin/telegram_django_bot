import json
from telegram import (
    # TelegramObject,
    Bot,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyMarkup,
    KeyboardButton,
)


class TelegramDjangoEncoder(json.JSONEncoder):
    def default(self, o):
        if issubclass(type(o), object) and o.__class__.__name__ == '__proxy__':
            return str(o)

        elif hasattr(o, '__call__'):
            return o.__call__()

        return super(TelegramDjangoEncoder, self).default(o)


class TelegramDjangoObject2Json:
    __slots__ = ()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), cls=TelegramDjangoEncoder)


class InlineKeyboardMarkupDJ(TelegramDjangoObject2Json, InlineKeyboardMarkup):
    pass


class InlineKeyboardButtonDJ(TelegramDjangoObject2Json, InlineKeyboardButton):
    pass


class ReplyMarkupDJ(TelegramDjangoObject2Json, ReplyMarkup):
    pass


class KeyboardButtonDJ(TelegramDjangoObject2Json, KeyboardButton):
    pass


class BotDJ(TelegramDjangoObject2Json, Bot):
    pass

