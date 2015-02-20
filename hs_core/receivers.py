__author__ = 'hydro'

## Note: this module has been imported in the models.py in order to receive signals
## se the end of the models.py for the import of this module

from django.dispatch import receiver
from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update
from hs_core.models import GenericResource
from forms import *
from django.contrib.auth.signals import user_logged_in

@receiver(user_logged_in)
def user_logged_in_callback(sender, **kwargs):
    if getattr(settings, 'USE_IRODS', False):
        if not getattr(settings, 'IRODS_GLOBAL_SESSION', False): # only create user session when IRODS_GLOBAL_SESSION is set to FALSE
            user = kwargs['user']
            if not user.is_superuser: # only create user session when the logged in user is not superuser
                from hs_core.models import irods_storage
                if irods_storage.session and irods_storage.environment:
                    try:
                        irods_storage.session.run('iexit full', None, irods_storage.environment.auth)
                    except:
                        pass # try to remove session if there is one, pass without error out if the previous session cannot be removed

                irods_storage.set_user_session(username=user.get_username(), password=settings.IRODS_DEFAULT_PASSWARD, userid=user.id)


# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_create, sender=GenericResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name']
    request = kwargs['request']
    if element_name == "subject":   #keywords
        element_form = SubjectsForm(data=request.POST)
    elif element_name == "description":   #abstract
        element_form = AbstractValidationForm(request.POST)
    elif element_name == "creator":
        element_form = CreatorValidationForm(request.POST)
    elif element_name == "contributor":
        element_form = ContributorValidationForm(request.POST)
    elif element_name == 'relation':
        element_form = RelationValidationForm(request.POST)
    elif element_name == 'source':
        element_form = SourceValidationForm(request.POST)
    elif element_name == 'rights':
        element_form = RightsValidationForm(request.POST)
    elif element_name == 'language':
        element_form = LanguageValidationForm(request.POST)
    elif element_name == 'date':
        element_form = ValidDateValidationForm(request.POST)
    elif element_name == 'coverage':
        if 'type' in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            element_form = CoverageTemporalForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_update, sender=GenericResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']
    if element_name == 'title':
        element_form = TitleValidationForm(request.POST)
    elif element_name == "description":   #abstract
        element_form = AbstractValidationForm(request.POST)
    elif element_name == "creator":
        # since creator is a repeatable element and creator data is displayed on the landing page
        # using formset, the data coming from a single creator form in the request for update
        # needs to be parsed to match with creator field names
        form_data = {}
        for field_name in CreatorValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]

        element_form = CreatorValidationForm(form_data)
    elif element_name == "contributor":
        # since contributor is a repeatable element and contributor data is displayed on the landing page
        # using formset, the data coming from a single contributor form in the request for update
        # needs to be parsed to match with contributor field names
        form_data = {}
        for field_name in ContributorValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]

        element_form = ContributorValidationForm(form_data)
    elif element_name == "relation":
        # since relation is a repeatable element and relation data is displayed on the landing page
        # using formset, the data coming from a single relation form in the request for update
        # needs to be parsed to match with relation field names
        form_data = {}
        for field_name in RelationValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]

        element_form = RelationValidationForm(form_data)

    elif element_name == "source":
        # since source is a repeatable element and source data is displayed on the landing page
        # using formset, the data coming from a single source form in the request for update
        # needs to be parsed to match with source field names
        form_data = {}
        for field_name in SourceValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]

        element_form = SourceValidationForm(form_data)
    elif element_name == 'rights':
        element_form = RightsValidationForm(request.POST)
    elif element_name == 'language':
        element_form = LanguageValidationForm(request.POST)
    elif element_name == 'date':
        element_form = ValidDateValidationForm(request.POST)
    elif element_name == 'coverage':
        if 'type' in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            element_form = CoverageTemporalForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        # TODO: need to return form errors
        return {'is_valid': False, 'element_data_dict': None}