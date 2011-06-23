import re
from django.core.validators import validate_email

SMS_REGEX = re.compile('^(1|)\d{10}$')
def valid_sms(number):
    if SMS_REGEX.match(str(number)):
        return True
    else:
        return False

def clean_sms(number):
    if number is None:
        return
    clean_chars = ['-', '(', ')', '+', ' ']
    for c in clean_chars:
        number = number.replace(c, '')
    return number

def valid_email(email):
    """ Checks to see if email is valid, returns True or False """
    try:
        validate_email(email)
        return True
    except:
        return False
