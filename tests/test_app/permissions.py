from telegram_django_bot.permissions import BasePermissionClass

from .models import Category


class CategoryPermission(BasePermissionClass):
    
    def has_permissions(self, bot, update, user, utrl_args, **kwargs):
        method = utrl_args[0]

        if method in ['up', 'de'] and len(utrl_args) > 1:
            instance = Category.objects.get(pk=utrl_args[1])

            if instance.name == 'hats':
                return False

        return True
