from django.contrib import admin
from telegram_django_bot.admin import Users
from .models import Category, Entity, User, Size
from django.db.models import Count, Q


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    pass


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(Users):
    pass
