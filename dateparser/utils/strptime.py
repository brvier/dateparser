import sys
import importlib.util
import regex as re
import imp

from datetime import datetime

TIME_MATCHER = re.compile(
    r".*?"
    r"(?P<hour>2[0-3]|[0-1]\d|\d):"
    r"(?P<minute>[0-5]\d|\d):"
    r"(?P<second>6[0-1]|[0-5]\d|\d)"
    r"\.(?P<microsecond>[0-9]{1,6})"
)

MS_SEARCHER = re.compile(r"\.(?P<microsecond>[0-9]{1,6})")


def patch_strptime():
    """Monkey patching _strptime to avoid problems related with non-english
    locale changes on the system.

    For example, if system's locale is set to fr_FR. Parser won't recognize
    any date since all languages are translated to english dates.
    """

    _strptime_spec = importlib.util.find_spec("_strptime")
    if "exec_module" in dir(_strptime_spec.loader):
        _strptime = importlib.util.module_from_spec(_strptime_spec)
        _strptime_spec.loader.exec_module(_strptime)
        sys.modules["strptime_patched"] = _strptime

        _calendar = importlib.util.module_from_spec(_strptime_spec)
        _strptime_spec.loader.exec_module(_calendar)
        sys.modules["calendar_patched"] = _calendar
    else:
        _strptime = imp.load_module("strptime_patched", *imp.find_module("_strptime"))
        _calendar = imp.load_module("calendar_patched", *imp.find_module("_strptime"))
        sys.modules["calendar_patched"] = _calendar
        sys.modules["strptime_patched"] = _strptime

    _strptime._getlang = lambda: ("en_US", "UTF-8")
    _strptime.calendar = _calendar
    _strptime.calendar.day_abbr = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    _strptime.calendar.day_name = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    _strptime.calendar.month_abbr = [
        "",
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    _strptime.calendar.month_name = [
        "",
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]

    return _strptime._strptime_time


__strptime = patch_strptime()


def strptime(date_string, format):
    obj = datetime(*__strptime(date_string, format)[:-3])

    if "%f" in format:
        try:
            match_groups = TIME_MATCHER.match(date_string).groupdict()
            ms = match_groups["microsecond"]
            ms = ms + ((6 - len(ms)) * "0")
            obj = obj.replace(microsecond=int(ms))
        except AttributeError:
            match_groups = MS_SEARCHER.search(date_string).groupdict()
            ms = match_groups["microsecond"]
            ms = ms + ((6 - len(ms)) * "0")
            obj = obj.replace(microsecond=int(ms))

    return obj
