# -*- coding: utf-8 -*-
from itertools import izip
import locale


class CollationSvc:
    """
    A wrapper around collation methods from locale and
    from custom collations
    """
    def __init__(self, localeid):
        self.locale = localeid
        if localeid == "is_IS":
            # Use the more portable builtin:
            icelandic_alphabet = u"AaÁáBbCcDdÐðEeÉéFfGg" \
                        u"HhIiÍíJjKkLlMmNnOoÓóPp" \
                        u"QqRrSsTtUuÚúVvWwXxYyÝýZzÞþÆæÖö"
            self.collation = Collation(icelandic_alphabet)
            self.strcoll = self.collation.strcoll
        else:
            locale.setlocale(locale.LC_COLLATE, localeid)
            self.strcoll = locale.strcoll

    def strcoll(self, a, b):
        """Behaves like locale.strcoll from the core"""
        pass


class Collation:
    """
    Provides a portable collation that doesn't require the locale
    to be available on the machine and avoids a bug on OSX.
    """
    def __init__(self, collation):
        self.coll_dict = {
            letter[1]: letter[0] for letter in enumerate(collation)}

    def strcoll(self, a, b):
        for pair in izip(a, b):
            delta = self.coll_dict[pair[0]] - \
                    self.coll_dict[pair[1]]
            if delta != 0:
                return delta
        return 0

