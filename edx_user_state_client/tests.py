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

    def set_many(self, user_idx, block_idx_to_state):
        return self.client.set_many(
            self.user(user_idx),
            {
                self.block(block_idx): state
                for block_idx, state
                in block_idx_to_state.items()
            },
            self.scope,
        )

    def get_many(self, user_idx, block_idxs, fields=None):
        return self.client.get_many(
            self.user(user_idx),
            [self.block(block_idx) for block_idx in block_idxs],
            self.scope,
            fields,
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

    def test_set_overlay(self):
        self.set(0, 0, {'a': 'b'})
        self.set(0, 0, {'b': 'c'})
        self.assertEquals(self.get(0, 0), {'a': 'b', 'b': 'c'})

    def test_get_fields(self):
        self.set(0, 0, {'a': 'b', 'b': 'c'})
        self.assertEquals(self.get(0, 0, ['a']), {'a': 'b'})
        self.assertEquals(self.get(0, 0, ['b']), {'b': 'c'})
        self.assertEquals(self.get(0, 0, ['a', 'b']), {'a': 'b', 'b': 'c'})

    def test_get_missing_block(self):
        self.set(0, 1, {})
        with self.assertRaises(self.client.DoesNotExist):
            self.get(0, 0)

    def test_get_missing_user(self):
        self.set(1, 0, {})
        with self.assertRaises(self.client.DoesNotExist):
            self.get(0, 0)

    def test_get_missing_field(self):
        self.set(0, 0, {'a': 'b'})
        self.assertEquals(self.get(0, 0, ['a', 'b']), {'a': 'b'})

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

    def test_set_many(self):
        self.set_many(0, {0: {'a': 'b'}, 1: {'b': 'c'}})
        self.assertEquals(self.get(0, 0), {'a': 'b'})
        self.assertEquals(self.get(0, 1), {'b': 'c'})

    def test_get_many(self):
        self.set_many(0, {0: {'a': 'b'}, 1: {'b': 'c'}})
        self.assertItemsEqual(
            self.get_many(0, [0, 1]),
            [
                (self.block(0), {'a': 'b'}),
                (self.block(1), {'b': 'c'})
            ]
        )


class DictUserStateClient(XBlockUserStateClient):
    def __init__(self):
        self._data = {}

    def get_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        for key in block_keys:
            if (username, key, scope) not in self._data:
                continue

            if fields is None:
                current_fields = self._data[(username, key, scope)].keys()
            else:
                current_fields = fields

            data = self._data[(username, key, scope)]
            yield (key, {
                field: data[field]
                for field in current_fields
                if field in data
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
