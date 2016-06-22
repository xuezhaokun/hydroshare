import os
import sqlite3
import tempfile
import shutil
import logging

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField

from django.core.exceptions import ValidationError
from django.db import models

from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement, \
    Coverage, Subject

from django_irods.storage import IrodsStorage


class TimeSeriesAbstractMetaDataElement(AbstractMetaDataElement):
    series_ids = ArrayField(models.CharField(max_length=36, null=True, blank=True), default=[])
    is_dirty = models.BooleanField(default=False)

    @classmethod
    def update(cls, element_id, **kwargs):
        super(TimeSeriesAbstractMetaDataElement, cls).update(element_id, **kwargs)
        element = cls.objects.get(id=element_id)
        element.is_dirty = True
        element.save()

    class Meta:
        abstract = True


# define extended metadata elements for Time Series resource type
class Site(TimeSeriesAbstractMetaDataElement):
    term = 'Site'

    site_code = models.CharField(max_length=200)
    site_name = models.CharField(max_length=255)
    elevation_m = models.IntegerField(null=True, blank=True)
    elevation_datum = models.CharField(max_length=50, null=True, blank=True)
    site_type = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return self.site_name

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Site element of a resource can't be deleted.")


class Variable(TimeSeriesAbstractMetaDataElement):
    term = 'Variable'
    variable_code = models.CharField(max_length=20)
    variable_name = models.CharField(max_length=100)
    variable_type = models.CharField(max_length=100)
    no_data_value = models.IntegerField()
    variable_definition = models.CharField(max_length=255, null=True, blank=True)
    speciation = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.variable_name

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # if the user has entered a new variable name
        if 'variable_name' in kwargs:
            if element.variable_name != kwargs['variable_name']:
                # check if the user has entered a new name
                if kwargs['variable_name'] not in [item.name for item in element.metadata.cv_variable_names.all()]:
                    # generate term for the new name
                    kwargs['variable_name'] = kwargs['variable_name'].strip()
                    term = _generate_term_from_name(kwargs['variable_name'])
                    variable_name = CVVariableName.objects.create(metadata=element.metadata, term=term,
                                                                  name=kwargs['variable_name'])
                    variable_name.is_dirty = True
                    variable_name.save()

        super(Variable, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Variable element of a resource can't be deleted.")


class Method(TimeSeriesAbstractMetaDataElement):
    term = 'Method'
    method_code = models.CharField(max_length=50)
    method_name = models.CharField(max_length=200)
    method_type = models.CharField(max_length=200)
    method_description = models.TextField(null=True, blank=True)
    method_link = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return self.method_name

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Method element of a resource can't be deleted.")


class ProcessingLevel(TimeSeriesAbstractMetaDataElement):
    term = 'ProcessingLevel'
    processing_level_code = models.IntegerField()
    definition = models.CharField(max_length=200, null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.processing_level_code

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ProcessingLevel element of a resource can't be deleted.")


class TimeSeriesResult(TimeSeriesAbstractMetaDataElement):
    term = 'TimeSeriesResult'
    units_type = models.CharField(max_length=255)
    units_name = models.CharField(max_length=255)
    units_abbreviation = models.CharField(max_length=20)
    status = models.CharField(max_length=255)
    sample_medium = models.CharField(max_length=255)
    value_count = models.IntegerField()
    aggregation_statistics = models.CharField(max_length=255)

    def __unicode__(self):
        return self.units_type

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ProcessingLevel element of a resource can't be deleted.")


class AbstractCVLookupTable(models.Model):
    term = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_dirty = models.BooleanField(default=False)

    class Meta:
        abstract = True


class CVVariableType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_variable_types")


class CVVariableName(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_variable_names")


class CVSpeciation(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_speciations")


class CVElevationDatum(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_elevation_datums")


class CVSiteType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_site_types")


class CVMethodType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_method_types")


class CVUnitsType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_units_types")


class CVStatus(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_statuses")


class CVMedium(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_mediums")


class CVAggregationStatistic(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_aggregation_statistics")


# To create a new resource, use these three super-classes.
#


class TimeSeriesResource(BaseResource):
    objects = ResourceManager("TimeSeriesResource")

    class Meta:
        verbose_name = 'Time Series'
        proxy = True

    @property
    def metadata(self):
        md = TimeSeriesMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # final phase of this resource type implementation will support 3 file types
        #return (".csv", ".xml", ".sqlite")
        # phase-1 of implementation supports only sqlite file
        return (".sqlite",)


    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file
        return False


# this would allow us to pick up additional form elements for the template before the template is displayed
processor_for(TimeSeriesResource)(resource_processor)


class TimeSeriesMetaData(CoreMetaData):
    _sites = GenericRelation(Site)
    _variables = GenericRelation(Variable)
    _methods = GenericRelation(Method)
    _processing_levels = GenericRelation(ProcessingLevel)
    _time_series_results = GenericRelation(TimeSeriesResult)

    @property
    def is_dirty(self):
        # this property is used to determine if the SQLite file needs
        # to be synced with metadata in database
        if self.resource.files.first() is None:
            # the SQLite file is missing - so nothing to update
            return False
        dirty = any(site.is_dirty for site in self.sites) or \
                any(variable.is_dirty for variable in self.variables) or \
                any(method.is_dirty for method in self.methods) or \
                any(processing_level.is_dirty for processing_level in self.processing_levels) or \
                any(ts_result.is_dirty for ts_result in self.time_series_results) or \
                any(cv_variable_name.is_dirty for cv_variable_name in CVVariableName.objects.filter(metadata=self)) or \
                any(cv_variable_type.is_dirty for cv_variable_type in CVVariableType.objects.filter(metadata=self)) or \
                any(cv_speciation.is_dirty for cv_speciation in CVSpeciation.objects.filter(metadata=self)) or \
                any(cv_site_type.is_dirty for cv_site_type in CVSiteType.objects.filter(metadata=self))

        return dirty

    @property
    def sites(self):
        return self._sites.all()

    @property
    def variables(self):
        return self._variables.all()

    @property
    def methods(self):
        return self._methods.all()

    @property
    def processing_levels(self):
        return self._processing_levels.all()

    @property
    def time_series_results(self):
        return self._time_series_results.all()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(TimeSeriesMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('Site')
        elements.append('Variable')
        elements.append('Method')
        elements.append('ProcessingLevel')
        elements.append('TimeSeriesResult')
        return elements

    def has_all_required_elements(self):
        if not super(TimeSeriesMetaData, self).has_all_required_elements():
            return False
        if not self.sites:
            return False
        if not self.variables:
            return False
        if not self.methods:
            return False
        if not self.processing_levels:
            return False
        if not self.time_series_results:
            return False

        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(TimeSeriesMetaData, self).get_required_missing_elements()
        if not self.sites:
            missing_required_elements.append('Site')
        if not self.variables:
            missing_required_elements.append('Variable')
        if not self.methods:
            missing_required_elements.append('Method')
        if not self.processing_levels:
            missing_required_elements.append('Processing Level')
        if not self.time_series_results:
            missing_required_elements.append('Time Series Result')
        return missing_required_elements

    def get_xml(self, pretty_print=True):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(TimeSeriesMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        for time_series_result in self.time_series_results:
            # since 2nd level nesting of elements exists here, can't use the helper function
            # add_metadata_element_to_xml()
            hsterms_time_series_result = etree.SubElement(container,
                                                          '{%s}timeSeriesResult' % self.NAMESPACES['hsterms'])
            hsterms_time_series_result_rdf_Description = etree.SubElement(hsterms_time_series_result,
                                                                          '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_result_UUID = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                                   '{%s}timeSeriesResultUUID' % self.NAMESPACES['hsterms'])
            hsterms_result_UUID.text = str(time_series_result.series_ids[0])
            hsterms_units = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                             '{%s}units' % self.NAMESPACES['hsterms'])
            hsterms_units_rdf_Description = etree.SubElement(hsterms_units, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_units_type = etree.SubElement(hsterms_units_rdf_Description,
                                                  '{%s}UnitsType' % self.NAMESPACES['hsterms'])
            hsterms_units_type.text = time_series_result.units_type

            hsterms_units_name = etree.SubElement(hsterms_units_rdf_Description,
                                                  '{%s}UnitsName' % self.NAMESPACES['hsterms'])
            hsterms_units_name.text = time_series_result.units_name

            hsterms_units_abbv = etree.SubElement(hsterms_units_rdf_Description,
                                                  '{%s}UnitsAbbreviation' % self.NAMESPACES['hsterms'])
            hsterms_units_abbv.text = time_series_result.units_abbreviation

            hsterms_status = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                              '{%s}Status' % self.NAMESPACES['hsterms'])
            hsterms_status.text = time_series_result.status

            hsterms_sample_medium = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                                     '{%s}SampleMedium' % self.NAMESPACES['hsterms'])
            hsterms_sample_medium.text = time_series_result.sample_medium

            hsterms_value_count = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                                   '{%s}ValueCount' % self.NAMESPACES['hsterms'])
            hsterms_value_count.text = str(time_series_result.value_count)

            hsterms_statistics = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                                  '{%s}AggregationStatistic' % self.NAMESPACES['hsterms'])
            hsterms_statistics.text = time_series_result.aggregation_statistics

            # generate xml for 'site' element
            site = [site for site in self.sites if time_series_result.series_ids[0] in site.series_ids][0]
            element_fields = [('site_code', 'SiteCode'), ('site_name', 'SiteName')]

            if site.elevation_m:
                element_fields.append(('elevation_m', 'Elevation_m'))

            if site.elevation_datum:
                element_fields.append(('elevation_datum', 'ElevationDatum'))

            if site.site_type:
                element_fields.append(('site_type', 'SiteType'))

            self.add_metadata_element_to_xml(hsterms_time_series_result_rdf_Description, (site, 'site'), element_fields)

            # generate xml for 'variable' element
            variable = [variable for variable in self.variables if time_series_result.series_ids[0] in
                        variable.series_ids][0]
            element_fields = [('variable_code', 'VariableCode'), ('variable_name', 'VariableName'),
                              ('variable_type', 'VariableType'), ('no_data_value', 'NoDataValue')]

            if variable.variable_definition:
                element_fields.append(('variable_definition', 'VariableDefinition'))

            if variable.speciation:
                element_fields.append(('speciation', 'Speciation'))

            self.add_metadata_element_to_xml(hsterms_time_series_result_rdf_Description, (variable, 'variable'), element_fields)

            # generate xml for 'method' element
            method = [method for method in self.methods if time_series_result.series_ids[0] in method.series_ids][0]
            element_fields = [('method_code', 'MethodCode'), ('method_name', 'MethodName'),
                              ('method_type', 'MethodType')]

            if method.method_description:
                element_fields.append(('method_description', 'MethodDescription'))

            if method.method_link:
                element_fields.append(('method_link', 'MethodLink'))

            self.add_metadata_element_to_xml(hsterms_time_series_result_rdf_Description, (method, 'method'), element_fields)

            # generate xml for 'processing_level' element
            processing_level = [processing_level for processing_level in self.processing_levels if
                                time_series_result.series_ids[0] in processing_level.series_ids][0]

            element_fields = [('processing_level_code', 'ProcessingLevelCode')]

            if processing_level.definition:
                element_fields.append(('definition', 'Definition'))

            if processing_level.explanation:
                element_fields.append(('explanation', 'Explanation'))

            self.add_metadata_element_to_xml(hsterms_time_series_result_rdf_Description, (processing_level, 'processingLevel'),
                                             element_fields)

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(TimeSeriesMetaData, self).delete_all_elements()
        self.sites.delete()
        self.variables.delete()
        self.methods.delete()
        self.processing_levels.delete()
        self.time_series_results.delete()

    def update_sqlite_file(self):
        if not self.is_dirty:
            return

        sqlite_file_to_update = self.resource.files.first()
        if sqlite_file_to_update is not None:
            istorage = IrodsStorage()
            log = logging.getLogger()

            # retrieve the sqlite file from iRODS and save it to temp directory
            temp_dir = tempfile.mkdtemp()
            sqlite_file_name = os.path.basename(sqlite_file_to_update.resource_file.name)
            temp_sqlite_file_destination = os.path.join(temp_dir, sqlite_file_name)
            istorage.getFile(sqlite_file_to_update.resource_file.name, temp_sqlite_file_destination)
            try:
                con = sqlite3.connect(temp_sqlite_file_destination)
                with con:
                    # get the records in python dictionary format
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    self._update_variables_table(con, cur)
                    self._update_methods_table(con, cur)
                    self._update_processinglevels_table(con, cur)
                    self._update_sites_related_tables(con, cur)
                    self._update_results_related_tables(con, cur)
                    self._update_CV_tables(con, cur)

                    # push the updated sqlite file to iRODS
                    sqlite_file_original = self.resource.files.first()
                    to_file_name = sqlite_file_original.resource_file.name
                    from_file_name = temp_sqlite_file_destination
                    istorage.saveFile(from_file_name, to_file_name, True)
            except sqlite3.Error, ex:
                sqlite_err_msg = str(ex.args[0])
                log.error("Failed to update SQLite file. Error:" + sqlite_err_msg)
                raise Exception(sqlite_err_msg)
            except Exception, ex:
                log.error("Failed to update SQLite file. Error:" + ex.message)
                raise ex
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

    def _update_CV_tables(self, con, cur):
        # here 'is_dirty' true means a new term has been added
        # so a new record needs to be added to the specific CV table
        def insert_cv_record(cv_elements, cv_table_name):
            for cv_element in cv_elements:
                if cv_element.is_dirty:
                    insert_sql = "INSERT INTO {table_name}(Term, Name) VALUES(?, ?)".format(table_name=cv_table_name)
                    cur.execute(insert_sql, (cv_element.term, cv_element.name))
                    con.commit()
                    cv_element.is_dirty = False
                    cv_element.save()

        insert_cv_record(self.cv_variable_names.all(), 'CV_VariableName')
        insert_cv_record(self.cv_variable_types.all(), 'CV_VariableType')
        insert_cv_record(self.cv_speciations.all(), 'CV_Speciation')
        insert_cv_record(self.cv_site_types.all(), 'CV_SiteType')
        insert_cv_record(self.cv_elevation_datums.all(), 'CV_ElevationDatum')
        insert_cv_record(self.cv_method_types.all(), 'CV_MethodType')
        insert_cv_record(self.cv_units_types.all(), 'CV_UnitsType')
        insert_cv_record(self.cv_statuses.all(), 'CV_Status')
        insert_cv_record(self.cv_mediums.all(), 'CV_Medium')
        insert_cv_record(self.cv_aggregation_statistics.all(), 'CV_AggregationStatistic')

    def _update_variables_table(self, con, cur):
        for variable in self.variables:
            if variable.is_dirty:
                # get the VariableID from Results table to update the corresponding row in Variables table
                series_id = variable.series_ids[0]
                cur.execute("SELECT VariableID FROM Results WHERE ResultUUID=?", (series_id,))
                ts_result = cur.fetchone()
                update_sql = "UPDATE Variables SET VariableCode=?, VariableTypeCV=?, VariableNameCV=?, " \
                             "VariableDefinition=?, SpeciationCV=?, NoDataValue=?  WHERE VariableID=?"

                params = (variable.variable_code, variable.variable_type, variable.variable_name,
                          variable.variable_definition, variable.speciation, variable.no_data_value,
                          ts_result['VariableID'])
                cur.execute(update_sql, params)
                con.commit()
                variable.is_dirty = False
                variable.save()

    def _update_methods_table(self, con, cur):
        # updates the Methods table
        for method in self.methods:
            if method.is_dirty:
                # get the MethodID to update the corresponding row in Methods table
                series_id = method.series_ids[0]
                cur.execute("SELECT FeatureActionID FROM Results WHERE ResultUUID=?", (series_id,))
                result = cur.fetchone()
                cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?", (result["FeatureActionID"],))
                feature_action = cur.fetchone()
                cur.execute("SELECT MethodID from Actions WHERE ActionID=?", (feature_action["ActionID"],))
                action = cur.fetchone()

                update_sql = "UPDATE Methods SET MethodCode=?, MethodName=?, MethodTypeCV=?, " \
                             "MethodDescription=?, MethodLink=?  WHERE MethodID=?"

                params = (method.method_code, method.method_name, method.method_type,
                          method.method_description, method.method_link,
                          action['MethodID'])
                cur.execute(update_sql, params)
                con.commit()
                method.is_dirty = False
                method.save()

    def _update_processinglevels_table(self, con, cur):
        # updates the ProcessingLevels table
        for processing_level in self.processing_levels:
            if processing_level.is_dirty:
                # get the ProcessingLevelID to update the corresponding row in ProcessingLevels table
                series_id = processing_level.series_ids[0]
                cur.execute("SELECT ProcessingLevelID FROM Results WHERE ResultUUID=?", (series_id,))
                result = cur.fetchone()

                update_sql = "UPDATE ProcessingLevels SET ProcessingLevelCode=?, Definition=?, Explanation=? " \
                             "WHERE ProcessingLevelID=?"

                params = (processing_level.processing_level_code, processing_level.definition,
                          processing_level.explanation, result['ProcessingLevelID'])

                cur.execute(update_sql, params)
                con.commit()
                processing_level.is_dirty = False
                processing_level.save()

    def _update_sites_related_tables(self, con, cur):
        # updates 'Sites' and 'SamplingFeatures' tables
        for site in self.sites:
            if site.is_dirty:
                # get the SamplingFeatureID to update the corresponding row in Sites and SamplingFeatures tables
                series_id = site.series_ids[0]
                cur.execute("SELECT FeatureActionID FROM Results WHERE ResultUUID=?", (series_id,))
                result = cur.fetchone()
                cur.execute("SELECT SamplingFeatureID FROM FeatureActions WHERE FeatureActionID=?",
                            (result["FeatureActionID"],))
                feature_action = cur.fetchone()

                # first update the sites table
                update_sql = "UPDATE Sites SET SiteTypeCV=? WHERE SamplingFeatureID=?"
                params = (site.site_type, feature_action["SamplingFeatureID"])
                cur.execute(update_sql, params)

                # then update the SamplingFeatures table
                update_sql = "UPDATE SamplingFeatures SET SamplingFeatureCode=?, SamplingFeatureName=?, Elevation_m=?, " \
                             "ElevationDatumCV=? WHERE SamplingFeatureID=?"

                params = (site.site_code, site.site_name, site.elevation_m,
                          site.elevation_datum, feature_action["SamplingFeatureID"])
                cur.execute(update_sql, params)
                con.commit()
                site.is_dirty = False
                site.save()

    def _update_results_related_tables(self, con, cur):
        # updates 'Results', 'Units' and 'TimeSeriesResults' tables
        for ts_result in self.time_series_results:
            if ts_result.is_dirty:
                # get the UnitsID and ResultID to update the corresponding row in Results, Units and TimeSeriesResults
                # tables
                series_id = ts_result.series_ids[0]
                cur.execute("SELECT UnitsID, ResultID FROM Results WHERE ResultUUID=?", (series_id,))
                result = cur.fetchone()

                # update Units table
                update_sql = "UPDATE Units SET UnitsTypeCV=?, UnitsName=?, UnitsAbbreviation=? WHERE UnitsID=?"
                params = (ts_result.units_type, ts_result.units_name, ts_result.units_abbreviation, result['UnitsID'])
                cur.execute(update_sql, params)

                # update TimeSeriesResults table
                update_sql = "UPDATE TimeSeriesResults SET AggregationStatisticCV=? WHERE ResultID=?"
                params = (ts_result.aggregation_statistics, result['ResultID'])
                cur.execute(update_sql, params)

                # then update the Results table
                update_sql = "UPDATE Results SET StatusCV=?, SampledMediumCV=?, ValueCount=? " \
                             "WHERE ResultID=?"

                params = (ts_result.status, ts_result.sample_medium, ts_result.value_count,
                          result['ResultID'])
                cur.execute(update_sql, params)
                con.commit()
                ts_result.is_dirty = False
                ts_result.save()


def _generate_term_from_name(name):
    name = name.strip()
    # remove any commas
    name = name.replace(',', '')
    # replace - with _
    name = name.replace('-', '_')
    # replace ( and ) with _
    name = name.replace('(', '_')
    name = name.replace(')', '_')

    name_parts = name.split()
    # first word lowercase, subsequent words start with a uppercase
    term = name_parts[0].lower() + ''.join([item.title() for item in name_parts[1:]])
    return term

import receivers
