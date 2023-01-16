from telegram_django_bot.utils import handler_decor
from telegram_django_bot.telegram_lib_redefinition import (
    InlineKeyboardMarkupDJ as inlinemark,
    InlineKeyboardButtonDJ as inlinebutt
)
from django.utils.translation import gettext as _


@handler_decor()
def me(bot, update, user):
    return bot.send_message(
        user.id,
        f"{user}",
        reply_markup=inlinemark([[
            inlinebutt(text=_('create category'), callback_data='cat/cr'),
            inlinebutt(text=_('create entity'), callback_data='ent/cr'),
            inlinebutt(text=_('user'), callback_data='us/se')
        ]])
    )


