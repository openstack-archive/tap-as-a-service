#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.utils.encoding import force_text

from horizon import exceptions
from horizon.test import helpers as test


class HandleTests(test.TestCase):
    def test_handle_translated(self):
        translated_unicode = u'\u30b3\u30f3\u30c6\u30ca\u30fc\u304c' \
                             u'\u7a7a\u3067\u306f\u306a\u3044\u305f' \
                             u'\u3081\u3001\u524a\u9664\u3067\u304d' \
                             u'\u307e\u305b\u3093\u3002'
        # Japanese translation of:
        # 'Because the container is not empty, it can not be deleted.'

        expected = ['error', force_text(translated_unicode), '']

        req = self.request
        req.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        try:
            raise exceptions.Conflict(translated_unicode)
        except exceptions.Conflict:
            exceptions.handle(req)

        # The real test here is to make sure the handle method doesn't throw a
        # UnicodeEncodeError, but making sure the message is correct could be
        # useful as well.
        self.assertItemsEqual(req.horizon['async_messages'], [expected])
