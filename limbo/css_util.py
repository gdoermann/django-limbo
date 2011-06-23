#!/usr/bin/env python2.5

# Copyright (c) 2010 SameGoal LLC.
# All Rights Reserved.
# Author: Andy Hochhaus

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import getopt, sys, re

def usage():
    print "usage: ./css_util.py [--css_file=<file>]"
    print "                                         [--css_map_file=<file>]"
    print "                                         [--static_versions_map_file=<file>]"
    print "                                         [--output_file=<file>]"
    print "                                         [--output_as_ctemplate]"
    print "                                         [--verbose] [--help]"
    print ""
    print "--css_file: input css file. This flag can be specified zero or more"
    print "                        times. These files will be processed to rename classes,"
    print "                        substitute static file references, remove comments, and"
    print "                        output a google-ctemplate for use in the serving system."
    print "                        A ctemplate's are used for the intelligent removal of"
    print "                        whitespace."
    print ""
    print "--css_map_file is the output file where the map from original to"
    print "                             obfuscated CSS class name is written. This file will"
    print "                             be created or overwritten as necessary."
    print ""
    print "--static_versions_map_file is the input file to read a map from"
    print "                                                     the version information for each static"
    print "                                                     file."
    print ""
    print "--output_file is the output file to embed in the binary for serving."
    print "                            Using ctemplates reduces filesize by eliminating"
    print "                            newlines and whitespace inteligently."
    print ""
    print "--output_as_ctemplate generate output as a ctemplate rather than"
    print "                                            a standard CSS file."
    print ""
    print "--help display this help screen."
    print ""
    print "--verbose displays detailed debugging information."

def concat_css_file(list_):
    orig_css_list = []
    for css_file in list_:
        f = open(css_file, 'rb')
        orig_css_list.append(f.read())
        f.close()
    return '\n'.join(orig_css_list)

def strip_comments(css):
    comments = re.compile('/\*.*?\*/', re.MULTILINE | re.DOTALL)
    return comments.sub('', css)

def sub_static_files(css, static_versions_map_file):
    f = open(static_versions_map_file, 'r')
    s_ = f.read()
    f.close()
    static_file_versions = eval(s_)

    for filename in static_file_versions.keys():
        version = static_file_versions[filename]['version']
        last_period = filename.rfind('.')
        if last_period < 0:
            raise Exception('Filename does not contain a period: %s.' % filename)
        versioned_filename = '%s_%s.%s' % (filename[:last_period],
                                                                             str(version),
                                                                             filename[last_period + 1:])
        url = re.compile("url\s*\(\s*'%s'\\s*\)" % filename)
        css = url.sub("url('%s');" % versioned_filename, css)

    return css

def uniq(list_):
    u = []
    for item in list_:
        if item not in u:
            u.append(item)
    return u

def get_class_names(css):
    first_class = css.find('{')
    if first_class < 0:
        raise Exception('Generatred CSS file requires at least one class.')
    # get the first selector
    selectors_list = [ css[:first_class], ]
    # get all other selectors
    selectors_regex = re.compile('}(.*?){', re.MULTILINE | re.DOTALL)
    selectors_list = selectors_regex.findall(css)

    class_regex = re.compile('\.([-]?[_a-zA-Z][_a-zA-Z0-9-]*)',
                                                     re.MULTILINE | re.DOTALL)
    class_names_list = []
    class_names_dups = {}
    for selector in selectors_list:
        class_list = class_regex.findall(selector)
        for cls in class_list:
            cls_lower = cls.lower()
            class_names_list.append(cls_lower)
            if cls_lower != cls:
                if not class_names_dups.has_key(cls_lower):
                    class_names_dups[cls_lower] = [ cls, ]
                else:
                    if cls not in class_names_dups[cls_lower]:
                        class_names_dups[cls_lower].append(cls)

    class_names_list = uniq(class_names_list)
    class_names_list.sort()
    return (class_names_list, class_names_dups)

class CssName:
    def __init__(self):
        self.__s = ''

    def __sub_char(self, c, i):
        self.__s = self.__s[:i] + c + self.__s[i + 1:]


    def get(self):
        if len(self.__s) == 0:
            self.__s = 'a'
            return self.__s

        active_digit_loc = len(self.__s) - 1

        carry = True
        while carry:
            carry = False

            # increment active_digit_loc
            self.__sub_char(chr(ord(self.__s[active_digit_loc]) + 1),
                                            active_digit_loc)

            if (self.__s[active_digit_loc] > 'z'):
                self.__sub_char('a', active_digit_loc)

                active_digit_loc -= 1
                if active_digit_loc < 0:
                    self.__s = 'a%s' % self.__s
                else:
                    carry = True

        return self.__s

def build_css_map(class_name_list):
    css_map = {}
    name_gen = CssName()
    for class_name in class_name_list:
        for part in class_name.split('-'):
            if not css_map.has_key(part):
                css_map[part] = name_gen.get()

    # some orig_class_names may collide with obfescated_class_names provided by
    # our map. swap values in our map such that every "colliding" class name
    # points to itself and is a noop during the renaming stage.
    changes = True
    while changes:
        changes = False
        for orig_class_name in class_name_list:
            for (src_name, dst_name) in css_map.items():
                if orig_class_name == src_name:
                    continue
                if orig_class_name == dst_name:
                    css_map[src_name] = css_map[orig_class_name]
                    css_map[orig_class_name] = dst_name
                    changes = True

    return css_map

