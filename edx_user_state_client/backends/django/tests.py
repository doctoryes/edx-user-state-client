"""
Black-box tests of the DjangoUserStateClient against the semantics
defined in edx_user_state_client.
"""

from django.conf import settings
settings.configure()

from collections import defaultdict
from datetime import datetime
from unittest import skip
from pytz import UTC

from django.contrib.auth.models import User
from django.test import TestCase

import factory

from edx_user_state_client.tests import UserStateClientTestBase
from edx_user_state_client.backends.django.client import DjangoXBlockUserStateClient
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    FACTORY_FOR = User
    FACTORY_DJANGO_GET_OR_CREATE = ('email', 'username')

    username = factory.Sequence(u'user{}'.format)
    email = factory.Sequence(u'test+user+{}@example.com'.format)
    password = factory.PostGenerationMethodCall('set_password', 'test')
    first_name = factory.Sequence(u'First {}'.format)
    last_name = factory.Sequence(u'Test {}'.format)
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime(2012, 1, 1, tzinfo=UTC)
    date_joined = datetime(2011, 1, 1, tzinfo=UTC)


class TestDjangoUserStateClient(UserStateClientTestBase, TestCase):
    """
    Tests of the DjangoUserStateClient backend.
    """
    __test__ = True

    def _user(self, user_idx):
        return self.users[user_idx].username

    def _block_type(self, block):  # pylint: disable=unused-argument
        # We only record block state history in DjangoUserStateClient
        # when the block type is 'problem'
        return 'problem'

    def setUp(self):
        super(TestDjangoUserStateClient, self).setUp()
        self.client = DjangoXBlockUserStateClient()
        self.users = defaultdict(UserFactory.create)

    # We're skipping these tests because the iter_all_by_block and iter_all_by_course
    # are not implemented in the DjangoXBlockUserStateClient
    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_blocks_deleted_block(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_blocks_empty(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_blocks_many_users(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_blocks_single_user(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_course_deleted_block(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_course_empty(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_course_single_user(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_course_many_users(self):
        pass
