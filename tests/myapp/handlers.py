from telegram_django_bot.utils import handler_decor
from telegram import (
    InlineKeyboardMarkup as inlinemark,
    InlineKeyboardButton as inlinebutt
)


@handler_decor()
def me(bot, update, user):
    bot.send_message(
        user.id,
        f"{user}",
        reply_markup=inlinemark([[
            inlinebutt(text='cоздать категорию', callback_data='cat/cr'),
            inlinebutt(text='cоздать cej', callback_data='ent/cr')
        ]])
    )


