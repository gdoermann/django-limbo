from django.template.defaultfilters import slugify
from django.utils.datastructures import SortedDict
import os
import traceback
import pickle
from limbo.classes import Singleton
import logging

__author__ = 'gdoermann'

logger = logging.getLogger(__file__)

class Properties(dict):
    def __init__(self, filepath):
        self.filepath = filepath
        dict.__init__(self)
        self.has_changed = False

    def reload(self):
        if not os.path.exists(self.filepath):
            f = open(self.filepath, 'w')
            f.close()
        self.file = open(self.filepath, 'r+')
        try:
            objs = pickle.load(self.file)
            self.update(dict(objs))
        except Exception:
            pass

    def save(self):
        if not self.has_changed:
            return
        try:
            self.file.close()
            self.file = open(self.filepath, 'w')
            s = pickle.dumps(self.items())
            self.file.write(s)
            self.file = open(self.filepath, 'r+')
            self.has_changed = False
        except Exception:
            logger.error(traceback.format_exc())

    def __setitem__(self, key, value):
        if self.get(key) != value:
            self.has_changed = True
        return dict.__setitem__(self, key, value)

    def set(self, key, value):
        return self.__setitem__(key, value)

    def pop(self, k, d=None):
        self.has_changed = True
        return dict.pop(self, k, d=d)

    def update(self, *args, **kwargs):
        self.has_changed = True
        return dict.update(self, *args, **kwargs)

class BaseStorage(object):
    """
     NOTE: Storage keys are case INSENSITIVE.  So TESTING is the same as testing.
    """
    reserved_names = ('reload', 'check', 'set', 'get', 'save', 'properties', 'reserved_names')
    
    def setup(self, appname=None, properties = SortedDict(), directories = SortedDict(), *args, **kwds):
        default_home = os.environ.get('USERPROFILE') or os.environ.get('HOME')
        home_dir = kwds.pop('home', None) or default_home
        if home_dir.startswith('~'):
            home_dir = os.path.join(default_home, home_dir[2:])
        self.home = home_dir
        base_path = appname and os.path.join(home_dir, '.%s' %(slugify(appname))) or home_dir
        self.base = base_path
        self.check(self.base)

        for name, path in directories.items():
            if name in self.reserved_names:
                raise ValueError('%s is a reserved name: %s' %(name))
            name = slugify(name).upper()
            if isinstance(path, basestring):
                path = [path]
            dirname = os.path.join(base_path, *path)
            setattr(self, name, dirname)
            self.check(dirname)

        self.properties = SortedDict()
        for name, path in properties.items():
            if name in self.reserved_names:
                raise ValueError('%s is a reserved name: %s' %(name))
            name = slugify(name)
            if isinstance(path, basestring):
                path = [path]
            self.properties[name] = Properties(os.path.join(base_path, *path))
            setattr(self, name, self.properties[name])
            self.check(os.path.dirname(self.properties[name].filepath))
        self.reload()


    def reload(self, name=None):
        if name:
            name = slugify(name)
            self.properties[name].reload()
        else:
            for p in self.properties.values():
                p.reload()

    def check(self, d):
        if not os.path.exists(d):
            os.makedirs(d)

    @property
    def rvalues(self):
        rvalues = self.properties.values()
        rvalues.reverse()
        return rvalues

    def set(self, name, value):
        name = slugify(name)
        values = self.rvalues
        for p in values:
            if p.has_key(name):
                p[name] = value
                p.save()
                return
        values[0][name] = value

    def get(self, name, default=None):
        name = slugify(name)
        for p in self.properties.values():
            if p.has_key(name):
                return p[name]
        return default

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        key = slugify(key)
        for p in self.rvalues:
            if p.has_key(key):
                del p[key]
                return

    def __delattr__(self, name):
        if name in self.reserved_names:
            raise ValueError('You cannot delete a reserved attribute.')
        if self.has_key(name):
            return self.__delitem__(name)
        return super(BaseStorage, self).__delattr__(name)

    def __getattribute__(self, name):
        try:
            return super(BaseStorage, self).__getattribute__(name)
        except AttributeError, e:
            val = self.get(name)
            if val:
                return val
            else:
                raise

    def keys(self):
        keys = []
        for p in self.properties.values():
            keys += p.keys()
        return keys

    def has_key(self, key):
        key = slugify(key)
        return key in self.keys()

    def save(self):
        for p in self.properties.values():
            p.save()

class Storage(Singleton, BaseStorage):
    """ An example/basic implementation of a singleton storage class"""
    def _1st_init(self, appname, properties = SortedDict(), directories = SortedDict(), *args, **kwds):
        self.setup(appname=appname, properties = properties , directories = directories , *args, **kwds)

if __name__ == '__main__':
    storage = Storage( 'limbo',
        properties = SortedDict((
            ('settings', 'client.settings'),
        )), directories = SortedDict((
            ('offline_path', ('storage', 'offline')),
            ('app_path', ('storage', 'app')),
            ('local_path', ('storage', 'local')),
        ))
    )
    assert(os.path.exists(storage.offline_path))
    assert(os.path.exists(storage.app_path))
    assert(os.path.exists(storage.local_path))
    assert(os.path.exists(storage.settings.filepath))
    storage = Storage()
    assert(os.path.exists(storage.settings.filepath))
    assert(storage.settings.filepath)
    print 'All tests passed.'