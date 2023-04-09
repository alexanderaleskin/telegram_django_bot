import csv

from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.db.models import Count
from django.contrib import admin

from .models import TeleDeepLink, ActionLog, Trigger, UserTrigger, BotMenuElem, BotMenuElemAttrText
from .admin_utils import CustomRelatedOnlyDropdownFilter, DefaultOverrideAdminWidgetsForm


class CustomModelAdmin(admin.ModelAdmin):
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        file_name = str(meta).replace('.', '_')

        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(file_name)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = _("Export Selected")
    actions = ('export_as_csv',)


class TelegramUserAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site) -> None:
        if apps.is_installed('rangefilter'):
            from rangefilter.filters import DateRangeFilter
            self.list_filter = (
                'is_active',
                ('date_joined', DateRangeFilter),
                ('teledeeplink', CustomRelatedOnlyDropdownFilter),
            )
        super().__init__(model, admin_site)

    list_display = ('id', 'first_name', 'last_name', 'telegram_username')
    search_fields = (
        'first_name__startswith',
        'last_name__startswith',
        'username__startswith',
        'id'
    )
    list_filter = (
        'is_active',
        'date_joined',
        ('teledeeplink', CustomRelatedOnlyDropdownFilter),
    )


@admin.register(ActionLog)
class ActionLogAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site) -> None:
        if apps.is_installed('rangefilter'):
            from rangefilter.filters import DateRangeFilter
            self.list_filter = (
                'type',
                ('dttm', DateRangeFilter),
                ('user', CustomRelatedOnlyDropdownFilter),
            )
        super().__init__(model, admin_site)
    
    list_display = ('id', 'user', 'dttm', 'type')
    search_fields = ('type__startswith',)
    list_filter = (
        'type',
        'dttm',
        ('user', CustomRelatedOnlyDropdownFilter),
    )
    raw_id_fields = ('user', )


@admin.register(TeleDeepLink)
class TeleDeepLinkAdmin(CustomModelAdmin):
    list_display = ('id', 'title', 'price', 'link', 'count_users')
    search_fields = ('title', 'link')

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


@admin.register(BotMenuElemAttrText)
class BotMenuElemAttrTextAdmin(CustomModelAdmin):
    list_display = ('id', 'dttm_added', 'language_code', 'default_text', 'translated_text')
    search_fields = ('default_text', 'translated_text')
    list_filter = ('language_code', 'bot_menu_elem')


class TriggerAdminForm(DefaultOverrideAdminWidgetsForm):
    json_fields = ['condition_db',]


@admin.register(Trigger)
class TriggerAdmin(CustomModelAdmin):
    list_display = ('id', 'name', 'min_duration', 'priority', 'botmenuelem_id')
    search_fields = ('name', 'condition_db')
    form = TriggerAdminForm


@admin.register(UserTrigger)
class UserTriggerAdmin(CustomModelAdmin):
    list_display = ('id', 'dttm_added', 'trigger_id', 'user_id', 'is_sent')
    list_filter = ('trigger', 'is_sent')
