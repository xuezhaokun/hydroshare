import os
from pprint import pprint 

from datetime import datetime, timedelta

from django.db import models
from django.core.exceptions import PermissionDenied, ValidationError
from mezzanine.conf import settings

from hs_core.signals import pre_check_bag_flag


class ResourceIRODSMixin(models.Model):
    """ This contains iRODS methods to be included as options for resources """
    class Meta:
        abstract = True

    def __home_path(self): 
        """ Return the home path for local iRODS resources """
        return settings.IRODS_CWD

    def update_bag(self):
        """
        Update a bag before issuing a download ticket
        """
        from hs_core.tasks import create_bag_by_irods
        from hs_core.hydroshare.resource import check_resource_type
        from hs_core.hydroshare.hs_bagit import create_bag_files

        # send signal for pre_check_bag_flag
        resource_cls = check_resource_type(self.resource_type)
        # pre_check_bag_flag.send(sender=resource_cls, resource=self)

        metadata_dirty = self.getAVU('metadata_dirty')
        bag_modified = self.getAVU('bag_modified')

        print('metadata_dirty = {} ({})'.format(str(metadata_dirty), type(metadata_dirty)))
        print('bag_modified = {} ({})'.format(str(bag_modified), type(bag_modified)))
        if metadata_dirty:  # automatically cast to Bool
            print("update_bag: creating bag files")
            create_bag_files(self)
            self.setAVU('metadata_dirty', False)

        # if bag_modified:  # automatically cast to Bool
        print("create bag")
        create_bag_by_irods(self.short_id)
        # self.setAVU('bag_modified', False)

    def update_metadata_files(self):
        from hs_core.hydroshare.hs_bagit import create_bag_files
        metadata_dirty = self.getAVU('metadata_dirty')
        print('{} metadata_dirty = {}'.format(self.short_id, str(metadata_dirty)))
        if metadata_dirty:
            print("update metadata files {}: calling create_bag_files".format(self.short_id)) 
            create_bag_files(self)
            self.setAVU('metadata_dirty', False)
        metadata_dirty = self.getAVU('metadata_dirty')
        print('metadata_dirty = {}'.format(str(metadata_dirty)))

    def create_ticket(self, user, path=None, write=False, allowed_uses=1):
        """
        create an iRODS ticket for reading or modifying a resource

        :param user: user to authorize
        :param path: path in iRODS to the object being requested.
        :return:

        :raises PermissionDenied: if user is not allowed to create the ticket.
        :raises SessionException: if ticket fails to be created for some reason.
        :raises SuspiciousFileOperation: if path uses .. illegally

        WARNING: This creates a ticket that expires in one hour in UTC. If the
        iRODS and django servers are in different time zones and not set for UTC,
        this results in a useless ticket. This includes federated servers.

        THERE IS NO STRAIGHTFORWARD MECHANISM IN IRODS for determining the time zone
        or local time of an iRODS server.

        """
        from hs_core.models import path_is_allowed
        from hs_core.tasks import create_bag_by_irods
        from hs_core.hydroshare.resource import check_resource_type
        from hs_core.hydroshare.hs_bagit import create_bag_files

        # raises SuspiciousFileOperation if path is not allowed
        path_is_allowed(path)

        # authorize user
        if write:
            if not user.uaccess.can_change_resource(self):
                raise PermissionDenied("user {} cannot change resource {}"
                                       .format(user.username, self.short_id))
        else:
            if not user.uaccess.can_view_resource(self):
                raise PermissionDenied("user {} cannot view resource {}"
                                       .format(user.username, self.short_id))
        if path is None:
            path = self.file_path  # default = all data files

        print("create ticket: creating bag files")
        create_bag_files(self)
        print("create ticket: create_bag_by_irods")
        create_bag_by_irods(self.short_id)

        # can only write resource files
        if write:
            if not path.startswith(self.file_path):
                raise PermissionDenied("{} can only write data files to {}"
                                       .format(user.username, self.short_id))
        # can read anything inside this particular resource
        else:
            if path != self.bag_path and not path.startswith(self.root_path):
                raise PermissionDenied("invalid resource file path {}".format(path))
            if path == self.bag_path:
                print("found a bag request for {}, updating bag".format(path))
                self.update_bag()
                istorage = self.get_irods_storage()
                stuff = istorage.listdir('bags') 
                print("contents of bags:")
                pprint(stuff) 
            elif path == self.resmap_path or path == self.scimeta_path:
                print("found a metadata request for {}, updating metadata files".format(path))
                self.update_metadata_files()
                istorage = self.get_irods_storage()
                stuff = istorage.listdir(os.path.join(self.root_path, 'data')) 
                pprint(stuff) 

        istorage = self.get_irods_storage()
        read_or_write = 'write' if write else 'read'
        if path.startswith(self.short_id) or path.startswith('bags/'):  # local path
            path = os.path.join(self.__home_path(), path)
        print("in create_ticket, path={} for {}".format(path, read_or_write))
        print("iticket command is 'iticket create {} {}'".format(read_or_write, path))
        stdout, stderr = istorage.session.run("iticket", None, 'create', read_or_write, path)
        if not stdout.startswith('ticket:'):
            raise ValidationError("ticket creation failed: {}", stderr)
        ticket = stdout.split('\n')[0]
        ticket = ticket[len('ticket:'):]
        _, _ = istorage.session.run('iticket', None, 'mod', ticket,
                                    'uses', str(allowed_uses))

        # This creates a timestamp with a one-hour timeout.
        # Note that this is a timeout on when the ticket is first used, and 
        # not on the completion of the use, which can take considerably longer. 
        # TODO: this will fail unless Django and iRODS are both running in UTC.
        # There is no current mechanism for determining the timezone of a remote iRODS 
        # server from within iRODS; shell access is required.
        timeout = datetime.now() + timedelta(hours=1)
        formatted = timeout.strftime("%Y-%m-%d.%H:%M")
        _, _ = istorage.session.run('iticket', None, 'mod', ticket,
                                    'expires', formatted)
        return ticket

    def list_ticket(self, ticket):
        """ List a ticket's attributes """
        istorage = self.get_irods_storage()
        stdout, stderr = istorage.session.run("iticket", None, 'ls', ticket)
        if stdout.startswith('id:'):
            stuff = stdout.split('\n')
            output = {}
            for s in stuff:
                try:
                    line = s.split(': ')
                    key = line[0]
                    value = line[1]
                    if key == 'collection name' or key == 'data collection':
                        output['full_path'] = value
                        if self.resource_federation_path:
                            if __debug__:
                                assert(value.startswith(self.resource_federation_path))
                            output['long_path'] = value[len(self.resource_federation_path):]
                            output['fed_path'] = self.resource_federation_path
                        else:
                            location = value.search(self.short_id)
                            if __debug__:
                                assert(location >= 0)
                            output['long_path'] = value[location:]
                            output['home_path'] = value[:(location-1)]
                        if __debug__:
                            assert(output['long_path'].startswith(self.short_id))
                        # data/....
                        qual_path = output['long_path'][len(self.short_id)+1:]
                        output['qual_path'] = qual_path
                        output['folder'] = None
                        if qual_path.startswith('data/contents/'):
                            output['folder'] = qual_path[len('data/contents/'):]

                    if key == 'data-object name':
                        output['filename'] = value
                    elif key == 'ticket type':
                        output['type'] = value
                    elif key == 'owner name':
                        output['owner'] = value
                    elif key == 'owner zone':
                        output['zone'] = value
                    elif key == 'expire time':
                        output['expires'] = value
                    else:
                        output[line[0]] = line[1]
                except Exception:  # no ':' in line
                    pass
            if 'filename' in output: 
                output['full_path'] = os.path.join(output['full_path'], output['filename'])

            return output
        else:
            raise ValidationError("ticket {} cannot be listed".format(ticket))

    def delete_ticket(self, user, ticket):
        """
        delete an existing ticket

        :param ticket: ticket string

        :raises SessionException: if ticket does not exist.

        This checks that the user at least has the privilege the ticket grants,
        before deleting it. This is not quite as comprehensive as keeping a
        ticket history, but provides a small amount of safety nonetheless.

        It remains possible for one user to delete the ticket of another user without
        that user's knowledge, provided that the users have the same privilege.
        However, tickets are not broadcast, so this is unlikely to happen.

        The usual mechanism -- of checking that the user owns the ticket -- is not
        practical, because the ticket owner is always the proxy user.
        """
        meta = self.list_ticket(ticket)

        if self.root_path not in meta['full_path']:
            raise PermissionDenied("user {} cannot delete ticket for a different resource"
                                   .format(user.username))
        # get kind of ticket
        write = meta['type'] == 'write'

        # authorize user
        if write:
            if not user.uaccess.can_change_resource(self):
                raise PermissionDenied("user {} cannot delete change ticket for {}"
                                       .format(user.username, self.short_id))
        else:
            if not user.uaccess.can_view_resource(self):
                raise PermissionDenied("user {} cannot delete view ticket for {}"
                                       .format(user.username, self.short_id))
        istorage = self.get_irods_storage()
        _, _ = istorage.session.run('iticket', None, 'delete', ticket)


class ResourceFileIRODSMixin(models.Model):
    """ This contains iRODS functions related to resource files """
    class Meta:
        abstract = True

    def create_ticket(self, user, write=False):
        """ This creates a ticket to read or modify this file """
        return self.resource.create_ticket(user, path=self.storage_path, write=write)
