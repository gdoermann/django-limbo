import tidy
import os
import logging

logger = logging.getLogger(__name__)

INDENT = True
INDENT_SPACES = 4
WRAP = 0

UNICODE_MAP = {
        u'\u2000': " ",
        u'\u2001': " ",
        u'\u2002': " ",
        u'\u2003': " ",
        u'\u2004': " ",
        u'\u2005': " ",
        u'\u2006': " ",
        u'\u2007': " ",
        u'\u2008': " ",
        u'\u2009': " ",
        u'\u200A': " ",
        u'\u200B': " ",
        u'\u200C': " ",
        u'\u200D': " ",
        u'\u2010': "-",
        u'\u2011': "-",
        u'\u2012': "-",
        u'\u2013': "-",
        u'\u2014': "-",
        u'\u2015': "-",
        u'\u2018': "'",
        u'\u2019': "'",
        u'\u201A': "'",
        u'\u201B': "'",
        u'\u201C': '"',
        u'\u201D': '"',
        u'\u201E': '"',
        u'\u201F': '"',
        u'\u2022': '*',
        u'\u2023': '*',
        u'\u2024': '.',
        u'\u2025': '.',
        u'\u2026': '.',
        u'\u2027': '.',
        u'\u2028': '\n',
        u'\u2029': '\n',
        u'\u202A': '',
        u'\u202B': '',
        u'\u2032': "'",
        u'\u2033': "''",
        u'\u2034': "'''",
        u'\u2035': "'",
        u'\u2036': "''",
        u'\u2037': "'''",
        u'\u2038': "^",
        u'\u2039': "<",
        u'\u203A': ">",
        u'\u203B': "*",
        u'\u203C': "!",
        u'\u2043': "-",
        u'\u204E': "*",
}


def clean_unicode(string):
    for ch, r in UNICODE_MAP.items():
        string = string.replace(ch, r)
    return string

def tidy_html(messy_text, options=None):
    if options is None: options = {}
    if not messy_text:  # don't bother tidying an empty string
        logger.warning('Tidy an empty string? No thanks.')
        return messy_text
    defaults = {
        'indent': INDENT,
        'indent-spaces': INDENT_SPACES,
        'wrap': WRAP,
    }
    defaults.update(options)
    cleaned = tidy.parseString(str(messy_text), **defaults)
    cleaned_text = str(cleaned).strip()
    if cleaned.errors:
        msg = ' '.join([str(e) for e in cleaned.errors])
        logger.debug(os.linesep.join(['Errors while tiding!', msg, '-' * 79]))
    if not cleaned_text:
        # Your response text was too disgustingly messy for tidy to even
        ## return a value. Be ashamed of your filth; you are dirty.
        if not cleaned.errors:
            logger.error('Tidy reported no errors, but your '
                'tidied document was empty.')
        return messy_text
    return cleaned_text


def tidy_xml(string):
    return clean_unicode(tidy_html(string, {'input-xml': True}))
