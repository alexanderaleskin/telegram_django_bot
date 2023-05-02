from django import forms
from django.utils.translation import gettext, gettext_lazy
from telegram_django_bot import forms as td_forms
from .models import Category, Entity, Order


class CategoryForm(td_forms.TelegramModelForm):
    form_name = gettext_lazy('Category')

    class Meta:
        model = Category
        fields = ['name', 'info',]

        labels = {
            "name": "Category name",
            "info": "Info"
        }

        widgets = {
            'info': forms.HiddenInput(),
        }


class EntityForm(td_forms.TelegramModelForm):
    form_name = 'Entity'

    class Meta:
        model = Entity
        fields = ['name', 'category', 'sizes', 'is_visable', 'price', 'author_id']

        labels = {
            "name": "Title",
            "info": "Info"
        }


class OrderForm(td_forms.TelegramModelForm):
    form_name = 'Order'

    entities = forms.ModelMultipleChoiceField(queryset=Entity.objects.all().order_by('-id'), required=False, label='Entities')

    class Meta:
        model = Order
        fields = ['info', 'entities']

        labels = {
            "info": "Title",
            "entities": "Entities"
        }

        # widgets = {
        #     'entities': forms.Select
        # }
