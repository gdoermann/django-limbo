import re

__author__ = 'gdoermann'


EXCLUDE_LOGIC = re.compile('([^|^&^\(^\).]*)')

def separate_logic(term):
    term = term.replace('||', '|').replace('&&', '&')
    sub_items = EXCLUDE_LOGIC.findall(term)
    keys = {}
    i = 0
    for item in sub_items:
        if item.strip():
            i += 1
            key = 'term_%i' % i
            term = term.replace(item, '%%(%s)s' % key)
            keys[key] = item.strip()
    return term, keys
