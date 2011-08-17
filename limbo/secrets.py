"""
Usage:
    Pass in a secret file:
    secrets = secret_settings('/path/to/secrets.conf')



    # secrets.conf
    [MAIN]
    SECRET_KEY = WLnvi)_#LKnif



"""
from ConfigParser import ConfigParser

def secret_settings(file):
    secret = ConfigParser()
    secret.optionxform = lambda x: x.upper()
    secret.read(file)
    return secret

