class Singleton(object):
    """
    We use a simple singleton pattern in Breadcrumbs.
    Example from http://svn.ademar.org/code/trunk/junk-code/singleton_vs_borg.py
    """
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it._1st_init(*args, **kwds)
        return it

    def _1st_init(self, *args, **kwds):
        pass