def write_css_map_file(class_name_list,
                                             css_map,
                                             class_names_dups,
                                             css_map_file):
    lines = []
    specified_parts = {}
    for class_name in class_name_list:
        for part in class_name.split('-'):
            if not specified_parts.has_key(part):
                lines.append("'%s': '%s'" % (part, css_map[part]))
                specified_parts[part] = True

    for class_name in class_name_list:
        if class_names_dups.has_key(class_name):
            for dup_class_name in class_names_dups[class_name]:
                for dup_part in dup_class_name.split('-'):
                    if not specified_parts.has_key(dup_part):
                        lines.append("'%s': '%s'" % (dup_part, css_map[dup_part.lower()]))
                        specified_parts[dup_part] = True

    s = ',\n    '.join(lines)
    s = 'goog.setCssNameMapping({\n    %s\n});\n' % s
    f = open(css_map_file, 'w')
    f.write(s)
    f.close()

def sub_class_names(css, class_name_list, css_map):
    for orig_class_name in class_name_list:
        new_class_name = []
        for part in orig_class_name.split('-'):
            new_class_name.append(css_map[part])
        new_class_name = '-'.join(new_class_name)

        if new_class_name == orig_class_name:
            continue

        # TODO(hochhaus): replace class names in the first selector of the file.
        # Currently only selectors in the file after the first have class names
        # replaced. In practice this is not a large issue as CSS files normally
        # contain browser standardizing code as the first selector. These selectors
        # tend to not contain class names.

        # replace class names that are immediately followed by a '{'
        total = 0
        class_regex1 = re.compile('(}[^{]*?\.)%s({)' % orig_class_name,
                                                            re.MULTILINE | re.DOTALL | re.IGNORECASE)
        num = True
        while num != 0:
            (css, num) = class_regex1.subn('\\1%s\\2' % new_class_name, css)
            total += num

        # replace class names that are followed by whitespace, a period (another
        # class), a comma or a ':' (pseudo classes)
        class_regex2 = re.compile('(}[^{]*?\.)%s([\s.,:][^{]*?{)' % orig_class_name,
                                                            re.MULTILINE | re.DOTALL | re.IGNORECASE)
        num = True
        while num != 0:
            (css, num) = class_regex2.subn('\\1%s\\2' % new_class_name, css)
            total += num

        if total == 0:
            raise Exception('Class not replaced: %s -> %s : %s' %
                                            (orig_class_name, new_class_name, num))
    return css


def ctemplate_format(css, output_file, output_as_ctemplate):
    if output_as_ctemplate:
        css = '{{%%AUTOESCAPE context="CSS"}}\n%s' % css
    f = open(output_file, 'w')
    f.write(css)
    f.close()

def main(argv):
    try:
        params = [
            "css_file=",
            "css_map_file=",
            "static_versions_map_file=",
            "output_file=",
            "output_as_ctemplate",
            "help",
            "verbose",
            ]
        opts, args = getopt.getopt(argv, "", params)
    except getopt.GetoptError, err:
        print str(err)
        print ""
        usage()
        sys.exit(2)

    css_file_list = []
    css_map_file = None
    static_versions_map_file = None
    output_file = None
    output_as_ctemplate = False
    verbose = False
    for o, a in opts:
        if o in [ "--css_file", ]:
            css_file_list.append(a)
        elif o in [ "--css_map_file", ]:
            css_map_file = a
        elif o in [ "--static_versions_map_file", ]:
            static_versions_map_file = a
        elif o in [ "--output_file", ]:
            output_file = a
        elif o in [ "--output_as_ctemplate", ]:
            output_as_ctemplate = True
        elif o in [ "--help", ]:
            usage()
            sys.exit()
        elif o in [ "--verbose", ]:
            verbose = True
        else:
            assert False, "unhandled option."

    if len(css_file_list) < 1:
        print "Error: At least one --css_file is required."
        usage()
        sys.exit(2)

    if not output_file:
        print "Error: --output_file is required."
        usage()
        sys.exit(2)

    # concat all css files together in order
    css = concat_css_file(css_file_list)

    # strip comments
    css = strip_comments(css)

    # replace static_versions file references
    if static_versions_map_file:
        css = sub_static_files(css, static_versions_map_file)
    if css_map_file:
        # get sorted list of all class names
        (class_names_list, class_names_dups) = get_class_names(css)

        # build css_map
        css_map = build_css_map(class_names_list)

        write_css_map_file(class_names_list, css_map, class_names_dups, css_map_file)

        # replace original class names using css_map
        css = sub_class_names(css, class_names_list, css_map)

    # write the css in ctemplate format
    ctemplate_format(css, output_file, output_as_ctemplate)


if __name__ == "__main__":
    main(sys.argv[1:])
