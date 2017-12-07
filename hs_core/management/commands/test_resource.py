"""This does a comprehensive test of a resource.

It checks iRODS synchronization, logical files, and bag function

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from django_irods.icommands import SessionException


class TestResource(object):
    header = False

    def __init__(self, short_id):
        self.short_id = short_id

    def label(self):
        if not self.header:
            print("resource {}:".format(self.resource.short_id))
            self.header = True

    def test_avu(self, label):
        try:
            value = self.resource.getAVU(label)
            if value is None:
                self.label()
                print("  AVU {} is None".format(label))
            return value
        except SessionException:
            self.label()
            print("  AVU {} WAS NOT FOUND.".format(label))
            return None

    def test(self, repair):
        """ Test view for resource depicts output of various integrity checking scripts """

        if repair:
            print("TESTING AND REPAIRING {}", self.short_id)
        else:
            print("TESTING {}".format(self.short_id))

        try:
            res = BaseResource.objects.get(short_id=self.short_id)
        except BaseResource.DoesNotExist:
            print("{} does not exist in Django".format(self.short_id))

        self.resource = res.get_content_model()
        assert self.resource, (res, res.content_model)

        istorage = self.resource.get_irods_storage()

        if not istorage.exists(self.resource.root_path):
            self.label()
            print("  root path {} does not exist in iRODS".format(self.resource.root_path))
            return

        for a in ('bag_modified', 'isPublic', 'resourceType', 'quotaUserName'):
            value = self.test_avu(a)
            if a == 'resourceType' and value is not None and value != self.resource.resource_type:
                self.label()

                print("  resourceType is {}, should be {}{}".format(
                    value,
                    self.resource.resource_type,
                    ' (REPAIRING)' if repair else ''))
                if repair:
                    self.resource.setAVU('resourceType', self.resource.resource_type)

            if a == 'isPublic' and value is not None and value != self.resource.raccess.public:
                self.label()
                print("  isPublic AVU is {}, but public is {}{}".format(
                    value,
                    self.resource.raccess.public,
                    ' (REPAIRING)' if repair else ''))
                if repair:
                    self.resource.setAVU('isPublic', self.resource.raccess.public)

        irods_issues, irods_errors = self.resource.check_irods_files(log_errors=False,
                                                                     return_errors=True)

        if irods_errors:
            self.label()
            print("  iRODS errors:")
            for e in irods_issues:
                print("    {}".format(e))

        logical_header = False

        if self.resource.resource_type == 'CompositeResource':
            for res_file in self.resource.files.all():
                if not res_file.has_logical_file:
                    self.label()
                    if not logical_header:
                        print("  logical file errors:")
                    print("    {} logical file NOT SPECIFIED".format(res_file.short_path))


class Command(BaseCommand):
    help = "Print results of testing resource integrity."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',           # value is options['log']
            help='log errors to system log',
        )

        # Named (optional) arguments
        parser.add_argument(
            '--repair',
            action='store_true',  # True for presence, False for absence
            dest='repair',           # value is options['log']
            help='repair problems if possible',
        )

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                TestResource(rid).test()
        else:
            for r in BaseResource.objects.all():
                TestResource(r.short_id).test(options['repair'])
