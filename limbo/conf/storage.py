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
        s = self.file.read()
        try:
            self.update(pickle.loads(s))
        except Exception:
            pass

    def save(self):
        if not self.has_changed:
            return
        try:
            self.file.close()
            self.file = open(self.filepath, 'w')
            s = pickle.dumps(self)
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

    def update(self, E=None, **F):
        self.has_changed = True
        return dict.update(self, E=E, **F)

class BaseStorage:
    reserved_names = ('reload', 'check', 'set', 'get', 'save', 'properties', 'reserved_names')
    
    def setup(self, appname, properties = SortedDict(), directories = SortedDict(), *args, **kwds):
        home_dir = os.environ.get('USERPROFILE') or os.environ.get('HOME')
        self.home = home_dir
        base_path = os.path.join(home_dir, '.%s' %(slugify(appname)))
        self.base = base_path
        self.check(self.base)

        for name, path in directories.items():
            if name in self.reserved_names:
                raise ValueError('%s is a reserved name: %s' %(name))
            name = slugify(name)
            if isinstance(path, basestring):
                path = [path]
            setattr(self, name, os.path.join(base_path, *path))
            self.check(getattr(self, name))

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
            self.reload(name)


    def reload(self, name=None):
        if name:
            self.properties[name].reload()
        else:
            for p in self.properties.values():
                p.reload()

    def check(self, d):
        if not os.path.exists(d):
            os.makedirs(d)

    def set(self, name, value):
        rvalues = self.properties.values()
        rvalues.reverse()
        for p in rvalues:
            if p.has_key(name):
                p[name] = value
                p.save()
                return
        rvalues[0][name] = value

    def get(self, name, default=None):
        for p in self.properties.values():
            if p.has_key(name):
                return p[name]
        return default

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)

    def save(self):
        for p in self.properties:
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