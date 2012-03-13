from django.conf import global_settings

def number_tuple_from_string(s):
    num_parts = []
    tup = s.split('.')
    for part in tup:
        try:
            num_parts.append(int(part))
        except ValueError:
            pass
    return tuple(num_parts)

class Version:
    def __init__(self, number, tup):
        self.number = number
        self.tuple = tup

    @property
    def display(self):
        return '.'.join(self.tuple)

    @property
    def choice(self):
        return self.number, self.display

    @property
    def number_tuple(self):
        return number_tuple_from_string(self.display)

    def __eq__(self, other):
        if isinstance(other, basestring):
            return other == self.display
        elif isinstance(other, Version):
            return self.tuple == other.tuple
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, basestring):
            return self.number_tuple < number_tuple_from_string(other)
        elif isinstance(other, Version):
            return self.number_tuple < other.number_tuple
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, basestring):
            return self.number_tuple > number_tuple_from_string(other)
        elif isinstance(other, Version):
            return self.number_tuple > other.number_tuple
        else:
            return False

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other