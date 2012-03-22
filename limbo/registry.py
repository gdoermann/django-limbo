from limbo.classes import Singleton
from twisted.internet.defer import inlineCallbacks, returnValue

__author__ = 'gdoermann'

class RegistryBase:
    def _1st_init(self, *args, **kwds):
        self.reg= {}
        self.reg.update(kwds)

    def register(self, name, value):
        self.reg[name] = value

    def unregister(self, name):
        del self.reg[name]

    def is_registered(self, name):
        return self.reg.has_key(name)

    def get(self, name):
        return self.reg.get(name)

    def set(self, name, value):
        self.register(name, value)

    def __getitem__(self, item):
        return self.reg[item]

    def __setitem__(self, key, value):
        self.reg[key] = value

    def all(self):
        return self.values()

    def items(self):
        return self.reg.items()

    def values(self):
        return self.reg.values()

    def names(self):
        return self.keys()

    def keys(self):
        return self.reg.keys()


class Registry(Singleton):
    pass

generic = Registry()

class EventRegistry(object):
    def __init__(self, *methods):
        self.methods = [method for method in methods if method]

    def register(self, method):
        if method not in self.methods:
            self.methods.append(method)

    def notify(self, *args, **kwargs):
        for method in self.methods:
            method(*args, **kwargs)

    @inlineCallbacks
    def txnotify(self, *args, **kwargs):
        for method in self.methods:
            yield method(*args, **kwargs)
        yield
        returnValue(None)


    def __call__(self, *args, **kwargs):
        self.notify(*args, **kwargs)