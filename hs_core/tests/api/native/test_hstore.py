from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core.hydroshare import resource
from hs_core.hydroshare import users
from hs_core.models import GenericResource, GenericMetaDataElement
from hs_core.testing import MockIRODSTestCaseMixin


class TestHStore(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestHStore, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[])

        self.res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

    def test_hstore_metadata(self):
        self.assertNotEquals(self.res.metadata_new, None)
        self.assertEquals(self.res.metadata_new.elements.all().count(), 0)
        generic_element = GenericMetaDataElement()
        generic_element.data = {'name': 'John Jackson'}
        generic_element.metadata= self.res.metadata_new
        generic_element.save()
        self.assertEquals(self.res.metadata_new.elements.all().count(), 1)
        element = self.res.metadata_new.elements.all().first()
        self.assertEquals(element.data['name'], 'John Jackson')

        generic_element_2 = GenericMetaDataElement()
        generic_element_2.data = {'name': 'Mellisa Kelly', "email": 'jk@gmail.com'}
        generic_element_2.metadata= self.res.metadata_new
        generic_element_2.save()

        self.assertEquals(self.res.metadata_new.elements.all().count(), 2)
        self.assertNotEquals(self.res.metadata_new.elements.filter(data__contains={'name': 'John Jackson'}), None)
        self.assertNotEquals(self.res.metadata_new.elements.filter(data__contains={'name': 'Mellisa Kelly', "email": 'jk@gmail.com'}), None)

        # delete all metadata elements
        self.res.metadata_new.elements.all().delete()

        # create a generic metadata element using the 'Generic' class
        data = {'color': 'red'}
        # generic = Generic()
        # generic.data = data
        # generic.metadata = self.res.metadata_new
        # generic.save()
        self.res.metadata_new.create_element('Generic', **data)
        self.assertEquals(self.res.metadata_new.generics.all().count(), 1)
        data = {'color': 'blue', 'size': '7.5'}
        self.res.metadata_new.create_element('Generic', **data)
        self.assertEquals(self.res.metadata_new.generics.all().count(), 2)

        self.assertEquals(self.res.metadata_new.generics.filter(data__color='red').count(), 1)
        self.assertEquals(self.res.metadata_new.generics.filter(data__size='7.5').count(), 1)
        # the should be 2 generic element that has key=color
        self.assertEquals(self.res.metadata_new.generics.filter(data__has_key='color').count(), 2)

        # delete all metadata elements
        #self.res.metadata_new.elements.all().delete()

        # create Author element that has the form validation for the allowed data
        data = {'name': 'Javed Akthor', 'email': 'ja@gmail.com', 'phone': '567-890-6789'}
        self.res.metadata_new.create_element('Author', **data)
        self.assertEquals(self.res.metadata_new.authors.all().count(), 1)

        # required email data is missing, should raise exception
        data = {'name': 'Lisa Holland', 'phone': '567-890-6789'}
        with self.assertRaises(Exception):
            self.res.metadata_new.create_element('Author', **data)

        self.assertEquals(self.res.metadata_new.authors.all().count(), 1)

        data = {'name': 'Lisa Holland', 'email': 'lh@gmail.com', 'phone': '123-456-0979'}
        self.res.metadata_new.create_element('Author', **data)
        self.assertEquals(self.res.metadata_new.authors.all().count(), 2)









