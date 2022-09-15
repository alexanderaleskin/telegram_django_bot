from telegram_django_bot.td_viewset import TelegaViewSet
from .models import Category, Entity
from .forms import CategoryForm, EntityForm
from telegram_django_bot.telegram_lib_redefinition import InlineKeyboardButtonDJ
from django.utils.translation import gettext_lazy as _


class CategoryViewSet(TelegaViewSet):
    command_routing_show_options = 'aaa'
    telega_form = CategoryForm
    queryset = Category.objects.all()
    viewset_name = _('Category')

    cancel_adding_button = InlineKeyboardButtonDJ(
        text=_('Cancel adding'),
        callback_data='cat/sl'
    )

    prechoice_fields_values = {
        'name': (
            ('шапки', 'шапки'),
            ('обувь', 'обувь'),
            ('одежда', 'одежда'),
        ),
        'some_int': (
            ('100', '100'),
            ('1000', '1000'),
            ('5000', '5000'),
        )
    }

    updating_fields = ['name', 'info', 'some_int']


class EntityViewSet(TelegaViewSet):
    command_routing_show_options = 'aaa'
    telega_form = EntityForm
    queryset = Entity.objects.all()
    viewset_name = _('Entity')

