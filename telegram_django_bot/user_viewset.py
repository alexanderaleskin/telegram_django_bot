from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import translation

from .forms import TelegramModelForm, BaseModelForm, BaseTelegramForm
from .td_viewset import TelegramViewSet



class UserForm(TelegramModelForm):
    form_name = _('User')

    class Meta:
        model = get_user_model()

        fields = ['timezone', 'telegram_language_code', ]

        labels = {
            "timezone": _("Timezone"),
            'telegram_language_code': _("Language"),
        }

    def save(self, commit=True, is_completed=True):
        if self.is_valid() and self.next_field is None and (is_completed or self.instance.pk):
            # full valid form

            BaseModelForm.save(self, commit=commit)
            self.user.refresh_from_db()
            self.user.clear_status()

            if settings.USE_I18N:
                translation.activate(self.user.language_code)
        else:
            BaseTelegramForm.save(self, commit=commit)



class UserViewSet(TelegramViewSet):
    actions = ['change', 'show_elem']

    queryset = get_user_model().objects.all()
    model_form = UserForm
    use_name_and_id_in_elem_showing = False

    prechoice_fields_values = {
        "timezone": list([(f'{tm}:0:0', f'+{tm} UTC' if tm > 0 else f'{tm} UTC') for tm in range(-11, 13)]),
        "telegram_language_code": settings.LANGUAGES,
    }

    def get_queryset(self):
        return super().get_queryset().filter(id=self.user.id)

    def show_elem(self, model_id=None, mess=''):
        _, (mess, buttons) = super().show_elem(self.user.id, mess)

        return self.CHAT_ACTION_MESSAGE, (mess, buttons)

    def gm_value_str(self, model, field, field_name, try_field='name'):
        if field_name == 'timezone':
            value = getattr(model, field_name, "")
            value = int(value.total_seconds() // 3600)
            return f'+{value} UTC' if value > 0 else f'{value} UTC'

        else:
            return super().gm_value_str(model, field, field_name, try_field)

    def gm_next_field_choice_buttons(self, *args, **kwargs):
        kwargs['self_variant'] = False
        return super().gm_next_field_choice_buttons(*args, **kwargs)
