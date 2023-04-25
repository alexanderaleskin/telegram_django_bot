from telegram_django_bot.models import BotMenuElem
from django.utils.translation import gettext_lazy as _
from telegram_django_bot import forms as td_forms


class BotMenuElemForm(td_forms.TelegaModelForm):
    form_name = _("Menu elem")

    class Meta:
        model = BotMenuElem
        fields = ['command', "is_visable", "callbacks_db", "message", "buttons_db"]

