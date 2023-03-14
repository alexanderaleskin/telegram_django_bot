from telegram_django_bot.models import TelegramUser
from django.db import models


class User(TelegramUser):
    pass


class NamedClass(models.Model):
    name = models.CharField(max_length=128, help_text='max length 128')
    is_visable = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Category(NamedClass):
    """category """

    info = models.TextField(null=True, blank=True, help_text='extra info about category')


class Size(NamedClass):
    """size"""


class Entity(NamedClass):
    price = models.DecimalField(max_digits=16, decimal_places=2, help_text='')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    sizes = models.ManyToManyField(Size, blank=True, related_name='entities', through='EntitySizeAmount')

    author_id = models.PositiveIntegerField(help_text='write positive number')
    used_material = models.FloatField(blank=True, null=True, help_text='float field')


class EntitySizeAmount(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)

    amount = models.FloatField(default=0)


class Order(models.Model):
    STATUS_CREATED = 'C'
    STATUS_WAITING = 'W'
    STATUS_COMPLETED = 'D'

    STATUSES = (
        (STATUS_CREATED, '✔️ ️Created'),
        (STATUS_WAITING, '⏱ Waiting'),
        (STATUS_COMPLETED, '✅ Completed'),
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
