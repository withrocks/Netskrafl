# -*- coding: utf-8 -*-
from itertools import izip
import sys
import locale


class CollationSvc:
    """
    Wraps the locale support in the OS and provides fallbacks.

    Locale support depends on the platform. A locale may not be installed
    on the machine or it may be installed with different keys on different
    platforms. This class encapsulates that.

    TODO: Look into using PyICU to provide full platform-independent support
    for all languages.
    """
    def __init__(self, localeid):
        """
        Initializes a new CollationSvc with a locale id on the format
        <language>_<country>[.encoding]

        The locale must exist on the OS except on OS X, which uses a built-in.
        """
        if localeid == "is_IS":
            self._handle_icelandic()
        else:
            self._use_os_locale(localeid)

    def _handle_icelandic(self):
        # Special handling for Icelandic to support
        # OS X and platforms that don't have the locale installed
        if sys.platform == "darwin":
            self._use_builtin_icelandic()
        else:
            if sys.platform.startswith("win32"):
                localeid = "isl"
            self._use_os_locale(localeid)

    def _use_os_locale(self, localeid):
        try:
            print("Collation setting with OS support using localeid='{}'")
            locale.setlocale(locale.LC_COLLATE, localeid)
            self.strcoll = locale.strcoll
        except locale.Error:
            raise LocaleNotAvailableException()

    def _use_builtin_icelandic(self):
        print("Collation setting with built-in support for is_IS")
        icelandic_alphabet = u"AaÁáBbCcDdÐðEeÉéFfGg" \
                             u"HhIiÍíJjKkLlMmNnOoÓóPp" \
                             u"QqRrSsTtUuÚúVvWwXxYyÝýZzÞþÆæÖö"
        self.collation = Collation(icelandic_alphabet)
        self.strcoll = self.collation.strcoll

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
        # TODO: Optimize
        for letter_a, letter_b in izip(a, b):
            delta = self.coll_dict[letter_a] - \
                    self.coll_dict[letter_b]
            if delta != 0:
                return delta

        # The prefix of length min(a, b) is equal, then they must be equal
        # or the longer one comes after the shorter one
        len_a = len(a)
        len_b = len(b)
        if len_a == len_b:
            return 0
        elif len_a > len_b:
            return 1
        else:
            return -1


class LocaleNotAvailableException(Exception):
    pass
