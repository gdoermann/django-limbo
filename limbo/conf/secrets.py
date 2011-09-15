"""
Usage:
    Pass in a secret file:
    secrets = secret_settings('/path/to/secrets.conf')



    # secrets.conf
    [MAIN]
    SECRET_KEY = WLnvi)_#LKnif



"""
import os
import ConfigParser
from django.core.exceptions import ImproperlyConfigured

class ConfigSettings:
    MAIN = 'MAIN'
    def __init__(self, *files, **kwargs):
        self.configs = []
        secret = ConfigParser.SafeConfigParser()
        secret.optionxform = lambda x: x.upper()
        self.secret = secret
        default_cfg=kwargs.pop('default_cfg', None)
        if default_cfg and os.path.exists(default_cfg):
            self.add_cfg(default_cfg)
        for path in files:
            path_default = self.defaults_config_path(path)
            if path_default and os.path.exists(path_default):
                self.add_cfg(path_default)
            self.add_cfg(path)
        if not self.configs:
            raise ImproperlyConfigured("You must specify a config file to use ConfigSettings")


    def add_cfg(self, path):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise ImproperlyConfigured('Config file does not exist: %s' % path)
        if path and os.path.exists(path):
            self.secret.read(path)
        self.configs.append(path)

    @classmethod
    def defaults_config_path(cls, settings_file):
        setting_dir = os.path.dirname(settings_file)
        return os.path.join(setting_dir, 'defaults.cfg')


    @classmethod
    def locals_config_path(cls, settings_file):
        setting_dir = os.path.dirname(settings_file)
        return os.path.join(setting_dir, 'locals.cfg')

    def group_dict(self, name, default=None):
        items = self.items(name, default)
        if items in [default, None]:
            return default
        return dict(items)

    def get(self, name, section=MAIN, default=None):
        if self.secret.has_section(section) and self.secret.has_option(section, name):
            return self.secret.get(section, name)
        else:
            return default

    def getboolean(self, name, section=MAIN, default=None):
        if self.secret.has_section(section) and self.secret.has_option(section, name):
            return self.secret.getboolean(section, name)
        else:
            return default

    def getint(self, name, section=MAIN, default=None):
        if self.secret.has_section(section) and self.secret.has_option(section, name):
            return self.secret.getint(section, name)
        else:
            return default

    def getfloat(self, name, section=MAIN, default=None):
        if self.secret.has_section(section) and self.secret.has_option(section, name):
            return self.secret.getfloat(section, name)
        else:
            return default

    def getlist(self, name, section=MAIN, default=[]):
        value = self.get(name, section, default)
        if not value:
            return default
        return [item.strip() for item in value.split(',')]

    def gettuple(self, name, section=MAIN, default=[]):
        value = self.get(name, section, default)
        if not value:
            return tuple(default)
        return tuple([item.strip() for item in value.split(',')])

    def get_loglevel(self, name, section=MAIN, default='WARNING'):
        try:
            return self.getint(name, section)
        except:
            import logging
            return logging.getLevelName(self.get(name, section, default))

    def getdir(self, name, section=MAIN, default=None):
        return self.get(name, section, default)

    def items(self, section, default=None):
        if self.secret.has_section(section):
            return self.secret.items(section)
        else:
            return default