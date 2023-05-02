from telegram_django_bot.td_viewset import TelegramViewSet
from .models import Category, Entity, Order
from .forms import CategoryForm, EntityForm, OrderForm
from telegram_django_bot.telegram_lib_redefinition import InlineKeyboardButtonDJ
from django.utils.translation import gettext_lazy as _
from django.db import models
from .permissions import CategoryPermission


class CategoryViewSet(TelegramViewSet):
    permission_classes = [CategoryPermission]
    command_routing_show_options = 'aaa'
    model_form = CategoryForm
    queryset = Category.objects.all()
    viewset_name = _('Category')

    cancel_adding_button = InlineKeyboardButtonDJ(
        text=_('Cancel adding'),
        callback_data='cat/sl'
    )

    generate_function_main_mess = {
        # 'gm_next_field': '\n',
        'gm_success_created': 'ff %(viewset_name)s\n\n',
    }

    prechoice_fields_values = {
        'name': (
            ('hats', 'Hats'),
            ('shoes', 'Shoes'),
            ('cloth', 'Cloth'),
        ),
    }

    updating_fields = ['name', 'info']

    def show_elem(self, model_or_pk, mess=''):
        if issubclass(type(model_or_pk), models.Model):
            model = model_or_pk
        else:
            model = self.get_queryset().filter(pk=model_or_pk).first()

        return super().show_elem(model, mess)


class EntityViewSet(TelegramViewSet):
    command_routing_show_options = 'aaa'
    model_form = EntityForm
    queryset = Entity.objects.all()
    viewset_name = _('Entity')

    meta_texts_dict = {
        'gm_next_field': _('Redefine %(label)s\n\n'),
    }


class OrderViewSet(TelegramViewSet):
    model_form = OrderForm
    queryset = Order.objects.all()
    viewset_name = 'Order'
    foreign_filter_amount = 1  # [entity_id]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.foreign_filters[0]:
            return queryset.filter(entities=self.foreign_filters[0])
        else:
            return queryset
