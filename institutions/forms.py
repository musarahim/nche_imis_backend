
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms

from .models import CertificationAndClassification, Institution


class CertificationAndClassificationForm(forms.ModelForm):
    class Meta:
        model = CertificationAndClassification
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CertificationAndClassificationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.layout = Layout(
            'institution_name',
            'certification_name',
            'certification_year',
            'certification_number',
            'certification_status',
            'certification_date',
            'certification_agency',
            'certification_type',
            'certification_description',
            'classification_name',
            'classification_number',
            'classification_description',
        )
        self.helper.form_class = 'form-vertical'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        