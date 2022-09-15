from .telegram_lib_redefinition import (
    InlineKeyboardButtonDJ as inlinebutt
)
import re
import copy
from django.forms import HiddenInput
from django.forms.models import ModelMultipleChoiceField
from django.db import models
from django.forms.fields import ChoiceField
from .utils import add_log_action
from django.utils.translation import gettext as _


class TelegaViewSetMetaClass(type):
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        # print(name, bases, attrs)

        current_fields = []
        for key, value in list(attrs.items()):
            if key.startswith('command_routing_') and (type(value) == str) and value:
                current_fields.append((key, value))
                attrs.pop(key)
        attrs['command_routings'] = dict(current_fields)
        new_class = super().__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        command_routings = {}
        for base in reversed(new_class.__mro__):
            # Collect command_routings from base class.
            if hasattr(base, 'command_routings'):
                command_routings.update(base.command_routings)

        new_class.command_routings = command_routings
        return new_class


class TelegaViewSet(metaclass=TelegaViewSetMetaClass):
    actions = ['create', 'change', 'delete', 'show_elem', 'show_list']

    command_routing_create = 'cr'
    command_routing_change = 'up'
    command_routing_delete = 'de'
    command_routing_show_elem = 'se'
    command_routing_show_list = 'sl'

    WRITE_MESSAGE_VARIANT_SYMBOLS = '!WMVS!'
    CHAT_ACTION_MESSAGE = 'message'

    telega_form = None
    queryset = None
    viewset_name = ''

    prechoice_fields_values = {}
    updating_fields = None

    cancel_adding_button = None
    show_cancel_updating_button = True

    # on_created_success_action = None
    # cancel_action = None
    #
    # return_button = None

    def construct_utrl(self, *args):
        return '-'.join(map(lambda x: str(x), args))

    def get_utrl_params(self, utrl):
        return utrl.split('-')

    def __init__(self, prefix):
        self.user = None
        self.bot = None
        self.update = None
        self.form = None

        self.viewset_routing = {}

        if self.queryset is None:
            raise ValueError('queryset could not be None')

        if self.telega_form is None:
            raise ValueError('telega_form could not be None')

        for action in self.actions:
            cr_action = f'command_routing_{action}'
            if not cr_action in self.command_routings.keys():
                raise ValueError(
                    f'for action {action} must be determinate {cr_action},'
                    f' but list is {self.command_routings.keys()}'
                )

            self.viewset_routing[self.command_routings[cr_action]] = self.__getattribute__(action)

        self.prefix = prefix.replace('^', '').replace('$', '')


    def dispatch(self, bot, update, user):
        """ terminate function for response """

        self.bot = bot
        self.update = update
        self.user = user

        if update.callback_query:
            utrl = update.callback_query.data
        else:
            utrl = user.current_utrl

        self.utrl = utrl

        print(utrl)
        # import pdb; pdb.set_trace()

        utrl_args = self.get_utrl_params(re.sub(f'^{self.prefix}', '', self.utrl))
        chat_action, chat_action_args = self.viewset_routing[utrl_args[0]](*utrl_args[1:])
        if chat_action == self.CHAT_ACTION_MESSAGE:
            message, buttons = chat_action_args
            res = self.bot.edit_or_send(
                self.update,
                message,
                buttons,
            )
        else:
            raise ValueError(f'unknown chat_action {chat_action} {utrl}, {user}')

        add_log_action(self.user.id, utrl)
        return res

    def get_queryset(self):
        if self.queryset._result_cache:
            self.queryset._result_cache = None
            self.queryset._prefetch_done = False
        return self.queryset

    # def get_item(self, item):
    #     """ show info about item"""

    def create_or_update_helper(self, field, value, func_response='create', instance=None, initial_data=None):
        def check_if_multichoice_and_get_value(value):
            if self.telega_form.base_fields[field].__class__ == ModelMultipleChoiceField:
                value = value.split(',')
            return value

        if initial_data is None:
            data = {}
        else:
            data = copy.deepcopy(initial_data)

        if func_response == 'change' and instance:
            if (not value is None) or (not self.update.message is None):
                for model_field in self.telega_form.base_fields:
                    if hasattr(instance, model_field):
                        data[model_field] = getattr(instance, model_field)
                        if issubclass(type(data[model_field]), models.Manager):
                            data[model_field] = data[model_field].all()
                    else:
                        raise ValueError('fields in Telegamodelform should have same name')

                data.pop(field, None)


        want_write_self_variant = False
        if (type(field) == str) and field:
            if value:
                if value == self.WRITE_MESSAGE_VARIANT_SYMBOLS:
                    want_write_self_variant = True
                else:
                    data[field] = check_if_multichoice_and_get_value(value)
            elif self.update.message:
                data[field] = check_if_multichoice_and_get_value(self.update.message.text)

        form_kwargs = {
            'user': self.user,
            'data': data,
        }
        instance_id = None
        if instance:
            form_kwargs['instance'] = instance
            instance_id = instance.id

        self.form = self.telega_form(**form_kwargs)
        form = self.form
        if not want_write_self_variant:
            if form.is_valid():
                if form.next_field:
                    form.save()
                    res = self.generate_message_next_field(form.next_field, func_response=func_response, instance_id=instance_id)
                else:
                    form.save()
                    if func_response == 'create':
                        res = self.generate_message_success_created(self.form.instance.id)
                    else:
                        res = self.show_elem(self.form.instance.id, _('The field has been updated!\n\n'))
            else:
                res = self.generate_message_value_error(
                    field or list(form.fields.keys())[-1],
                    form.errors, func_response=func_response, instance_id=instance_id
                )
        else:
            res = self.generate_message_self_variant(field, func_response=func_response, instance_id=instance_id)
        return res

    def create(self, field=None, value=None):
        """creating item, could be several steps"""

        # import pdb;pdb.set_trace()
        if field is None and value is None:
            # then it is starting adding
            self.user.clear_status(commit=False)

        return self.create_or_update_helper(field, value, 'create')

    def change(self, model_id, field, value=None):
        """change item"""

        model = self.get_queryset().filter(id=model_id).first()
        self.user.clear_status(commit=True)

        if model:
            if (not value is None) or (not self.update.message is None):
                return self.create_or_update_helper(field, value, func_response='change', instance=model)
            else:
                return self.generate_message_next_field(field, func_response='change', instance_id=model.id)
        else:
            return self.generate_message_no_elem(model_id)

    def delete(self, model_id):
        """delete item"""

        # import pdb;pdb.set_trace()
        deleted = self.get_queryset().filter(id=model_id).delete()
        if deleted[0]:
            mess = _('The %(viewset_name)s  #%(model_id)s is successfully deleted.') % {
                'viewset_name': self.viewset_name,
                'model_id': model_id,
            }

            buttons = None
            if 'show_list' in self.actions:
                buttons = [
                    [inlinebutt(
                        text=_('🔙 Return to list'),
                        callback_data=self.generate_message_callback_data(
                            self.command_routings['command_routing_show_list'],
                        )
                    )]
                ]
            return self.CHAT_ACTION_MESSAGE, (mess, buttons)
        else:
            return self.generate_message_no_elem(model_id)

    def generate_value_str(self, model, field, field_name, try_field='name'):
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

    def generate_show_fields(self, model):
        mess = ''
        for field_name, field in self.telega_form.base_fields.items():
            if type(field.widget) != HiddenInput:
                mess += f'<b>{field.label}</b>: {self.generate_value_str(model, field, field_name)}\n'

        return mess

    def generate_elem_buttons(self, model_id, elem_per_raw=2):
        buttons = []
        if 'change' in self.actions:
            if type(self.updating_fields) == list and len(self.updating_fields):
                updating_fields = self.updating_fields
            else:
                updating_fields = list(self.telega_form.base_fields.keys())

            raw_elems = []
            for field in updating_fields:
                if type(self.telega_form.base_fields[field].widget) != HiddenInput:
                    if len(raw_elems) >= elem_per_raw:
                        buttons.append(raw_elems)
                        raw_elems = []

                    raw_elems.append(
                        inlinebutt(
                            text=f'🔄 {self.telega_form.base_fields[field].label}',
                            callback_data=self.generate_message_callback_data(
                                self.command_routings['command_routing_change'],
                                model_id,
                                field,
                            )
                        )
                    )

            if len(raw_elems):
                buttons.append(raw_elems)

        if 'delete' in self.actions:
            buttons.append(
                [inlinebutt(
                    text=_('❌ Delete #%(model_id)s') % {'model_id': model_id},
                    callback_data=self.generate_message_callback_data(
                        self.command_routings['command_routing_delete'],
                        model_id,
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

    def show_elem(self, model_id, mess=''):
        """show item"""

        model = self.get_queryset().filter(id=model_id).first()

        if model:
            mess += f'{self.viewset_name} #{model_id} \n'
            mess += self.generate_show_fields(model)

            buttons = self.generate_elem_buttons(model_id)

            return self.CHAT_ACTION_MESSAGE, (mess, buttons)
        else:
            return self.generate_message_no_elem(model_id)

    def show_list(self, page=0, per_page=10, columns=1, use_name_and_id=True):
        """show list items"""

        # import pdb;pdb.set_trace()
        mess = ''
        buttons = []
        page = int(page)

        count_models = self.get_queryset().count()
        first_this_page = page * per_page * columns
        first_next_page = (page + 1) * per_page * columns
        models = list(self.get_queryset()[first_this_page: first_next_page])

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

        if len(models) < count_models:
            if (first_this_page > 0) and (first_next_page < count_models):
                buttons = [[prev_page_button, next_page_button]]
            elif first_this_page == 0:
                buttons = [[next_page_button]]
            elif first_next_page >= count_models:
                buttons = [[prev_page_button]]
            else:
                print(f'unreal situation {count_models}, {len(models)}, {first_this_page}, {first_next_page}')

        if len(models):
            for it_m, model in enumerate(models, page * per_page * columns + 1):
                mess += f'{it_m}. {self.viewset_name} #{model.id}\n' if use_name_and_id else f'{it_m}. '
                mess += self.generate_show_fields(model)
                mess += '\n\n'
                buttons += [
                    [inlinebutt(
                        text=f'{it_m}. {self.viewset_name} #{model.id}',
                        callback_data=self.generate_message_callback_data(
                            self.command_routings['command_routing_show_elem'], model.id,
                        )
                    )]
                ]
        else:
            mess = _('There is nothing to show.')
            buttons = []

        return self.CHAT_ACTION_MESSAGE, (mess, buttons)


    def generate_message_callback_data(self, *args):
        return self.prefix + self.construct_utrl(*args)

    def generate_message_next_field(self, next_field, mess='', func_response='create', instance_id=None):
        # import pdb;pdb.set_trace()

        is_choice_field = issubclass(type(self.telega_form.base_fields[next_field]), ChoiceField)

        if is_choice_field or self.prechoice_fields_values.get(next_field):
            buttons = []
            field = self.telega_form.base_fields[next_field]
            mess += _('Please, fill the field %(label)s\n\n') % {'label': field.label}
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
                      list(filter(lambda x: x[0], self.telega_form.base_fields[next_field].choices))

            print(choices)
            buttons += list([
                [inlinebutt(
                    text=text, callback_data=callback_path(value))]
                for value, text in choices
            ])

            if not is_choice_field:
                buttons.append([
                    inlinebutt(text=_('Write the value'), callback_data=callback_path(self.WRITE_MESSAGE_VARIANT_SYMBOLS))
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
        else:
            return self.generate_message_self_variant(next_field, mess, func_response=func_response, instance_id=instance_id)

    def generate_message_success_created(self, model_id=None, mess=''):
        mess += _('The %(viewset_name)s is created! \n\n') % {'viewset_name': self.viewset_name}

        if model_id:
            return self.show_elem(model_id, mess)
        return self.CHAT_ACTION_MESSAGE, (mess, [])

    def generate_message_value_error(self, field_name, errors, mess='', func_response='create', instance_id=None):
        # import pdb;pdb.set_trace()

        field = self.telega_form.base_fields[field_name]
        mess += _('While adding %(label)s the next errors were occurred: %(errors)s\n\n') % {'label': field.label, 'errors': errors}
        return self.generate_message_self_variant(field_name, mess, func_response=func_response, instance_id=instance_id)

    def generate_message_self_variant(self, field_name, mess='', func_response='create', instance_id=None):
        # import pdb;pdb.set_trace()

        field = self.telega_form.base_fields[field_name]
        mess += _('Please, write the value for field %(label)s \n\n') % {'label': field.label}
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

    def generate_message_no_elem(self, model_id):
        mess = _('The %(viewset_name)s %(model_id)s has not been found 😱 \nPlease try again from the beginning.') % {
            'viewset_name': self.viewset_name,
            'model_id': model_id
        }
        return self.CHAT_ACTION_MESSAGE, (mess, None)
#
# class TelegaViewSet(BaseTelegaViewSet, metaclass=TelegaViewSetMetaClass):
#     pass