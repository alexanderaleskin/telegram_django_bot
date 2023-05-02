import sys

from functools import wraps
import telegram

from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ActionLog, TeleDeepLink
from .telegram_lib_redefinition import (
    InlineKeyboardButtonDJ as inlinebutt
)
from django.conf import settings  # LANGUAGES, USE_I18N
from calendar import monthcalendar
from dateutil.relativedelta import relativedelta
from django.utils import translation
from django.utils.translation import gettext_lazy as _


ERROR_MESSAGE = _('Oops! It seems that an error has occurred, please write to support (contact in bio)!')
LOGGING_TELEGRAM_ACTIONS = getattr(settings, 'TELEGRAM_ACTION_LOG', True)


def add_log_action(user_id, action):
    if LOGGING_TELEGRAM_ACTIONS:
        ActionLog.objects.create(type=action, user_id=user_id)


def handler_decor(log_type='F', update_user_info=True):
    """

    :param log_type: 'F' -- функция, 'C' -- callback or command, 'U' -- user-status, 'N' -- NO LOG
    :param update_user_info: update user info if it has been changed
    :return:
    """

    def decor(func):
        @wraps(func)
        def wrapper(update, CallbackContext):
            def check_first_income():
                if update and update.message and update.message.text:
                    query_words = update.message.text.split()
                    if len(query_words) > 1 and query_words[0] == '/start':
                        telelink, _ = TeleDeepLink.objects.get_or_create(link=query_words[1])
                        telelink.users.add(user)

            bot = CallbackContext.bot

            user_details = update.effective_user
            # if update.callback_query:
            #     user_details = update.callback_query.from_user
            # elif update.inline_query:
            #     user_details = update.inline_query.from_user
            # else:
            #     user_details = update.message.from_user

            if user_details is None:
                raise ValueError(
                    f'handler_decor is made for communication with user, current update has not any user: {update}'
                )

            User = get_user_model()

            user_adding_info = {
                'username': '{}'.format(user_details.id),
                'telegram_language_code': user_details.language_code or 'en',

                'telegram_username': user_details.username[:64] if user_details.username else '',
                'first_name': user_details.first_name[:30] if user_details.first_name else '',
                'last_name': user_details.last_name[:60] if user_details.last_name else '',
            }

            user, created = User.objects.get_or_create(
                id=user_details.id,
                defaults=user_adding_info
            )

            if created:
                add_log_action(user.id, 'ACTION_CREATED')
                check_first_income()
            elif update_user_info:
                # check if telegram_username or first_name or last_name changed:
                fields_changed = False
                for key in ['telegram_username', 'first_name', 'last_name']:
                    if getattr(user, key) != user_adding_info[key]:
                        setattr(user, key, user_adding_info[key])
                        fields_changed = True

                if fields_changed:
                    user.save()

            if not user.is_active:
                check_first_income()
                user.is_active = True
                user.save()

            if settings.USE_I18N:
                translation.activate(user.language_code)

            raise_error = None
            try:
                res = func(bot, update, user)
            except telegram.error.BadRequest as error:
                if 'Message is not modified:' in error.message:
                    res = None
                else:
                    res = bot.send_message(user.id, str(ERROR_MESSAGE))  # should be bot.send_format_message
                    tb = sys.exc_info()[2]
                    raise_error = error.with_traceback(tb)
            except Exception as error:

                res = bot.send_message(user.id, str(ERROR_MESSAGE))  # should be bot.send_format_message
                tb = sys.exc_info()[2]
                raise_error = error.with_traceback(tb)

            # log actions

            if log_type != 'N':
                if log_type == 'C':
                    if update.callback_query:
                        log_value = update.callback_query.data
                    else:
                        log_value = update.message.text
                elif log_type == 'U':
                    log_value = user.current_utrl
                # elif log_type == 'F':
                else:
                    log_value = func.__name__

                add_log_action(user.id, log_value[:32])

            if ActionLog.objects.filter(user=user, type='ACTION_ACTIVE_TODAY', dttm__date=timezone.now().date()).count() == 0:
                add_log_action(user.id, 'ACTION_ACTIVE_TODAY')

            if raise_error:
                raise raise_error

            return res
        return wrapper
    return decor



