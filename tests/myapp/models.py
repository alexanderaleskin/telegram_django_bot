from telegram_django_bot.models import TelegramUser
from django.db import models


class User(TelegramUser):
    pass


class NamedClass(models.Model):
    name = models.CharField(max_length=128, help_text='Введите данные без ошибок')
    is_visable = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Category(NamedClass):
    """category """

    info = models.TextField(null=True, blank=True)
    some_int = models.IntegerField(null=True, blank=True)
    some_float = models.FloatField(null=True, blank=True)
    some_demical = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)

class Size(NamedClass):
    """size"""

class Entity(NamedClass):
    price = models.DecimalField(max_digits=16, decimal_places=2, help_text='a')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    sizes = models.ManyToManyField(Size, blank=True, related_name='entities', through='EntitySizeAmount')


class EntitySizeAmount(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)

    amount = models.FloatField(default=0)


class Order(models.Model):
    STATUS_CREATED = 'C'
    STATUS_WAITING = 'W'
    STATUS_COMPLETED = 'D'

    STATUSES = (
        (STATUS_CREATED, STATUS_CREATED),
        (STATUS_WAITING, STATUS_WAITING),
        (STATUS_COMPLETED, STATUS_COMPLETED),
    )

    dttm_added = models.DateTimeField(auto_now_add=True)
    info = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUSES)

    entities = models.ManyToManyField(Entity, blank=True)

class BoughtItem(models.Model):
    entity_size = models.ForeignKey(EntitySizeAmount, on_delete=models.PROTECT)
    amount = models.IntegerField(default=1)

    price = models.DecimalField(max_digits=16, decimal_places=2)

    order = models.ForeignKey(Order, on_delete=models.CASCADE)

