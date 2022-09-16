from django.forms.models import modelform_factory
from django import forms
from telegram_django_bot import forms as td_forms
from .models import Category, Size, Entity, Order


class ff(td_forms.TelegaForm):
    f1 = forms.IntegerField()
    f2 = forms.CharField()
    f3 = forms.FloatField()


class dd(ff):
    f4 = forms.IntegerField()


class CategoryForm(td_forms.TelegaModelForm):
    form_name = 'Категория'

    class Meta:
        model = Category
        fields = ['name', 'info', 'some_int']

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
        fields = ['name', 'category', 'sizes', 'is_visable', 'price']

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

