from decimal import Decimal
from django.conf import settings
from django.template.defaultfilters import slugify
import math
from django.utils.datastructures import SortedDict
import logging
import re
from limbo.templatetags.formatting import number

logger = logging.getLogger(__file__)

def pretty_dict(d, title):
    """
    Provides a way for views or event handlers to get clean and predictable
    dicts.  It also provides a central place to log the clean dicts to aid in
    debugging.
    """
    # TODO - Yes, this is orig.  If you have time, clean it up. I do not have
    # time tonight.
    if settings.LOG_PRETTY_DICT:
        key_width = 35
        val_width = 55
        width = key_width + val_width + 6
        pretty= ''
        bar = '-' * width
        title = "   " + title + "   "
        centered = title.center(width, '|')
        cap = '\n'.join((bar, centered, bar))
        ordered = {}
        for k in sorted(d):
             pretty += '|%+35s -> %-55s|\n' % \
                     (str(k), str(d[k])[:45])
        logger.debug('\n' + cap + '\n' + pretty + cap + '\n')



def clean_dict(d):
    def clean_key(k):
        k = k.lower().replace('-', '_')
        if k.startswith('variable_'):
            k = k[len('variable_'):]
        return k
    return dict((clean_key(k), v) for k,v in d.iteritems())


def camelcase(text):
    cc = ''
    for each in text.replace(' ', '_').replace('-', '_').split('_'):
        cc += each.capitalize()
    return cc


def _line(char):
    print(char * 80)


def parse_channel_vars(varstring):
    var_dict = {}
    lines = varstring.split('\n')
    for line in lines:
        data = line.split('=')
        if len(data) == 2:
            var_dict[str(data[0]).strip()] = str(data[1].strip())
    return var_dict

def chan_vars_to_string(var_dict):
    kv_pairs = []
    for k, v in var_dict.iteritems():
        kv_pairs.append("%s='%s'" % (k,v))
    return '{%s}' % ','.join(kv_pairs)

BYTE_REGEX = re.compile('([\d]+)b', re.I)
KB_REGEX = re.compile('([\d]+)kb', re.I)
MB_REGEX = re.compile('([\d]+)mb', re.I)
GB_REGEX = re.compile('([\d]+)gb', re.I)
TB_REGEX = re.compile('([\d]+)tb', re.I)

SIZE_DICT = SortedDict((
    (BYTE_REGEX, 0),
    (KB_REGEX, 3),
    (MB_REGEX, 6),
    (GB_REGEX, 9),
    (TB_REGEX, 12),
))

LABEL_DICT = SortedDict((
    (0, 'B'),
    (3, 'kB'),
    (6, 'MB'),
    (9, 'GB'),
    (12, 'TB'),
))

def str_size_to_bytes(s):
    s = slugify(s).replace('-', '').replace('_', '')
    for regex, power in SIZE_DICT.items():
        if regex.match(s):
            return int(regex.match(s).groups()[0])*math.pow(10, power)
    try:
        return int(s)
    except TypeError:
        pass

def formatted_bytes(i):
    i = int(i)
    powers = SIZE_DICT.values()
    powers.reverse()
    for power in powers:
        if (i / int(math.pow(10, power))):
            value = number(Decimal(i)/Decimal(str(math.pow(10, power))))
            return '%s %s' %(value, LABEL_DICT[power])