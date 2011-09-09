import datetime
import hashlib
import random
import re
from string import zfill

POPULATION = [chr(x) for x in range(256)]
NULL = ''
UNDERSCORE_PATTERN = re.compile('(?<=[a-z])([A-Z])')
def md5_hash(txt):
    """ Quick md5 hash of any given txt """
    return hashlib.md5(txt).hexdigest()

def random_hash():
    rand = [random.choice(POPULATION) for x in range(25)]
    now = datetime.datetime.now()
    return md5_hash('%s#%s' %(now, rand))

def unique_string(length = None):
     if length is None:
         return random_hash()
     else:
         s = ""
         while len(s) < length:
             s += random_hash()
         return s[:length]

def map_xml(obj, tree, map):
    """
    Takes a map of xml path -> attribute / callable and maps the
    attributes found in the tree to the object.  If the path
    doesn't exist, it skips the node.  If you map to a callable
    it passes the object and the tree node found to the
    callable, otherwise it just sets the text value of the node
    to the object attribute.
    """
    for path, attr in map.items():
        if tree.find(path) is not None:
            if callable(attr):
                attr(obj, tree.find(path))
            else:
                setattr(obj, attr, tree.find(path).text)

numbers = re.compile('\d+')
def increment(s):
    """ look for the last sequence of number(s) in a string and increment """
    if numbers.findall(s):
        lastoccr_sre = list(numbers.finditer(s))[-1]
        lastoccr = lastoccr_sre.group()
        lastoccr_incr = str(int(lastoccr) + 1)
        if len(lastoccr) > len(lastoccr_incr):
            lastoccr_incr = zfill(lastoccr_incr, len(lastoccr))
        return s[:lastoccr_sre.start()]+lastoccr_incr+s[lastoccr_sre.end():]
    return s

def get_unique_username(email):
    """ Creates a unique username from a given email """
    username = email
    if len(username) > 30:
        username = username[:30]
    no_numbers_username = username
    # NOTE: even though this is bad practice, we need to do this import
    ## here instead of in the module namespace
    ## this module, and we don't want to require Django installation on
    ## client machines
    from django.contrib.auth.models import User
    if User.objects.filter(username = username):
        if len(username) == 30:
            username = username[:-4]
        first_username = username + '0000'
        if User.objects.filter(username = first_username):
            last_user = User.objects.filter(username__startswith = username).order_by('-username').exclude(username=no_numbers_username)[0]
            username = increment(last_user.username)
        else:
            username = first_username
    return username

def strip_underscores(str, **attribs):
    return str.replace('_', NULL)


def insert_underscores(str, **attribs):
    return UNDERSCORE_PATTERN.sub('_\\1', str)


def strip_dashes(str, **attribs):
    return str.replace('-', NULL)


def insert_dashes(str, **attribs):
    return UNDERSCORE_PATTERN.sub('-\\1', str)


def to_camel_case(str, **attribs):
    if is_magic(str):
        return str
    else:
        return strip_dashes(strip_underscores(from_camel_case(str).title()))

def is_magic(str):
    return str in ['self', 'cls'] or str.startswith('__') and str.endswith('__')

def from_camel_case(str, **attribs):
    if is_magic(str):
        return str
    else:
        return insert_underscores(str).lower()

def from_camel_case_dashes(str, **attribs):
    if is_magic(str):
        return str
    else:
        return insert_dashes(str).lower()

def unslugify(string):
    return string.replace('-', ' ').replace('_', ' ')

def make_shortname(first, last):
    """ Logic behind creating a short name given a first and last name """
    sname = ''
    if first:
        sname += first
    else:
        return last
    if len(last):
        sname += ' %s.' %last[0]
    return sname

def shortname(user):
    """ Returns a short name of a user.
    Example: Greg Doermann would be Greg D."""
    if user.is_anonymous():
        return None
    sname = user.email
    try:
        new_sname = make_shortname(user.first_name, user.last_name)
        if new_sname:
            sname = new_sname
    except:
        pass
    return sname