# todo: rewrite code
# ButtonPagination WITHOUT WARRANTY
class ButtonPagination:
    """
    construct several pages with buttons

    buttons -- array of buttons with values for display to user, button format:
        [text; value]
    selected_buttons -- selected buttons (add icon)
    header_buttons -- buttons in the header for navigation or other cases, format:
       [text; value; callback_prefix]  -- if callback_prefix=None then self.callback_prefix is selected
    footer_buttons -- same as header_buttons, but in the footer

    """

    def __init__(
            self,
            callback_prefix,
            buttons=None,
            selected_values=None,
            callback_prefix_context_values=None,
            rows=8,
            columns=1,
    ):
        self.SELECTED_TICK = '✅ '
        self.PREV_PAGE_STR = '⏮'
        self.NEXT_PAGE_STR = '⏭'
        self.PAGE_CALLBACK_SYMBOL = 'telegram_p'

        self.callback_prefix = callback_prefix
        self.buttons = buttons
        self.callback_prefix_context_values = callback_prefix_context_values
        self.selected_values = selected_values
        self.rows = rows
        self.columns = columns

    @property
    def buttons_per_page(self):
        return self.rows * self.columns

    @property
    def full_callback_prefix(self):
        context_callback = ''
        if self.callback_prefix_context_values:
            context_callback = '-'.join(map(str, self.callback_prefix_context_values)) + '-'
        return self.callback_prefix + context_callback

    def value_page(self, value):
        """
        select the default page for display

        :param value: ???
        :return:
        """

        selected_item_index = list(
            map(lambda x: x[1], self.buttons)
        ).index(value)
        return selected_item_index // self.buttons_per_page

    def _select_page_buttons(self, page_num):
        """
        select buttons for display on the page_num page. Func is created for easy logic redefinition.
        :param page_num: if None, then  _select_page is called
        :return:
        """
        return self.buttons[page_num * self.buttons_per_page: (page_num + 1) * self.buttons_per_page]

    def construct_inline_curr_page(self, page_num=None, ):
        """
        Created  inline buttons

        :param page_num:
        :return:
        """

        telegram_buttons = []
        if page_num is None:
            if self.selected_values:
                page_num = self.value_page(self.selected_values[0])
            else:
                page_num = 0

        value_buttons = self._select_page_buttons(page_num)

        col_index = 0
        for button in value_buttons:
            button_text = ''
            if self.selected_values and (button[1] in self.selected_values):
                button_text += self.SELECTED_TICK

            button_text += button[0]
            button_telegram = inlinebutt(button_text, callback_data=self.full_callback_prefix + button[1])

            if col_index == 0:
                # new row
                telegram_buttons.append([button_telegram])
            else:
                # add in last row
                telegram_buttons[-1].append(button_telegram)

            col_index += 1
            if col_index == self.columns:
                col_index = 0

        # neighbor pages
        neighbor_buttons = []
        if page_num > 0:
            callback_data = self.full_callback_prefix + self.PAGE_CALLBACK_SYMBOL + str(page_num - 1)
            neighbor_buttons.append(
                inlinebutt(self.PREV_PAGE_STR, callback_data=callback_data)
            )
        if page_num < int(len(self.buttons) / self.buttons_per_page + 0.9999) - 1:
            callback_data = self.full_callback_prefix + self.PAGE_CALLBACK_SYMBOL + str(page_num + 1)
            neighbor_buttons.append(
                inlinebutt(self.NEXT_PAGE_STR, callback_data=callback_data)
            )
        if neighbor_buttons:
            telegram_buttons.append(neighbor_buttons)

        return telegram_buttons


class CalendarPagination:
    def __init__(
            self,
            callback_prefix,
            curr_month,

            buttons: dict = None,
            selected_values=None,
            month_callback_prefix=None,
            month_callback_str_format=None,

            not_clickable=True,
    ):
        self.SELECTED_TICK = '✅ '
        self.PREV_PAGE_STR = '⏮'
        self.NEXT_PAGE_STR = '⏭'

        self.callback_prefix = callback_prefix
        self.curr_month = curr_month
        self.buttons = buttons or {}
        self.selected_values = selected_values or []
        self.month_callback_prefix = month_callback_prefix or callback_prefix
        self.month_callback_str_format = month_callback_str_format or '%y.%m'

        self.not_clickable = not_clickable

    def construct_inline_curr_page(self):
        prev_month = self.curr_month - relativedelta(months=1)
        next_month = self.curr_month + relativedelta(months=1)
        curr_month_callback = self.month_callback_prefix + self.curr_month.strftime(self.month_callback_str_format)

        month_buttons = [
            [
                inlinebutt(
                    self.PREV_PAGE_STR,
                    callback_data=self.month_callback_prefix + prev_month.strftime(self.month_callback_str_format)
                ),
                inlinebutt(
                    self.NEXT_PAGE_STR,
                    callback_data=self.month_callback_prefix + next_month.strftime(self.month_callback_str_format)
                ),
            ]
        ]

        for week_row in monthcalendar(self.curr_month.year, self.curr_month.month):
            week_buttons = []
            for month_day in week_row:
                if month_day > 0:
                    day_button_info = self.buttons.get(month_day)
                    if day_button_info:
                        button_callback, button_text = day_button_info
                    else:
                        button_callback = curr_month_callback if self.not_clickable else self.callback_prefix + f'{month_day}'
                        button_text = f'{month_day}'

                    if month_day in self.selected_values:
                        button_text = f'{self.SELECTED_TICK} {button_text}'


                else:
                    button_text = '\u200b'
                    button_callback = curr_month_callback

                week_buttons.append(
                    inlinebutt(button_text, callback_data=button_callback)
                )
            month_buttons.append(week_buttons)
        return month_buttons

