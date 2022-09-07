from django.contrib import admin
from .models import TeleDeepLink, ActionLog, Trigger, UserTrigger, BotMenuElem
from .admin_utils import CustomRelatedOnlyDropdownFilter, DefaultOverrideAdminWidgetsForm
from django.db.models import Count, Q


# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('id', 'first_name', 'last_name', 'telegram_username')
#     list_filter = ('first_name', 'last_name', 'telegram_username')


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dttm', 'type')
    list_filter = (
        'type',
        ('user', CustomRelatedOnlyDropdownFilter),
    )
    raw_id_fields = ('user', )


@admin.register(TeleDeepLink)
class TeleDeepLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'link', 'count_users', 'count_activated',)
    search_fields = ('title',)

    def get_queryset(self, request):
        qs = super(TeleDeepLinkAdmin, self).get_queryset(request)
        return qs.annotate(
            c_users=Count('users'),
            ca_users=Count('users', filter=Q(users__activated=True))
        )

    def count_users(self, inst):
        return inst.c_users

    count_users.admin_order_field = 'c_users'

    def count_activated(self, inst):
        return inst.ca_users

    count_activated.admin_order_field = 'ca_users'



class BotMenuElemAdminForm(DefaultOverrideAdminWidgetsForm):
    json_fields = ['buttons_db', 'callbacks_db', ]


@admin.register(BotMenuElem)
class BotMenuElemAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'is_visable', 'callbacks_db')
    search_fields = ('command', 'callbacks_db', 'message', 'buttons_db',)
    list_filter = ('is_visable', 'empty_block')
    form = BotMenuElemAdminForm


class TriggerAdminForm(DefaultOverrideAdminWidgetsForm):
    json_fields = ['condition_db',]


@admin.register(Trigger)
class TriggerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'min_duration', 'priority', 'botmenuelem_id')
    search_fields = ('name', 'condition_db')
    form = TriggerAdminForm


@admin.register(UserTrigger)
class UserTriggerAdmin(admin.ModelAdmin):
    list_display = ('id', 'dttm_added', 'trigger_id', 'user_id', 'is_sent')
    list_filter = ('trigger', 'is_sent')
