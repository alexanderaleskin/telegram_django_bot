import logging

import re
import copy
from django.forms import HiddenInput
from django.forms.models import ModelMultipleChoiceField
from django.db import models
from django.forms.fields import ChoiceField, BooleanField
from django.utils.translation import gettext as _, gettext_lazy

from .utils import add_log_action
from .telegram_lib_redefinition import InlineKeyboardButtonDJ as inlinebutt
from .permissions import PermissionAllowAny


class TelegramViewSetMetaClass(type):
    """
    Needed for inheritance information of command_routings_<func> and meta_texts_dict

    """

    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.

        current_fields = []
        for key, value in list(attrs.items()):
            if key.startswith('command_routing_') and (type(value) == str) and value:
                current_fields.append((key, value))
                attrs.pop(key)
        attrs['command_routings'] = dict(current_fields)
        new_class = super().__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        command_routings = {}
        show_texts_dict = {}
        for base in reversed(new_class.__mro__):
            # Collect command_routings from base class.
            if hasattr(base, 'command_routings'):
                command_routings.update(base.command_routings)

            if hasattr(base, 'meta_texts_dict'):
                show_texts_dict.update(base.meta_texts_dict)

        new_class.command_routings = command_routings
        new_class.show_texts_dict = show_texts_dict
        return new_class


