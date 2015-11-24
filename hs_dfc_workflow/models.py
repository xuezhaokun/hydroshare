__author__ = 'Mohamed Morsy'
from lxml import etree

from django.contrib.contenttypes import generic
from django.db import models

from mezzanine.pages.page_processors import processor_for

import os

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.hydroshare import utils

# extended metadata elements for DFC Workflow resource type
class WorkflowInput(AbstractMetaDataElement):
    term = 'WorkflowInput'
    inputType = models.CharField(max_length=200, null=True, blank=True, verbose_name='Input files type')
    inputDescription = models.TextField(verbose_name='Input files description')

    def __unicode__(self):
        return self.inputType

class WorkflowOutput(AbstractMetaDataElement):
    term = 'WorkflowOutput'
    outputType = models.CharField(max_length=200, null=True, blank=True, verbose_name='Output files type')
    outputDescription = models.TextField(verbose_name='Output files description')

    def __unicode__(self):
        return self.outputType

class WorkflowProcessors(AbstractMetaDataElement):
    term = 'WorkflowProcessors'
    processorsNumber = models.PositiveIntegerField(max_length=200, null=True, blank=True, verbose_name='Processors number')
    processorsType = models.CharField(max_length=200, null=True, blank=True, verbose_name='Processors type')
    processorsDescription = models.TextField(verbose_name='Processors description')
    has_CodeRepository = models.BooleanField(default=False, verbose_name='Has code repository?')
    codeRepositoryURI = models.URLField(null=True, blank=True, verbose_name='Code repository URI')
    has_DockerImage = models.BooleanField(default=False, verbose_name='Has Docker image?')
    dockerImageURI = models.URLField(null=True, blank=True, verbose_name='Docker image URI')

    def __unicode__(self):
        return self.processorsType

    @property
    def hasDockerImage(self):
        if self.has_DockerImage:
            return "Yes"
        else:
            return "No"

    @property
    def hasCodeRepository(self):
        if self.has_CodeRepository:
            return "Yes"
        else:
            return "No"

class IrodsWorkflowProcessors(AbstractMetaDataElement):
    term = 'IrodsWorkflowProcessors'
    irodsProcessorsNumber = models.PositiveIntegerField(max_length=200, null=True, blank=True, verbose_name='iRODS Processors number')
    irodsProcessorsType = models.CharField(max_length=200, null=True, blank=True, verbose_name='iRODS Processors type')
    irodsProcessorsDescription = models.TextField(verbose_name='iRODS Processors description')
    has_CodeRepository = models.BooleanField(default=False, verbose_name='Has code repository?')
    codeRepositoryURI = models.URLField(null=True, blank=True, verbose_name='Code repository URI')

    def __unicode__(self):
        return self.irodsProcessorsType

    @property
    def hasCodeRepository(self):
        if self.has_CodeRepository:
            return "Yes"
        else:
            return "No"

# DFC Workflow Resource type
class DFCWorkflowResource(BaseResource):
    objects = ResourceManager("DFCWorkflowResource")

    class Meta:
        verbose_name = 'DFC Workflow Resource'
        proxy = True

    @property
    def metadata(self):
        md = DFCWorkflowMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

    def has_required_content_files(self):
        mss_file_exists = False
        mpf_file_exists = False
        if len(self.get_supported_upload_file_types()) > 0:
            if self.files.all().count() >= 2:
                for res_file in self.files.all():
                     ext = os.path.splitext(res_file.resource_file.name)[-1]
                     if ext == '.mss':
                         mss_file_exists = True
                     elif ext == '.mpf':
                         mpf_file_exists = True

                return mss_file_exists and mpf_file_exists
            else:
                return False
        else:
            return True

processor_for(DFCWorkflowResource)(resource_processor)

# metadata container class
class DFCWorkflowMetaData(CoreMetaData):
    _workflow_input = generic.GenericRelation(WorkflowInput)
    _workflow_output = generic.GenericRelation(WorkflowOutput)
    _workflow_processors = generic.GenericRelation(WorkflowProcessors)
    _irods_workflow_processors = generic.GenericRelation(IrodsWorkflowProcessors)

    @property
    def workflow_input(self):
        return self._workflow_input.all().first()

    @property
    def workflow_output(self):
        return self._workflow_output.all().first()

    @property
    def workflow_processors(self):
        return self._workflow_processors.all().first()

    @property
    def irods_workflow_processors(self):
        return self._irods_workflow_processors.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(DFCWorkflowMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('WorkflowInput')
        elements.append('WorkflowOutput')
        elements.append('WorkflowProcessors')
        elements.append('IrodsWorkflowProcessors')
        return elements

    def get_xml(self, pretty_print=True):
        # get the xml string representation of the core metadata elements
        xml_string = super(DFCWorkflowMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.workflow_input:
            workflowInputFields = ['inputType', 'inputDescription']
            self.add_metadata_element_to_xml(container,self.workflow_input,workflowInputFields)

        if self.workflow_output:
            workflowOutputFields = ['outputType', 'outputDescription']
            self.add_metadata_element_to_xml(container,self.workflow_output,workflowOutputFields)

        if self.workflow_processors:
            workflowProcessorsFields = ['processorsNumber', 'processorsType', 'processorsDescription', \
                                        'hasCodeRepository', 'codeRepositoryURI', 'hasDockerImage', 'dockerImageURI']
            self.add_metadata_element_to_xml(container,self.workflow_processors,workflowProcessorsFields)

        if self.irods_workflow_processors:
            irodsWorkflowOutputFields = ['irodsProcessorsNumber', 'irodsProcessorsType', 'irodsProcessorsDescription', \
                                         'hasCodeRepository', 'codeRepositoryURI']
            self.add_metadata_element_to_xml(container,self.irods_workflow_processors,irodsWorkflowOutputFields)


        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(DFCWorkflowMetaData, self).delete_all_elements()
        self._workflow_input.all().delete()
        self._workflow_output.all().delete()
        self._workflow_processors.all().delete()
        self._irods_workflow_processors.all().delete()

import receivers