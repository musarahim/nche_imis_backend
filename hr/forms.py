from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Div, Fieldset, Layout, Submit
from django import forms
from unfold.contrib.forms.widgets import UnfoldAdminTextInputWidget

from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "system_account",
            "department",
            "employee_number",
            "designation",
        ]
        exclude = ['created', 'modified', 'deleted_at']
        widgets = {
            "system_account": UnfoldAdminTextInputWidget(),
            "last_name": UnfoldAdminTextInputWidget(),
            "code": UnfoldAdminTextInputWidget(),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset(
                "",
                Div(
                    Div("system_account", css_class="col-span-1"),
                    Div("department", css_class="col-span-1"),
                    css_class="grid grid-cols-1 sm:grid-cols-2 gap-4"
                ),
                Div(
                    Div("employee_number", css_class="col-span-1"),
                    Div("designation", css_class="col-span-1"),
                    css_class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3"
                ),
            ),
            ButtonHolder(
                Submit("submit", "Save", css_class="btn btn-primary")
            ),
        )
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col"
        self.helper.field_class = "col-lg-12"