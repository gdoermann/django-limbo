from cStringIO import StringIO
from decimal import Decimal
import pprint
from django.utils.datastructures import SortedDict
import urllib
from xml.etree import ElementTree as ET

class XMLStatsBaseHandler:
    DEFAULT_PARSER=None
    def __init__(self, parser = None):
        self.parser = parser or self.DEFAULT_PARSER
        self.value = self.initial_value()

    def initial_value(self):
        """ Designed to be overridden. """
        return None

    def handle(self, value):
        """ Designed to be overridden. Handles each value as it is passed in.  Null values are passed in when
         xml path is not found."""
        pass

    def parse(self, value):
        if self.parser:
            return self.parser(value=value)
        return value

    def calc(self):
        return self.value

    def __str__(self):
        return '%s' %self.calc()


def decimal_parser(*args, **kwargs):
    val = kwargs['value']
    if val is None:
        return Decimal(0)
    return Decimal(str(val))

def float_parser(*args, **kwargs):
    val = kwargs['value']
    if val is None:
        return float(0)
    return float(str(val))


class TotalStatsHandler(XMLStatsBaseHandler):
    DEFAULT_PARSER=decimal_parser

    def initial_value(self):
        return Decimal('0')

    def handle(self, value):
        self.value += self.parse(value)

class AverageStatsHandler(XMLStatsBaseHandler):
    DEFAULT_PARSER=decimal_parser

    def initial_value(self):
        return []

    def handle(self, value):
        self.value.append(self.parse(value))

    def average(self):
        return sum(self.value) / len(self.value)

    def calc(self):
        return self.average()

class MaxStatsHandler(XMLStatsBaseHandler):
    DEFAULT_PARSER=decimal_parser

    def initial_value(self):
        return []

    def handle(self, value):
        self.value.append(self.parse(value))

    def calc(self):
        return max(self.value)

class MinStatsHandler(XMLStatsBaseHandler):
    DEFAULT_PARSER=decimal_parser

    def initial_value(self):
        return []

    def handle(self, value):
        self.value.append(self.parse(value))

    def calc(self):
        return min(self.value)

class StdDevStatsHandler(XMLStatsBaseHandler):
    DEFAULT_PARSER=float_parser

    def initial_value(self):
        return []

    def handle(self, value):
        self.value.append(self.parse(value))

    def calc(self):
        try:
            import numpy
        except ImportError:
            return 'You need to install numpy for this calculation.'
        return numpy.std(self.value)

class CountStatsHandler(XMLStatsBaseHandler):

    def initial_value(self):
        return Decimal('0')

    def handle(self, value):
        self.value += Decimal(1)

    def parse(self, value):
        return 1

class OccurrenceStatsHandler(XMLStatsBaseHandler):
    """ How many times each type occurs """

    def initial_value(self):
        return []

    def handle(self, value):
        self.value.append(value)

    def counts(self):
        counts = SortedDict()
        for key in set(self.value):
            counts[key] = self.value.count(key)
        return counts

    def calc(self):
        sio = StringIO()
        pprint.pprint(self.counts(), sio, 2)
        sio.seek(0)
        return '\n\t' + sio.read()

class XMLStats:
    def __init__(self):
        self.map = self.get_map()
        self.reset()

    def get_map(self):
        """ The map is a group of:
                xml_path : value_handler
                e.g. callflow/times/transfer_time:TotalStatsHandler
        """
        return SortedDict()

    def string_xml_from_file(self, path):
        return file(path, mode='r').read()

    def unquote_string(self, string):
        return urllib.unquote(string)

    def reset(self):
        self.stats = SortedDict()

    def xml_from_file(self, path):
        s = self.string_xml_from_file(path)
        try:
            return ET.fromstring(s)
        except Exception:
            s = self.unquote_string(s)
            return ET.fromstring(s)

    def process_xml(self, xml):
        for path, handler in self.map.values():
            node = xml.find(path)
            value = node is not None and node.text or None
            handler.handle(value)

    def __str__(self):
        s = ''
        for name, handler in self.map.items():
            s += '%s : %s\n' %(name, handler[-1])
        return s
