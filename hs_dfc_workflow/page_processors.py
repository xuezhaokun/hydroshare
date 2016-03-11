__author__ = 'Mohamed Morsy'
from crispy_forms.bootstrap import AccordionGroup
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context

from hs_dfc_workflow.models import DFCWorkflowResource
from hs_dfc_workflow.forms import WorkflowInputForm, WorkflowOutputForm, WorkflowProcessorsForm, IrodsWorkflowProcessorsForm

from mezzanine.pages.page_processors import processor_for

@processor_for(DFCWorkflowResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=None, request=request)
        extended_metadata_exists = False
        if content_model.metadata.workflow_input or \
                content_model.metadata.workflow_output or \
                content_model.metadata.irods_workflow_processors or \
                content_model.metadata.workflow_processors:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['workflow_input'] = content_model.metadata.workflow_input
        context['workflow_output'] = content_model.metadata.workflow_output
        context['irods_workflow_processors'] = content_model.metadata.irods_workflow_processors
        context['workflow_processors'] = content_model.metadata.workflow_processors
    else:
        workflow_input_form = WorkflowInputForm(instance=content_model.metadata.workflow_input,
                                            res_short_id=content_model.short_id,
                                            element_id=content_model.metadata.workflow_input.id if content_model.metadata.workflow_input else None)

        workflow_output_form = WorkflowOutputForm(instance=content_model.metadata.workflow_output,
                                          res_short_id=content_model.short_id,
                                          element_id=content_model.metadata.workflow_output.id if content_model.metadata.workflow_output else None)

        irods_workflow_processors_form = IrodsWorkflowProcessorsForm(instance=content_model.metadata.irods_workflow_processors,
                                          res_short_id=content_model.short_id,
                                          element_id=content_model.metadata.irods_workflow_processors.id if content_model.metadata.irods_workflow_processors else None)

        workflow_processors_form = WorkflowProcessorsForm(instance=content_model.metadata.workflow_processors,
                                          res_short_id=content_model.short_id,
                                          element_id=content_model.metadata.workflow_processors.id if content_model.metadata.workflow_processors else None)


        ext_md_layout = Layout(
                           HTML("<div class='row'><div class='col-xs-12 col-sm-6'><div class='form-group' id='workflowinput'> "
                                '{% load crispy_forms_tags %} '
                                '{% crispy workflow_input_form %} '
                                '</div>'),

                           HTML('<div class="form-group" id="workflowprocessors"> '
                                '{% load crispy_forms_tags %} '
                                '{% crispy workflow_processors_form %} '
                                '</div></div> '),

                           HTML('<div class="col-xs-12 col-sm-6"><div class="form-group" id="workflowoutput"> '
                                '{% load crispy_forms_tags %} '
                                '{% crispy workflow_output_form %} '
                                '</div> '),

                           HTML('<div class="form-group" id="irodsworkflowprocessors"> '
                                '{% load crispy_forms_tags %} '
                                '{% crispy irods_workflow_processors_form %} '
                                '</div> '),
        )


        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout, request=request)

        context['resource_type'] = 'DFC Workflow Resource'
        context['workflow_input_form'] = workflow_input_form
        context['workflow_output_form'] = workflow_output_form
        context['irods_workflow_processors_form'] = irods_workflow_processors_form
        context['workflow_processors_form'] = workflow_processors_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context