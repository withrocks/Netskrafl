# -*- coding: utf-8 -*-
# There seems to be an issue with the locale settings on OSX
# In general, using the locale support in Python is difficult
# since it depends on support from the OS and the particular
# packages installed.
# But it seems that the support for Icelandic on OSX is simply not correct
# when it comes to collation.
# Locale support on Unix like machines can be queried with `locale -a`

from __future__ import print_function
import sys
import locale
from itertools import izip

print("Running test on '{}'".format(sys.platform))


def validate_sort_order(for_locale, test_set, cmp=locale.strcoll):
    # Send in a sequence in the expected order
    if for_locale:
        locale.setlocale(locale.LC_COLLATE, for_locale)
    valid = test_set == sorted(test_set, cmp=cmp)
    return valid


class IcelandicColl:
    """
    Defines an Icelandic collation that doesn't require the locale
    to be available on the machine and avoids a bug on OSX.
    """
    def __init__(self):
        icelandic_coll = u"AaÁáBbCcDdÐðEeÉéFfGg"\
                         u"HhIiÍíJjKkLlMmNnOoÓóPp"\
                         u"QqRrSsTtUuÚúVvWwXxYyÝýZzÞþÆæÖö"
        self.icelandic_coll_dict = {
            letter[1]: letter[0] for letter in enumerate(icelandic_coll)}

    def compare(self, a, b):
        for pair in izip(a, b):
            delta = self.icelandic_coll_dict[pair[0]] - \
                    self.icelandic_coll_dict[pair[1]]
            if delta != 0:
                return delta

# All of these are in the correct expected order:
test_sets = [[u"a", u"á"],
             [u"d", u"ð"],
             [u"abbadísunum", u"abbaðist"],
             [u"abbaðist", u"abbast"]]

current_locale = "is_IS.UTF-8"
status = [validate_sort_order(current_locale, test_set) for test_set in test_sets]
print("locale", "accepted", "status")
print(current_locale, all(status), status)

icelandic_coll = IcelandicColl()
status = [validate_sort_order(None, test_set, icelandic_coll.compare) for test_set in test_sets]
print("locale", "accepted", "status")
print(IcelandicColl, all(status), status)

