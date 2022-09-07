from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass, ErrorList, ErrorDict
from django.forms.models import BaseModelForm, ModelFormMetaclass
from django.forms import HiddenInput

# todo: PreChoise logic to fields
# todo: support media

# class TelegaErrorList(ErrorList):
#     def __str__(self):
#         return self.as_text()
#

class TelegaErrorDict(ErrorDict):
    def __str__(self):
        return self.as_text()


class BaseTelegaForm(BaseForm):
    # field_order = None
    form_name = ''

    def _init_helper_get_data(self, user, data):
        # import pdb;pdb.set_trace()

        curr_data = {}
        if user.current_utrl_form.get('form_name') == self.__class__.__name__:
            curr_data = user.current_utrl_form.get('form_data')
        else:
            user.clear_status()

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
        # self.error_class = TelegaErrorList

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
        self._errors = TelegaErrorDict() # only for change TelegaErrorDict()
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


class BaseTelegaModelForm(BaseTelegaForm, BaseModelForm):
    def __init__(self, user, data=None, files=None, initial=None, instance=None):
        self.user = user
        if instance is None:
            data = self._init_helper_get_data(user, data)

        BaseModelForm.__init__(self, data, files, initial=initial, instance=instance)
        # self.error_class = TelegaErrorList

        self.next_field = None
        if instance is None:
            self.fields, self.next_field = self._init_helper_fields_detection(data)

    def save(self, commit=True):
        # import pdb; pdb.set_trace()

        # there was add condition " len(set(self.base_fields.keys()) - set(self.fields.keys())) == 0: " --
        # but with hidden unnecessary field could be len(set(self.base_fields.keys()) - set(self.fields.keys())) > 0
        if self.is_valid() and self.next_field is None:
            # full valid form
            BaseModelForm.save(self, commit=commit)
            self.user.clear_status()
        else:
            BaseTelegaForm.save(self, commit=commit)


class TelegaForm(BaseTelegaForm, metaclass=DeclarativeFieldsMetaclass):
    """just for terminate metaclass"""


class TelegaModelForm(BaseTelegaModelForm, metaclass=ModelFormMetaclass):
    """just for terminate metaclass"""


