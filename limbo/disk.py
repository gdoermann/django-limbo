import os
from django.core.cache import cache
from limbo.classes import Singleton
from limbo.strings import md5_hash

__author__ = 'gdoermann'

class FileChecker(Singleton):
    FILE_KEY = 'file-exists_%(md5)s'

    def __getitem__(self, filepath):
        md5 = md5_hash(filepath)
        key = self.FILE_KEY % locals()
        cached = cache.get(key, None)
        if cached is not None:
            return cached
        else:
            exists = os.path.exists(filepath)
            cache.set(key, exists)
            return exists

default_checker = FileChecker()