from mezzanine.pages.page_processors import processor_for

from crispy_forms.layout import Layout, HTML

from forms import SiteForm, VariableForm, MethodForm, ProcessingLevelForm, TimeSeriesResultForm, \
    UpdateSQLiteLayout, SeriesSelectionLayout, TimeSeriesMetaDataLayout
from hs_core import page_processors
from hs_core.views import add_generic_context
from hs_core.hydroshare import utils
from hs_app_timeseries.models import TimeSeriesResource


@processor_for(TimeSeriesResource)
def landing_page(request, page):
    """
        A typical Mezzanine page processor.

    """
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    extended_metadata_exists = False
    if content_model.metadata.sites or \
            content_model.metadata.variables or \
            content_model.metadata.methods or \
            content_model.metadata.processing_levels or \
            content_model.metadata.time_series_results:
        extended_metadata_exists = True

    series_ids = {}
    if not content_model.metadata.time_series_results:
        res_file = content_model.files.all().first()
        if res_file:
            # check if the file is a csv file
            file_ext = utils.get_resource_file_name_and_extension(res_file)[1]
            if file_ext == ".csv":
                for index, series_name in enumerate(sorted(content_model.metadata.series_names)):
                    series_ids[str(index)] = series_name
    else:
        for result in content_model.metadata.time_series_results:
            series_id = result.series_ids[0]
            series_ids[series_id] = _get_series_label(series_id, content_model)

    if 'series_id' in request.GET:
        selected_series_id = request.GET['series_id']
        if 'series_id' in request.session:
            if selected_series_id != request.session['series_id']:
                is_resource_specific_tab_active = True
                request.session['series_id'] = selected_series_id
            else:
                is_resource_specific_tab_active = False
        else:
            request.session['series_id'] = selected_series_id
            is_resource_specific_tab_active = False
    else:
        selected_series_id = series_ids.keys()[0] if series_ids.keys() else None
        request.session['series_id'] = selected_series_id
        is_resource_specific_tab_active = False

    # view depends on whether the resource is being edited
    if not edit_resource:
        # resource in VIEW Mode
        context = _get_resource_view_context(page, request, content_model, selected_series_id,
                                             series_ids, extended_metadata_exists)
    else:
        # resource in EDIT Mode
        context = _get_resource_edit_context(page, request, content_model, selected_series_id,
                                             series_ids, extended_metadata_exists)

    context['is_resource_specific_tab_active'] = is_resource_specific_tab_active

    # TODO: can we refactor to make it impossible to skip adding the generic context
    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context


def _get_resource_view_context(page, request, content_model, selected_series_id, series_ids,
                               extended_metadata_exists):
    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user, resource_edit=False,
                                               extended_metadata_layout=None, request=request)

    context['extended_metadata_exists'] = extended_metadata_exists
    context['selected_series_id'] = selected_series_id
    context['series_ids'] = series_ids
    context['sites'] = [site for site in content_model.metadata.sites if selected_series_id in
                        site.series_ids]
    context['variables'] = [variable for variable in content_model.metadata.variables if
                            selected_series_id in variable.series_ids]
    context['methods'] = [method for method in content_model.metadata.methods if
                          selected_series_id in method.series_ids]
    context['processing_levels'] = [pro_level for pro_level in
                                    content_model.metadata.processing_levels if
                                    selected_series_id in pro_level.series_ids]
    context['timeseries_results'] = [ts_result for ts_result in
                                     content_model.metadata.time_series_results if
                                     selected_series_id in ts_result.series_ids]

    return context


