from django import forms
from django.utils.translation import gettext, gettext_lazy
from telegram_django_bot import forms as td_forms
from .models import Category, Entity, Order


class CategoryForm(td_forms.TelegaModelForm):
    form_name = gettext_lazy('Category')

    class Meta:
        model = Category
        fields = ['name', 'info',]

        labels = {
            "name": "Название категории",
            "info": "Информация"
        }

        widgets = {
            'info': forms.HiddenInput(),
        }


class EntityForm(td_forms.TelegaModelForm):
    form_name = 'Изделие'

    class Meta:
        model = Entity
        fields = ['name', 'category', 'sizes', 'is_visable', 'price', 'author_id']

        labels = {
            "name": "Название",
            "info": "Информация"
        }



class OrderForm(td_forms.TelegaModelForm):
    form_name = 'Заказ'

    entities = forms.ModelMultipleChoiceField(queryset=Entity.objects.all().order_by('-id'), required=False, label='Товары')

    class Meta:
        model = Order
        fields = ['info', 'entities']

        labels = {
            "info": "Название",
            "entities": "Товары"
        }

        # widgets = {
        #     'entities': forms.Select
        # }
