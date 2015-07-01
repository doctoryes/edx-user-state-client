from unittest import TestCase
from edx_user_state_client.interface import XBlockUserStateClient
from xblock.fields import Scope
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator

class UserStateClientTestBase(TestCase):

    __test__ = False

    scope = Scope.user_state

    def user(self, user_idx):
        return "user{}".format(user_idx)

    def block(self, block_idx):
        return BlockUsageLocator(
            CourseLocator('org', 'course', 'run'),
            'block_type',
            'block{}'.format(block_idx)
        )

    def field(self, field_idx):
        return "field{}".format(field_idx)

    def get(self, user_idx, block_idx, fields=None):
        if fields is not None:
            fields = [self.field(field_idx) for field_idx in fields]
        return self.client.get(
            self.user(user_idx),
            self.block(block_idx),
            self.scope,
            fields=fields
        )

    def set(self, user_idx, block_idx, state):
        return self.client.set(
            self.user(user_idx),
            self.block(block_idx),
            state,
            self.scope,
        )

    def test_set_get(self):
        self.set(0, 0, {'a': 'b'})
        self.assertEquals(self.get(0, 0), {'a': 'b'})

    def test_set_get_get(self):
        self.set(0, 0, {'a': 'b'})
        self.assertEquals(self.get(0, 0), {'a': 'b'})
        self.assertEquals(self.get(0, 0), {'a': 'b'})

    def test_set_set_get(self):
        self.set(0, 0, {'a': 'b'})
        self.set(0, 0, {'a': 'c'})
        self.assertEquals(self.get(0, 0), {'a': 'c'})

    def test_set_two_users(self):
        self.set(0, 0, {'a': 'b'})
        self.set(1, 0, {'b': 'c'})
        self.assertEquals(self.get(0, 0), {'a': 'b'})
        self.assertEquals(self.get(1, 0), {'b': 'c'})

    def test_set_two_blocks(self):
        self.set(0, 0, {'a': 'b'})
        self.set(0, 1, {'b': 'c'})
        self.assertEquals(self.get(0, 0), {'a': 'b'})
        self.assertEquals(self.get(0, 1), {'b': 'c'})


class DictUserStateClient(XBlockUserStateClient):
    def __init__(self):
        self._data = {}

    def get_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        for key in block_keys:
            if fields is None:
                fields = self._data[(username, key, scope)].keys()

            yield (key, {
                field: self._data[(username, key, scope)][field]
                for field in fields
            })

    def set_many(self, username, block_keys_to_state, scope=Scope.user_state):
        for key, state in block_keys_to_state.items():
            self._data.setdefault((username, key, scope), {}).update(state)

    def delete_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        raise NotImplementedError()

    def get_mod_date_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        raise NotImplementedError()


class TestDictUserStateClient(UserStateClientTestBase):
    __test__ = True

    def setUp(self):
        self.client = DictUserStateClient()
