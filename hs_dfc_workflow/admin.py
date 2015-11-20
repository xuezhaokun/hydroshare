__author__ = 'Mohamed Morsy'
from mezzanine.pages.admin import PageAdmin

from django.contrib import admin

from hs_dfc_workflow.models import DFCWorkflowResource

admin.site.register(DFCWorkflowResource, PageAdmin)