class TelegramViewSet(metaclass=TelegramViewSetMetaClass):
    permission_classes = [PermissionAllowAny]   # in dispatch function check permission for calling action with args
    actions = ['create', 'change', 'delete', 'show_elem', 'show_list']  # actions of the class

    # utrl for actions
    command_routing_create = 'cr'
    command_routing_change = 'up'
    command_routing_delete = 'de'
    command_routing_show_elem = 'se'
    command_routing_show_list = 'sl'

    WRITE_MESSAGE_VARIANT_SYMBOLS = '!WMVS!'
    NONE_VARIANT_SYMBOLS = '!NoneNULL!'
    GO_NEXT_MULTICHOICE_SYMBOLS = '!GNMS!'

    CHAT_ACTION_MESSAGE = 'message'

    ARGS_SEPARATOR_SYMBOL = '&'

    model_form = None

    queryset = None
    # viewset_name = ''  # used in message for user, redefined as property by default
    foreign_filter_amount = 0

    prechoice_fields_values = {}

    updating_fields = None

    show_cancel_updating_button = True
    deleting_with_confirm = True
    cancel_adding_button = None

    use_name_and_id_in_elem_showing = True

    meta_texts_dict = {
        'succesfully_deleted': gettext_lazy('The %(viewset_name)s  %(model_id)s is successfully deleted.'),
        'confirm_deleting': gettext_lazy('Are you sure you want to delete %(viewset_name)s  %(model_id)s?'),
        'confirm_delete_button_text': gettext_lazy('🗑 Yes, delete'),
        'gm_next_field': gettext_lazy('Please, fill the field %(label)s\n\n'),
        'gm_success_created': gettext_lazy('The %(viewset_name)s is created! \n\n'),
        'gm_value_error': gettext_lazy('While adding %(label)s the next errors were occurred: %(errors)s\n\n'),
        'gm_self_variant': gettext_lazy('Please, write the value for field %(label)s \n\n'),
        'gm_no_elem': gettext_lazy(
            'The %(viewset_name)s %(model_id)s has not been found 😱 \nPlease try again from the beginning.'
        ),
        'leave_blank_button_text': gettext_lazy('Leave blank'),
    }

    def __init__(self, prefix, user=None, bot=None, update=None, foreign_filters=None):
        self.user = user
        self.bot = bot
        self.update = update
        self.form = None
        self.foreign_filters = foreign_filters or []

        self.viewset_routing = {}

        if self.queryset is None:
            raise ValueError('queryset could not be None')

        if self.model_form is None:
            raise ValueError('model_form could not be None')

        for action in self.actions:
            cr_action = f'command_routing_{action}'
            if not cr_action in self.command_routings.keys():
                raise ValueError(
                    f'for action {action} must be determinate {cr_action},'
                    f' but list is {self.command_routings.keys()}'
                )

            self.viewset_routing[self.command_routings[cr_action]] = self.__getattribute__(action)

        self.prefix = prefix.replace('^', '').replace('$', '')

    @property
    def viewset_name(self) -> str:
        """ just for easy creating class """
        return self.__str__()

    def __repr__(self):
        return f'{self.__class__.__name__}'

    def __str__(self):
        return f'{self.__class__.__name__}'


    # Entrance and exit of the class:
    # dispatch gets info about user action, checks permissions, selects and executes function
    # (one of the 5 main or self written) basing on user action, and finally send answer to user

    def dispatch(self, bot, update, user):
        """ terminate function for response """

        self.bot = bot
        self.update = update
        self.user = user

        utrl = update.callback_query.data if update.callback_query else user.current_utrl
        utrl_args = self.get_utrl_params(re.sub(f'^{self.prefix}', '', utrl))
        logging.debug(f'used utrl: {utrl}')

        if self.has_permissions(bot, update, user, utrl_args):
            chat_reply_action, chat_action_args = self.viewset_routing[utrl_args[0]](*utrl_args[1:])
        else:
            chat_reply_action = self.CHAT_ACTION_MESSAGE
            message = _('Sorry, you do not have permissions to this action.')
            buttons = []
            chat_action_args = (message, buttons)

        res = self.send_answer(chat_reply_action, chat_action_args, utrl)

        utrl_path = utrl.split(self.ARGS_SEPARATOR_SYMBOL)[0]   # log without params as there are too much varients
        add_log_action(self.user.id, utrl_path)
        return res

    def get_utrl_params(self, utrl):
        edge = self.foreign_filter_amount + 1
        args = utrl.split(self.ARGS_SEPARATOR_SYMBOL)
        self.foreign_filters = args[1:edge]
        return args[:1] + args[edge:]

    def has_permissions(self, bot, update, user, utrl_args, **kwargs):
        for permission in self.permission_classes:
            if not permission().has_permissions(bot, update, user, utrl_args, **kwargs):
                return False
        return True

    def send_answer(self, chat_reply_action, chat_action_args, utrl, *args, **kwargs):
        if chat_reply_action == self.CHAT_ACTION_MESSAGE:
            message, buttons = chat_action_args
            res = self.bot.edit_or_send(
                self.update,
                message,
                buttons,
            )
        else:
            raise ValueError(f'unknown chat_action {chat_reply_action} {utrl}, {self.user}')
        return res

    # 5 main functions for data managing

    def create(self, field=None, value=None, initial_data=None):
        """creating item, could be several steps"""

        if field is None and value is None:
            # then it is starting adding
            self.user.clear_status(commit=False)

        return self.create_or_update_helper(field, value, 'create', initial_data=initial_data)

    def change(self, model_or_pk, field, value=None):
        """
        change item
        :param model_or_pk: django models.Model or pk
        :param field:
        :param value:
        :return:
        """

        model = self.get_orm_model(model_or_pk)

        self.user.clear_status(commit=True)

        if model:
            return self.create_or_update_helper(field, value, func_response='change', instance=model)
        else:
            return self.gm_no_elem(model_or_pk)

    def delete(self, model_or_pk, is_confirmed=False):
        """delete item"""

        model = self.get_orm_model(model_or_pk)

        if model:
            if self.deleting_with_confirm and not is_confirmed:
                # just ask for confirmation
                mess, buttons = self.gm_delete_getting_confirmation(model)
            else:
                # real deleting
                model.delete()
                mess, buttons = self.gm_delete_successfully(model)

            return self.CHAT_ACTION_MESSAGE, (mess, buttons)
        else:
            return self.gm_no_elem(model_or_pk)

    def show_elem(self, model_or_pk, mess=''):
        """

        :param model_or_pk:
        :param mess:
        :return:
        """

        # generate content
        model = self.get_orm_model(model_or_pk)

        # generate view of content
        if model:
            if self.use_name_and_id_in_elem_showing:
                mess += f'{self.viewset_name} #{model.pk} \n'
            mess += self.gm_show_elem_or_list_fields(model, is_elem=True)

            buttons = self.gm_show_elem_create_buttons(model)

            return self.CHAT_ACTION_MESSAGE, (mess, buttons)
        else:
            return self.gm_no_elem(model_or_pk)

    def show_list(self, page=0, per_page=10, columns=1, *args, **kwargs):
        """show list items"""
        page = int(page)

        # generate content
        count_models, page_models, first_this_page, first_next_page = self.show_list_get_queryset(
            page, per_page, columns, *args, **kwargs
        )

        # generate view of content
        if page_models_amount := len(page_models):
            mess = ''
            buttons = self.gm_show_list_create_pagination(
                page, count_models, first_this_page, first_next_page, page_models_amount
            )

            for it_m, model in enumerate(page_models, page * per_page * columns + 1):
                mess += self.gm_show_list_elem_info(model, it_m)

                buttons += [
                    [inlinebutt(
                        text=self.gm_show_list_button_names(it_m, model),
                        callback_data=self.gm_callback_data('show_elem', model.pk)
                    )]
                ]
        else:
            mess = _('There is nothing to show.')
            buttons = []

        return self.CHAT_ACTION_MESSAGE, (mess, buttons)

    # help functions for main functions for doing its work.

    def get_queryset(self):
        if self.queryset._result_cache:
            self.queryset._result_cache = None
            self.queryset._prefetch_done = False
        return self.queryset

    def create_or_update_helper(self, field, value, func_response='create', instance=None, initial_data=None):
        # init data
        is_multichoice_field = self.model_form.base_fields[field].__class__ == ModelMultipleChoiceField if field else False
        show_field_variants_for_update = (func_response == 'change') and (value is None) and (self.update.message is None)
        want_1more_variant_for_multichoice = True
        want_write_self_variant = False
        data = {} if initial_data is None else copy.deepcopy(initial_data)

        # understanding what user has sent
        if (type(field) == str) and field:
            field_value = None
            if value:
                if value == self.WRITE_MESSAGE_VARIANT_SYMBOLS:
                    want_write_self_variant = True
                elif value == self.GO_NEXT_MULTICHOICE_SYMBOLS:
                    want_1more_variant_for_multichoice = False
                elif value == self.NONE_VARIANT_SYMBOLS:
                    data[field] = None
                else:
                    field_value = value
            elif self.update.message:
                field_value = self.update.message.text

            if not field_value is None:
                data[field] = field_value.split(',') if is_multichoice_field else field_value

        # some prepare work
        want_1more_variant_for_multichoice &= is_multichoice_field  # and len(data.get('field', []))

        form_kwargs = {
            'user': self.user,
            'data': data,
        }
        instance_id = None
        if instance:
            form_kwargs['instance'] = instance
            instance_id = instance.pk

        self.form = self.model_form(**form_kwargs)
        form = self.form

        # show message or change data in backend...
        if want_write_self_variant:
            res = self.gm_self_variant(field, func_response=func_response, instance_id=instance_id)
        else:
            if not form.is_valid():
                res = self.gm_value_error(
                    field or list(form.fields.keys())[-1],
                    form.errors, func_response=func_response, instance_id=instance_id
                )
            else:
                if not show_field_variants_for_update:
                    # todo: rewrite as is_completed will work only form ModelForm
                    form.save(is_completed=not want_1more_variant_for_multichoice)

                if want_1more_variant_for_multichoice or show_field_variants_for_update:
                    res = self.gm_next_field(
                        field,
                        func_response=func_response,
                        instance_id=instance_id
                    )

                elif form.next_field:
                    res = self.gm_next_field(
                        form.next_field,
                        func_response=func_response,
                        instance_id=instance_id
                    )
                else:
                    if func_response == 'create':
                        res = self.gm_success_created(self.form.instance)
                    else:
                        res = self.show_elem(self.form.instance, _('The field has been updated!\n\n'))
        return res

    def show_list_get_queryset(self, page=0, per_page=10, columns=1, *args, **kwargs):
        count_models = self.get_queryset().count()
        first_this_page = page * per_page * columns
        first_next_page = (page + 1) * per_page * columns
        page_models = list(self.get_queryset()[first_this_page: first_next_page])
        return count_models, page_models, first_this_page, first_next_page

    def get_orm_model(self, model_or_pk):
        if issubclass(type(model_or_pk), models.Model):
            model = model_or_pk
        else:
            model = self.get_queryset().filter(pk=model_or_pk).first()
        return model

    # next functions are helpers for generate view of content (text and buttons for reply message)
    # these functions just show / generate readable content for human and do not change anything

    def gm_show_elem_create_buttons(self, model, elem_per_raw=2):

        buttons = []
        if 'change' in self.actions:
            if type(self.updating_fields) == list and len(self.updating_fields):
                updating_fields = self.updating_fields
            else:
                updating_fields = list(self.model_form.base_fields.keys())

            raw_elems = []
            for field in updating_fields:
                if type(self.model_form.base_fields[field].widget) != HiddenInput:
                    if len(raw_elems) >= elem_per_raw:
                        buttons.append(raw_elems)
                        raw_elems = []

                    raw_elems.append(
                        inlinebutt(
                            text=f'🔄 {self.model_form.base_fields[field].label}',
                            callback_data=self.generate_message_callback_data(
                                self.command_routings['command_routing_change'],
                                model.id,
                                field,
                            )
                        )
                    )

            if len(raw_elems):
                buttons.append(raw_elems)

        if 'delete' in self.actions:
            buttons.append(
                [inlinebutt(
                    text=_('❌ Delete #%(model_id)s') % {'model_id': model.id},
                    callback_data=self.generate_message_callback_data(
                        self.command_routings['command_routing_delete'],
                        model.id,
                    )
                )]
            )

        if 'show_list' in self.actions:
            buttons.append(
                [inlinebutt(
                    text=_('🔙 Return to list'),
                    callback_data=self.generate_message_callback_data(
                        self.command_routings['command_routing_show_list'],
                    )
                )]
            )
        return buttons

    def gm_show_elem_or_list_fields(self, model, is_elem=False, **kwargs):
        """

        :param model:
        :param is_elem: True for show_elem and false for show_list
        :return:
        """

        if 'full_show' in kwargs:
            is_elem = kwargs['full_show']

        mess = ''
        for field_name, field in self.model_form.base_fields.items():
            if type(field.widget) != HiddenInput:
                mess += f'<b>{field.label}</b>: {self.gm_value_str(model, field, field_name)}\n'

        return mess

    def gm_value_str(self, model, field, field_name, try_field='name'):
        value = getattr(model, field_name, "")

        if value:
            if issubclass(type(value), models.Manager):
                value = value.all()

            if issubclass(value.__class__, models.Model):
                value = f'{getattr(value, try_field, "# " + str(value.pk))}'
            elif (type(value) in [list, models.QuerySet]) and all(map(lambda x: issubclass(x.__class__, models.Model), value)):
                value = ', '.join([f'{getattr(x, try_field, "# " + str(x.pk))}' for x in value])
        elif type(value) != bool:
            value = ''

        is_choice_field = issubclass(type(field), ChoiceField)
        if is_choice_field or field_name in self.prechoice_fields_values:
            choices = field.choices if is_choice_field else self.prechoice_fields_values[field_name]
            choice = list(filter(lambda x: x[0] == value, choices))
            if len(choice):
                value = choice[0][1]
        return value

    def gm_show_list_elem_info(self, model, it_m:int) -> str:
        mess = f'{it_m}. {self.viewset_name} #{model.pk}\n' if self.use_name_and_id_in_elem_showing else f'{it_m}. '
        mess += self.gm_show_elem_or_list_fields(model)
        mess += '\n\n'
        return mess

    def gm_show_list_button_names(self, it_m, model):
        return f'{it_m}. {self.viewset_name} #{ model.pk}'

    def gm_show_list_create_pagination(
            self,
            page: int,
            count_models: int,
            first_this_page: int,
            first_next_page: int,
            page_model_amount: int
    ) -> []:
        prev_page_button = inlinebutt(
            text=f'◀️️️',
            callback_data=self.generate_message_callback_data(
                self.command_routings['command_routing_show_list'], str(page - 1),
            )
        )
        next_page_button = inlinebutt(
            text=f'️▶️️',
            callback_data=self.generate_message_callback_data(
                self.command_routings['command_routing_show_list'], str(page + 1),
            )
        )

        buttons = []
        if page_model_amount < count_models:
            if (first_this_page > 0) and (first_next_page < count_models):
                buttons = [[prev_page_button, next_page_button]]
            elif first_this_page == 0:
                buttons = [[next_page_button]]
            elif first_next_page >= count_models:
                buttons = [[prev_page_button]]
            else:
                logging.error(
                    f'unreal situation {count_models}, {page_model_amount}, {first_this_page}, {first_next_page}'
                )
        return buttons

    def construct_utrl(self, *args, add_filters=True, **kwargs):
        f_args = list(args)
        if add_filters:
            f_args = f_args[:1] + self.foreign_filters + f_args[1:]
        return self.ARGS_SEPARATOR_SYMBOL.join(map(lambda x: str(x), f_args))

    def generate_message_callback_data(self, *args, add_filters=True, **kwargs):
        return self.prefix + self.construct_utrl(*args, add_filters=add_filters, **kwargs)

    def gm_callback_data(self, method, *args, **kwargs):
        return self.generate_message_callback_data(
            self.command_routings[f'command_routing_{method}'],
            *args,
            **kwargs,
        )

    def gm_next_field_choice_buttons(
            self,
            next_field,
            func_response,
            choices,
            selected_variants,
            callback_path,
            self_variant=True,
            show_next_button=True,
    ):
        is_boolean_field = issubclass(type(self.model_form.base_fields[next_field]), BooleanField)
        is_choice_field = issubclass(type(self.model_form.base_fields[next_field]), ChoiceField)
        is_multichoice_field = self.model_form.base_fields[next_field].__class__ == ModelMultipleChoiceField

        buttons = list([
            [inlinebutt(
                text=text if not value in selected_variants else f'✅ {text}',
                callback_data=callback_path(value)
            )] for value, text in choices
        ])

        if self_variant and not (is_choice_field or is_boolean_field):
            buttons.append([
                inlinebutt(text=_('Write the value'), callback_data=callback_path(self.WRITE_MESSAGE_VARIANT_SYMBOLS))
            ])
        if show_next_button and is_multichoice_field:
            buttons.append([
                inlinebutt(text=_('Next'), callback_data=callback_path(self.GO_NEXT_MULTICHOICE_SYMBOLS))
            ])
        return buttons

    def gm_next_field(self, next_field, mess='', func_response='create', instance_id=None):

        is_choice_field = issubclass(type(self.model_form.base_fields[next_field]), ChoiceField)

        if is_choice_field or self.prechoice_fields_values.get(next_field):
            buttons = []
            field = self.model_form.base_fields[next_field]

            mess += self.show_texts_dict['gm_next_field'] % {'label': field.label}
            if field.help_text:
                mess += f'{field.help_text}\n\n'

            if instance_id:
                callback_path = lambda x: self.generate_message_callback_data(
                    self.command_routings[f'command_routing_{func_response}'], instance_id, next_field, x
                )
            else:
                callback_path = lambda x: self.generate_message_callback_data(
                    self.command_routings[f'command_routing_{func_response}'], next_field, x
                )
            # todo: add beautiful text view

            choices = self.prechoice_fields_values.get(next_field) or \
                      list(filter(lambda x: x[0], self.model_form.base_fields[next_field].choices))

            selected_variants = []
            if self.form and self.form.is_valid() and next_field in self.form.cleaned_data:
                field_value = self.form.cleaned_data[next_field]
                selected_variants = [field_value]

                if field_value:
                    # if issubclass(type(value), models.Manager):
                    #     value = value.all()

                    if issubclass(field_value.__class__, models.Model):
                        selected_variants = [field_value.pk]
                    elif (type(field_value) in [set, list, models.QuerySet]):
                        if all(map(lambda x: issubclass(x.__class__, models.Model), field_value)):
                            selected_variants = list([el.pk for el in field_value])
                        else:
                            selected_variants = field_value

            buttons += self.gm_next_field_choice_buttons(
                next_field, func_response, choices, selected_variants, callback_path
            )

            # required=False also for multichoice field or field with default value,
            # so it is better create button in app logic.

            # if not self.model_form.base_fields[next_field].required:
            #     buttons.append([
            #         inlinebutt(
            #             text=self.show_texts_dict['leave_blank_button_text'],
            #             callback_data=callback_path(self.NONE_VARIANT_SYMBOLS)
            #         )
            #     ])

            if self.cancel_adding_button and func_response == 'create':
                buttons.append([self.cancel_adding_button])
            elif self.show_cancel_updating_button and instance_id and 'show_elem' in self.actions:
                buttons.append([inlinebutt(
                    text=_('⬅️ Go back'),
                    callback_data=self.generate_message_callback_data(
                        self.command_routings[f'command_routing_show_elem'],
                        instance_id
                    )
                )])

            return self.CHAT_ACTION_MESSAGE, (mess, buttons)
        else:
            return self.gm_self_variant(next_field, mess, func_response=func_response, instance_id=instance_id)

    def gm_success_created(self, model_or_pk=None, mess=''):

        mess += self.show_texts_dict['gm_success_created'] % {'viewset_name': self.viewset_name}

        if model_or_pk:
            return self.show_elem(model_or_pk, mess)
        return self.CHAT_ACTION_MESSAGE, (mess, [])

    def gm_value_error(self, field_name, errors, mess='', func_response='create', instance_id=None):
        field = self.model_form.base_fields[field_name]
        mess += self.show_texts_dict['gm_value_error'] % {'label': field.label, 'errors': errors}

        # error could be only in self_variant?
        return self.gm_self_variant(field_name, mess, func_response=func_response, instance_id=instance_id)

    def gm_self_variant(self, field_name, mess='', func_response='create', instance_id=None):
        field = self.model_form.base_fields[field_name]

        mess += self.show_texts_dict['gm_self_variant'] % {'label': field.label}

        if field.help_text:
            mess += f'{field.help_text}\n\n'

        if instance_id:
            current_utrl = self.generate_message_callback_data(
                self.command_routings[f'command_routing_{func_response}'],
                instance_id,
                field_name
            )
        else:
            current_utrl = self.generate_message_callback_data(
                self.command_routings[f'command_routing_{func_response}'],
                field_name
            )

        self.user.current_utrl = current_utrl
        self.user.save()

        # add return buttons
        buttons = []

        if not self.model_form.base_fields[field_name].required:
            if func_response == 'create':
                button_args = [func_response, field_name, self.NONE_VARIANT_SYMBOLS]
            else:
                button_args = [func_response, instance_id, field_name, self.NONE_VARIANT_SYMBOLS]

            buttons.append([
                inlinebutt(
                    text=self.show_texts_dict['leave_blank_button_text'],
                    callback_data=self.gm_callback_data(*button_args)
                )
            ])

        if self.cancel_adding_button and func_response == 'create':
            buttons.append([self.cancel_adding_button])

        elif self.show_cancel_updating_button and instance_id and 'show_elem' in self.actions:
            buttons.append([inlinebutt(
                text=_('⬅️ Go back'),
                callback_data=self.generate_message_callback_data(
                    self.command_routings[f'command_routing_show_elem'],
                    instance_id
                )
            )])
        return self.CHAT_ACTION_MESSAGE, (mess, buttons)

    def gm_no_elem(self, model_id):
        mess = self.show_texts_dict['gm_no_elem'] % {
            'viewset_name': self.viewset_name,
            'model_id': model_id,
        }
        return self.CHAT_ACTION_MESSAGE, (mess, [])

    def gm_delete_getting_confirmation(self, model):
        mess = self.show_texts_dict['confirm_deleting'] % {
            'viewset_name': self.viewset_name,
            'model_id': f'#{model.id}' or '',
        }
        buttons = [
            [inlinebutt(
                text=self.show_texts_dict['confirm_delete_button_text'],
                callback_data=self.gm_callback_data(
                    'delete',
                    model.id,
                    '1'  # True
                )
            )]
        ]
        if 'show_elem' in self.actions:
            buttons += [
                [inlinebutt(
                    text=_('🔙 Back'),
                    callback_data=self.gm_callback_data(
                        'show_elem',
                        model.id,
                    )
                )]
            ]
        return mess, buttons

    def gm_delete_successfully(self, model):
        mess = self.show_texts_dict['succesfully_deleted'] % {
            'viewset_name': self.viewset_name,
            'model_id': f'#{model.id}' or '',
        }

        buttons = []
        if 'show_list' in self.actions:
            buttons += [
                [inlinebutt(
                    text=_('🔙 Return to list'),
                    callback_data=self.generate_message_callback_data(
                        self.command_routings['command_routing_show_list'],
                    )
                )]
            ]
        return mess, buttons




