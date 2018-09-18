# Copyright (C) 2018 AT&T
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


def get_list_from_ranges_str(ranges_str):
    """Convert the range in string format to ranges list

    And yield the merged ranges in order. The argument must be a
    string having comma separated vlan and vlan-ranges.

    get_list_from_ranges_str("4,6,10-13,25-27,100-103")
    [4, 6, 10, 11, 12, 13, 25, 26, 27, 100, 101, 102, 103]
    """
    return sum(((list(range(*[int(range_start) + range_index
                              for range_index, range_start in
                              enumerate(range_item.split('-'))]))
                if '-' in range_item else [int(range_item)])
                for range_item in ranges_str.split(',')), [])


def get_ranges_str_from_list(ranges):
    """Convert the ranges list to string format

    And yield the merged ranges in order in string format.
    The argument must be an iterable of pairs (start, stop).

    get_ranges_str_from_list([4, 11, 12, 13, 25, 26, 27, 101, 102, 103])
    "4,11-13,25-27,101-103"
    """
    ranges_str = []
    for val in sorted(ranges):
        if not ranges_str or ranges_str[-1][-1] + 1 != val:
            ranges_str.append([val])
        else:
            ranges_str[-1].append(val)
    return ",".join([str(range_item[0]) if len(range_item) == 1
                     else str(range_item[0]) + "-" + str(range_item[-1])
                     for range_item in ranges_str])
