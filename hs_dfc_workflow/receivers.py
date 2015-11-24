__author__ = 'Mohamed Morsy'
from django.dispatch import receiver

from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update,pre_create_resource

from hs_dfc_workflow.forms import WorkflowInputValidationForm, WorkflowOutputValidationForm,\
    WorkflowProcessorsValidationForm, IrodsWorkflowProcessorsValidationForm
from hs_dfc_workflow.models import DFCWorkflowResource

# @receiver(pre_create_resource, sender=DFCWorkflowResource)
# def dfcworkflow_pre_create_resource(sender, **kwargs):
#     metadata = kwargs['metadata']
#     workflowprocessors = {'workflowprocessors': {'has_DockerImage': False}}
#     metadata.append(workflowprocessors)

@receiver(pre_metadata_element_create, sender=DFCWorkflowResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    return _process_metadata_update_create(**kwargs)


@receiver(pre_metadata_element_update, sender=DFCWorkflowResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    return _process_metadata_update_create(**kwargs)

def _process_metadata_update_create(**kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "workflowinput":
        element_form = WorkflowInputValidationForm(request.POST)
    elif element_name == 'workflowoutput':
        element_form = WorkflowOutputValidationForm(request.POST)
    elif element_name == 'workflowprocessors':
        element_form = WorkflowProcessorsValidationForm(request.POST)
    elif element_name == 'IrodsWorkflowProcessors':
        element_form = IrodsWorkflowProcessorsValidationForm(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}