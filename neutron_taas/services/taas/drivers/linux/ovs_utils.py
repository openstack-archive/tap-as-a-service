# Copyright (C) 2015 Ericsson AB
# Copyright (c) 2015 Gigamon
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


#
# This class implements a simple key-value manager that can support
# the following relationships.
#
# - Multiple values may be affiliated with a key.
# - A value may be affiliated with multiple keys.
# - A value may be affiliated with a key multiple times.
#
class key_value_mgr(object):
    #
    # Initializes internal state for specified # keys
    #
    def __init__(self, nr_keys):
        self.key_list = []
        for i in range(nr_keys):
            self.key_list.append([])

        return

    #
    # Returns specified key-value affilation, if it exists.
    #
    def _find_affiliation(self, key, value):
        aff_list = self.key_list[key]

        for aff in aff_list:
            if aff['value'] == value:
                return aff

        return None

    #
    # Adds an affiliation of 'value' with 'key'
    #
    def affiliate(self, key, value):
        # Locate key-value affiliation
        aff = self._find_affiliation(key, value)
        if aff is None:
            # Create a (new) key-value affiliation
            aff = {
                'value': value,
                'refcnt': 0,
            }
            aff_list = self.key_list[key]
            aff_list.append(aff)

        # Increment affiliation reference count
        aff['refcnt'] += 1

        return

    #
    # Removes an affiliation of 'value' with 'key'
    #
    def unaffiliate(self, key, value):
        # Locate key-value affiliation
        aff = self._find_affiliation(key, value)
        if aff is None:
            return

        # Decrement affiliation reference count
        aff['refcnt'] -= 1

        # Destroy affiliation iff no outstanding references
        if aff['refcnt'] <= 0:
            aff_list = self.key_list[key]
            aff_list.remove(aff)

        return

    #
    # Lists all values affiliated with 'key'
    #
    # Note: The returned list is a set (contains no duplicates)
    #
    def list_affiliations(self, key):
        aff_list = self.key_list[key]

        value_list = []
        for aff in aff_list:
            value_list.append(aff['value'])

        return value_list
