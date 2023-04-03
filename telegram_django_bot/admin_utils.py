from django_admin_listfilter_dropdown.filters import RelatedOnlyDropdownFilter
from django_json_widget.widgets import JSONEditorWidget
from django import forms


class CustomRelatedOnlyDropdownFilter(RelatedOnlyDropdownFilter):
    template = 'dropdown_filter1.html'
    ordering_field = 'id'

    def field_choices(self, field, request, model_admin):
        pk_qs = model_admin.get_queryset(request).distinct().values_list('%s__pk' % self.field_path, flat=True)
        return field.get_choices(include_blank=False, limit_choices_to={'pk__in': pk_qs}, ordering=[self.ordering_field,])


class DefaultOverrideAdminWidgetsForm(forms.ModelForm):
    json_fields = []
    list_json_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.json_fields:
            self.fields[field].widget = JSONEditorWidget()

        for field in self.list_json_fields:
            self.fields[field].widget = JSONEditorWidget(attrs={"value": "[]"})

