"""This does a comprehensive test of a resource.

It checks iRODS synchronization, logical files, and bag function

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource


class TestHeader(object):
    header = False

    def __init__(self, resource):
        self.resource = resource

    def label(self):
        if not self.header:
            print("resource {}:".format(self.resource.short_id))
            self.header = True


def test_resource(short_id):
    """ Test view for resource depicts output of various integrity checking scripts """

    # print("TEST {}".format(short_id))
    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    resource = res.get_content_model()
    assert resource, (res, res.content_model)

    head = TestHeader(resource)

    if resource.getAVU('bag_modified') is None:
        head.label()
        print("  bag_modified is None")
    if resource.getAVU('isPublic') is None:
        head.label()
        print("  isPublic is None")
    if resource.getAVU('resourceType') is None:
        head.label()
        print("  resourceType is None")
    if resource.getAVU('quotaUserName') is None:
        head.label()
        print("  quotaUserName is None")

    irods_issues, irods_errors = resource.check_irods_files(log_errors=False, return_errors=True)

    if irods_errors:
        head.label()
        print("  iRODS errors:")
        for e in irods_issues:
            print("    {}".format(e))

    logical_header = False

    if resource.resource_type == 'CompositeResource':
        for res_file in resource.files.all():
            if not res_file.has_logical_file:
                head.label()
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

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                test_resource(rid)
        else:
            for r in BaseResource.objects.all():
                test_resource(r.short_id)
