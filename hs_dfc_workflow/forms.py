__author__ = 'Mohamed Morsy'
from django.forms import ModelForm
from django import forms

from crispy_forms import layout
from crispy_forms.layout import Layout, Field, HTML

from hs_core.forms import BaseFormHelper
from hs_core.hydroshare import users

from hs_dfc_workflow.models import WorkflowInput, WorkflowOutput, WorkflowProcessors, IrodsWorkflowProcessors

class MetadataField(layout.Field):
          def __init__(self, *args, **kwargs):
              kwargs['css_class'] = 'form-control input-sm'
              super(MetadataField, self).__init__(*args, **kwargs)

class WorkflowInputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('inputType'),
                        MetadataField('inputDescription'),
                 )
        kwargs['element_name_label'] = 'Workflow Input'
        super(WorkflowInputFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class WorkflowInputForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(WorkflowInputForm, self).__init__(*args, **kwargs)
        self.helper = WorkflowInputFormHelper(allow_edit, res_short_id, element_id, element_name='WorkflowInput')

    class Meta:
        model = WorkflowInput
        fields = ('inputType',
                  'inputDescription',)

class WorkflowInputValidationForm(forms.Form):
    inputType = forms.CharField(max_length=200, required=False)
    inputDescription = forms.CharField(max_length=5000, required=False)

class WorkflowOutputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('outputType'),
                        MetadataField('outputDescription'),
                 )
        kwargs['element_name_label'] = 'Workflow Output'
        super(WorkflowOutputFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class WorkflowOutputForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(WorkflowOutputForm, self).__init__(*args, **kwargs)
        self.helper = WorkflowOutputFormHelper(allow_edit, res_short_id, element_id, element_name='WorkflowOutput')

    class Meta:
        model = WorkflowOutput
        fields = ('outputType',
                  'outputDescription',)

class WorkflowOutputValidationForm(forms.Form):
    outputType = forms.CharField(max_length=200, required=False)
    outputDescription = forms.CharField(max_length=5000, required=False)

class WorkflowProcessorsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('processorsNumber'),
                        MetadataField('processorsType'),
                        MetadataField('processorsDescription'),
                        MetadataField('has_DockerImage'),
                        MetadataField('dockerImageURI'),
                 )
        kwargs['element_name_label'] = 'Workflow Processors'
        super(WorkflowProcessorsFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class WorkflowProcessorsForm(ModelForm):
    has_DockerImage = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect(attrs={'style': 'width:auto;margin-top:-5px'}))
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(WorkflowProcessorsForm, self).__init__(*args, **kwargs)
        self.helper = WorkflowProcessorsFormHelper(allow_edit, res_short_id, element_id, element_name='WorkflowProcessors')

    class Meta:
        model = WorkflowProcessors
        fields = ('processorsNumber',
                  'processorsType',
                  'processorsDescription',
                  'has_DockerImage',
                  'dockerImageURI',)

class WorkflowProcessorsValidationForm(forms.Form):
    processorsNumber = forms.CharField(max_length=200, required=False)
    processorsType = forms.CharField(max_length=200, required=False)
    processorsDescription = forms.CharField(max_length=5000, required=False)
    has_DockerImage = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)
    dockerImageURI = forms.URLField(required=False)

    def clean_has_DockerImage(self):
        data = self.cleaned_data['has_DockerImage']
        if data == u'False':
            return False
        else:
            return True

class IrodsWorkflowProcessorsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('irodsProcessorsNumber'),
                        MetadataField('irodsProcessorsType'),
                        MetadataField('irodsProcessorsDescription'),
                 )
        kwargs['element_name_label'] = 'iRODS WSO Processors'
        super(IrodsWorkflowProcessorsFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class IrodsWorkflowProcessorsForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(IrodsWorkflowProcessorsForm, self).__init__(*args, **kwargs)
        self.helper = IrodsWorkflowProcessorsFormHelper(allow_edit, res_short_id, element_id, element_name='IrodsWorkflowProcessors')

    class Meta:
        model = IrodsWorkflowProcessors
        fields = ('irodsProcessorsNumber',
                  'irodsProcessorsType',
                  'irodsProcessorsDescription',)

class IrodsWorkflowProcessorsValidationForm(forms.Form):
    processorsNumber = forms.CharField(max_length=200, required=False)
    processorsType = forms.CharField(max_length=200, required=False)
    processorsDescription = forms.CharField(max_length=5000, required=False)