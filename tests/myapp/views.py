from telegram_django_bot.td_viewset import TelegaViewSet
from .models import Category, Entity, Order
from .forms import CategoryForm, EntityForm, OrderForm
from telegram_django_bot.telegram_lib_redefinition import InlineKeyboardButtonDJ
from django.utils.translation import gettext_lazy as _
from django.db import models


class CategoryViewSet(TelegaViewSet):
    command_routing_show_options = 'aaa'
    telega_form = CategoryForm
    queryset = Category.objects.all()
    viewset_name = _('Category')

    cancel_adding_button = InlineKeyboardButtonDJ(
        text=_('Cancel adding'),
        callback_data='cat/sl'
    )

    generate_function_main_mess = {
        # 'generate_message_next_field': '\n',
        'generate_message_success_created': 'ff %(viewset_name)s\n\n',
    }

    prechoice_fields_values = {
        'name': (
            ('шапки', 'шапки'),
            ('обувь', 'обувь'),
            ('одежда', 'одежда'),
        ),
        'some_int': (
            (100, '100'),
            (1000, '1000'),
            (5000, '5000'),
        )
    }

    updating_fields = ['name', 'info', 'some_int']

    def show_elem(self, model_or_pk, mess=''):
        if issubclass(type(model_or_pk), models.Model):
            model = model_or_pk
        else:
            model = self.get_queryset().filter(pk=model_or_pk).first()

        return super().show_elem(model, mess)


class EntityViewSet(TelegaViewSet):
    command_routing_show_options = 'aaa'
    telega_form = EntityForm
    queryset = Entity.objects.all()
    viewset_name = _('Entity')

    meta_texts_dict = {
        'generate_message_next_field': _('Redefine %(label)s\n\n'),
    }


class OrderViewSet(TelegaViewSet):
    telega_form = OrderForm
    queryset = Order.objects.all()
    viewset_name = 'Заказ'

