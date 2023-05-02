from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass, ErrorDict
from django.forms.models import BaseModelForm, ModelFormMetaclass, ModelMultipleChoiceField
from django.forms import HiddenInput
from django.db import models


# todo: PreChoise logic to fields
# todo: support media

# class TelegramErrorList(ErrorList):
#     def __str__(self):
#         return self.as_text()
#

class TelegramErrorDict(ErrorDict):
    def __str__(self):
        return self.as_text()


class BaseTelegramForm(BaseForm):
    # field_order = None

    # form_name = ''  # make sure that this name is unique!! It is used for storing in User details while adding or
    # # updating element attributes.
    # todo: add check if there are forms with same form_names

    @property
    def form_name(self) -> str:
        """ just for easy creating class. So, the name of class should be unique  """
        return self.__str__()

    def __repr__(self):
        return f'{self.__class__.__name__}'

    def __str__(self):
        return f'{self.__class__.__name__}'


    def _multichoice_intersection(self, set_from_user, set_from_db):
        # todo: in another place should be check with check from field type

        if len(set_from_db):
            db_values_type = type(next(iter(set_from_db)))  # int (if standart pk)
            set_from_user = set([db_values_type(elem) for elem in set_from_user])

        if set_from_db.intersection(set_from_user):
            new_pks = set_from_db - set_from_user
        else:
            if len(set_from_user):
                new_pks = set_from_db.union(set_from_user)
            else:
                new_pks = []
        return list(new_pks)

    def _init_helper_get_data(self, user, data):
        # import pdb;pdb.set_trace()

        curr_data = {}
        if user.current_utrl_form.get('form_name') == self.__class__.__name__:
            curr_data = user.current_utrl_form.get('form_data')
        else:
            user.clear_status()

        for model_field in self.base_fields:
            if self.base_fields[model_field].__class__ == ModelMultipleChoiceField and model_field in data:
                models_from_user = set(data.pop(model_field, []) or [])
                models_from_db = set(curr_data.pop(model_field, []))
                curr_data[model_field] = self._multichoice_intersection(models_from_user, models_from_db)

        if type(data) is dict:
            curr_data.update(data)

        data = curr_data
        return data

    def _init_helper_fields_detection(self, data):
        filled_fields = {}
        not_filled_fields = []

        for field_name, elem in self.fields.items():
            if field_name in data.keys():
                filled_fields[field_name] = elem
            elif type(elem.widget) != HiddenInput:
                not_filled_fields.append(field_name)

        # if len(filled_fields) == 0:
        #     first_field_couple = list(self.fields.items())[0]
        #     filled_fields[first_field_couple[0]] = first_field_couple[1]

        next_field = not_filled_fields[0] if len(not_filled_fields) else None
        return  filled_fields, next_field


    def __init__(self, user, data=None, files=None, initial=None):

        self.user = user
        data = self._init_helper_get_data(user, data)

        super().__init__(data, files, initial=initial)
        # self.error_class = TelegramErrorList

        self.fields, self.next_field = self._init_helper_fields_detection(data)

    def save(self, commit=True):
        """ save temp data to user data"""
        if self.is_valid():
            self.user.save_form_in_db(self.__class__.__name__, self.cleaned_data, do_save=commit)
        else:
            raise ValueError('cant save unvalid data')

    def get_next_field(self):
        """info about next field for full validation (creating) form"""
        return self.next_field

    def full_clean(self):
        """
        Clean all of self.data and populate self._errors and self.cleaned_data.
        """
        self._errors = TelegramErrorDict()  # only for change TelegramErrorDict()
        if not self.is_bound:  # Stop further processing.
            return
        self.cleaned_data = {}
        # If the form is permitted to be empty, and none of the form data has
        # changed from the initial data, short circuit any validation.
        if self.empty_permitted and not self.has_changed():
            return

        self._clean_fields()
        self._clean_form()
        self._post_clean()


class BaseTelegramModelForm(BaseTelegramForm, BaseModelForm):
    def __init__(self, user, data=None, files=None, initial=None, instance=None):
        self.user = user
        if instance is None:
            data = self._init_helper_get_data(user, data)
        else:
            for model_field in self.base_fields:
                use_from_db = False
                if hasattr(instance, model_field):
                    if self.base_fields[model_field].__class__ == ModelMultipleChoiceField:
                        info_from_user = data.get(model_field)
                        if not info_from_user is None:
                            get_from_user_pks = set(info_from_user)
                            get_from_db = getattr(instance, model_field).all()
                            get_from_db_pks = set(el.pk for el in get_from_db)

                            data[model_field] = self._multichoice_intersection(get_from_user_pks, get_from_db_pks)
                        else:
                            use_from_db = True

                    elif not model_field in data:
                        use_from_db = True

                    if use_from_db:
                        data[model_field] = getattr(instance, model_field)
                        if issubclass(type(data[model_field]), models.Manager):
                            data[model_field] = data[model_field].all()
                else:
                    raise ValueError(
                        f'fields in TelegramModelForm should have same name: {model_field}, {instance.__dict__.keys()}')

        BaseModelForm.__init__(self, data, files, initial=initial, instance=instance)
        # self.error_class = TelegramErrorList

        self.next_field = None
        self.fields, self.next_field = self._init_helper_fields_detection(data)

    def save(self, commit=True, is_completed=True):
        """

        :param commit: save to db (in user on in model)
        :param is_completed: special signal -- if not yet completed and no instance, then save only to user
        :return:
        """

        # there was add condition " len(set(self.base_fields.keys()) - set(self.fields.keys())) == 0: " --
        # but with hidden unnecessary field could be len(set(self.base_fields.keys()) - set(self.fields.keys())) > 0
        if self.is_valid() and self.next_field is None and (is_completed or self.instance.pk):
            # full valid form
            BaseModelForm.save(self, commit=commit)
            self.user.clear_status()
        else:
            BaseTelegramForm.save(self, commit=commit)


class TelegramForm(BaseTelegramForm, metaclass=DeclarativeFieldsMetaclass):
    """just for executing metaclass"""


class TelegramModelForm(BaseTelegramModelForm, metaclass=ModelFormMetaclass):
    """just for executing metaclass"""