def _get_resource_edit_context(page, request, content_model, selected_series_id, series_ids,
                               extended_metadata_exists):
    processing_level_form = None
    method_form = None
    timeseries_result_form = None

    # create timeseries specific metadata element forms

    # create form for the "Site" element
    if content_model.metadata.sites:
        site = content_model.metadata.sites.filter(
            series_ids__contains=[selected_series_id]).first()
        site_form = SiteForm(instance=site, res_short_id=content_model.short_id,
                             element_id=site.id if site else None,
                             cv_site_types=content_model.metadata.cv_site_types.all(),
                             cv_elevation_datums=content_model.metadata.cv_elevation_datums.all(),
                             show_site_code_selection=not content_model.has_sqlite_file,
                             available_sites=content_model.metadata.sites,
                             selected_series_id=selected_series_id)

        if site is not None:
            site_form.action = _get_element_update_form_action('site', content_model.short_id,
                                                               site.id)
            site_form.number = site.id

            site_form.set_dropdown_widgets(site_form.initial['site_type'],
                                           site_form.initial['elevation_datum'])
        else:
            # this case can only happen in case of csv upload
            site_form.set_dropdown_widgets(content_model.metadata.cv_site_types.all().first().name,
                                           content_model.metadata.cv_elevation_datums.all().
                                           first().name)

    else:
        # this case can happen only in case of CSV upload
        site_form = SiteForm(instance=None, res_short_id=content_model.short_id,
                             element_id=None,
                             cv_site_types=content_model.metadata.cv_site_types.all(),
                             cv_elevation_datums=content_model.metadata.cv_elevation_datums.all(),
                             selected_series_id=selected_series_id)

        site_form.set_dropdown_widgets(content_model.metadata.cv_site_types.all().first().name,
                                       content_model.metadata.cv_elevation_datums.all().first().name)

    # create form for the "Variable" element
    if content_model.metadata.variables:
        variable = content_model.metadata.variables.filter(
            series_ids__contains=[selected_series_id]).first()
        variable_form = VariableForm(
            instance=variable, res_short_id=content_model.short_id,
            element_id=variable.id if variable else None,
            cv_variable_types=content_model.metadata.cv_variable_types.all(),
            cv_variable_names=content_model.metadata.cv_variable_names.all(),
            cv_speciations=content_model.metadata.cv_speciations.all(),
            show_multiple_variable_chkbox=False, selected_series_id=selected_series_id)
        if variable is not None:
            variable_form.action = _get_element_update_form_action('variable',
                                                                   content_model.short_id,
                                                                   variable.id)
            variable_form.number = variable.id
            variable_form.set_dropdown_widgets(variable_form.initial['variable_type'],
                                               variable_form.initial['variable_name'],
                                               variable_form.initial['speciation'])
        else:
            variable_form.set_dropdown_widgets(
                variable_type=content_model.metadata.cv_variable_types.all().first().name,
                variable_name=content_model.metadata.cv_variable_names.all().first().name,
                speciation=content_model.metadata.cv_speciations.all().first().name)
    else:
        variable_form = VariableForm(
            instance=None, res_short_id=content_model.short_id,
            element_id=None,
            cv_variable_types=content_model.metadata.cv_variable_types.all(),
            cv_variable_names=content_model.metadata.cv_variable_names.all(),
            cv_speciations=content_model.metadata.cv_speciations.all(),
            show_multiple_variable_chkbox=True, selected_series_id=min(series_ids.keys()))

        variable_form.set_dropdown_widgets(
            variable_type=content_model.metadata.cv_variable_types.all().first().name,
            variable_name=content_model.metadata.cv_variable_names.all().first().name,
            speciation=content_model.metadata.cv_speciations.all().first().name)

    # TODO: The forms for the following elements need to be created based on the 2 elements above.
    method = content_model.metadata.methods.filter(
        series_ids__contains=[selected_series_id]).first()
    if method is not None:
        method_form = MethodForm(instance=method, res_short_id=content_model.short_id,
                                 element_id=method.id if method else None,
                                 cv_method_types=content_model.metadata.cv_method_types.all())

        method_form.action = _get_element_update_form_action('method',
                                                             content_model.short_id, method.id)
        method_form.number = method.id
        method_form.set_dropdown_widgets(method_form.initial['method_type'])

    processing_level = content_model.metadata.processing_levels.filter(
        series_ids__contains=[selected_series_id]).first()
    if processing_level is not None:
        processing_level_form = ProcessingLevelForm(instance=processing_level,
                                                    res_short_id=content_model.short_id,
                                                    element_id=processing_level.id if
                                                    processing_level else None)

        processing_level_form.action = _get_element_update_form_action('pocessinglevel',
                                                                       content_model.short_id,
                                                                       site.id)
        processing_level.number = processing_level.id

    time_series_result = content_model.metadata.time_series_results.filter(
        series_ids__contains=[selected_series_id]).first()
    if time_series_result is not None:
        timeseries_result_form = TimeSeriesResultForm(
            instance=time_series_result,
            res_short_id=content_model.short_id,
            element_id=time_series_result.id if time_series_result else None,
            cv_sample_mediums=content_model.metadata.cv_mediums.all(),
            cv_units_types=content_model.metadata.cv_units_types.all(),
            cv_aggregation_statistics=content_model.metadata.cv_aggregation_statistics.all(),
            cv_statuses=content_model.metadata.cv_statuses.all())

        timeseries_result_form.action = _get_element_update_form_action('timeseriesresult',
                                                                        content_model.short_id,
                                                                        time_series_result.id)
        timeseries_result_form.number = time_series_result.id
        timeseries_result_form.set_dropdown_widgets(timeseries_result_form.initial['sample_medium'],
                                                    timeseries_result_form.initial['units_type'],
                                                    timeseries_result_form.initial[
                                                        'aggregation_statistics'],
                                                    timeseries_result_form.initial['status'])

    ext_md_layout = Layout(UpdateSQLiteLayout,
                           SeriesSelectionLayout,
                           TimeSeriesMetaDataLayout)

    if content_model.files.all().count() == 0:
        ext_md_layout = Layout(HTML("""<div class="alert alert-warning"><strong>No resource
        specific metadata is available. Add an ODM2 SQLite file or CSV file to see
        metadata.</strong></div>"""))

    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user, resource_edit=True,
                                               extended_metadata_layout=ext_md_layout,
                                               request=request)

    # customize base context
    context['extended_metadata_exists'] = extended_metadata_exists
    context['resource_type'] = 'Time Series Resource'
    context['selected_series_id'] = selected_series_id
    context['series_ids'] = series_ids
    context['site_form'] = site_form
    context['variable_form'] = variable_form
    context['method_form'] = method_form
    context['processing_level_form'] = processing_level_form
    context['timeseries_result_form'] = timeseries_result_form
    return context


def _get_series_label(series_id, resource):
    label = "{site_code}:{site_name}, {variable_code}:{variable_name}, {units_name}, " \
            "{pro_level_code}, {method_name}"
    site = [site for site in resource.metadata.sites if series_id in site.series_ids][0]
    variable = [variable for variable in resource.metadata.variables if
                series_id in variable.series_ids][0]
    method = [method for method in resource.metadata.methods if series_id in method.series_ids][0]
    pro_level = [pro_level for pro_level in resource.metadata.processing_levels if
                 series_id in pro_level.series_ids][0]
    ts_result = [ts_result for ts_result in resource.metadata.time_series_results if
                 series_id in ts_result.series_ids][0]
    label = label.format(site_code=site.site_code, site_name=site.site_name,
                         variable_code=variable.variable_code,
                         variable_name=variable.variable_name, units_name=ts_result.units_name,
                         pro_level_code=pro_level.processing_level_code,
                         method_name=method.method_name)
    return label


def _get_element_update_form_action(element_name, resource_id, element_id):
    action = "/hsapi/_internal/{}/{}/{}/update-metadata/"
    return action.format(resource_id, element_name, element_id)
