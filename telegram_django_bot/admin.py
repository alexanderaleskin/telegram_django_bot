import csv

from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.db.models import Count
from django.contrib import admin

from .models import TeleDeepLink, ActionLog, Trigger, UserTrigger, BotMenuElem, BotMenuElemAttrText
from .admin_utils import CustomRelatedOnlyDropdownFilter, DefaultOverrideAdminWidgetsForm


class CustomModelAdmin(admin.ModelAdmin):
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = _("Export Selected")


class Users(CustomModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'telegram_username')
    search_fields = (
        'first_name__startswith',
        'last_name__startswith',
        'username__startswith',
        'id'
    )
    list_filter = (
        'is_active',
        ('teledeeplink', CustomRelatedOnlyDropdownFilter)
    )
    actions = ('export_as_csv',)


@admin.register(ActionLog)
class ActionLogAdmin(CustomModelAdmin):
    list_display = ('id', 'user', 'dttm', 'type')
    search_fields = ('type__startswith',)
    list_filter = (
        'type',
        'dttm',
        ('user', CustomRelatedOnlyDropdownFilter),
    )
    raw_id_fields = ('user', )
    actions = ('export_as_csv',)


@admin.register(TeleDeepLink)
class TeleDeepLinkAdmin(CustomModelAdmin):
    list_display = ('id', 'title', 'price', 'link', 'count_users')
    search_fields = ('title', 'link')
    actions = ('export_as_csv',)

    def get_queryset(self, request):
        qs = super(TeleDeepLinkAdmin, self).get_queryset(request)
        return qs.annotate(
            c_users=Count('users')
        )

    def count_users(self, inst):
        return inst.c_users

    count_users.admin_order_field = 'c_users'

    def count_activated(self, inst):
        return inst.ca_users

    count_activated.admin_order_field = 'ca_users'



class BotMenuElemAdminForm(DefaultOverrideAdminWidgetsForm):
    list_json_fields = ['buttons_db', 'callbacks_db', ]


@admin.register(BotMenuElem)
class BotMenuElemAdmin(CustomModelAdmin):
    list_display = ('id', 'message', 'is_visable', 'callbacks_db')
    search_fields = ('command', 'callbacks_db', 'message', 'buttons_db',)
    list_filter = ('is_visable', 'empty_block')
    form = BotMenuElemAdminForm
    actions = ('export_as_csv',)


@admin.register(BotMenuElemAttrText)
class BotMenuElemAttrTextAdmin(CustomModelAdmin):
    list_display = ('id', 'dttm_added', 'language_code', 'default_text', 'translated_text')
    search_fields = ('default_text', 'translated_text')
    list_filter = ('language_code', 'bot_menu_elem')
    actions = ('export_as_csv',)



class TriggerAdminForm(DefaultOverrideAdminWidgetsForm):
    json_fields = ['condition_db',]


@admin.register(Trigger)
class TriggerAdmin(CustomModelAdmin):
    list_display = ('id', 'name', 'min_duration', 'priority', 'botmenuelem_id')
    search_fields = ('name', 'condition_db')
    form = TriggerAdminForm
    actions = ('export_as_csv',)


@admin.register(UserTrigger)
class UserTriggerAdmin(CustomModelAdmin):
    list_display = ('id', 'dttm_added', 'trigger_id', 'user_id', 'is_sent')
    list_filter = ('trigger', 'is_sent')
    actions = ('export_as_csv',)
