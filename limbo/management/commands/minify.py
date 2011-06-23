from django.core.management.base import BaseCommand
from django.conf import settings
import os
from limbo import css_util
from os.path import dirname

limbo_root = os.path.join(dirname(dirname(dirname(__file__))), 'static')
JS_COMPILER = 'java -jar %s' %os.path.join(os.path.split(__file__)[0], 'compiler.jar')
class Command(BaseCommand):
    args = ''
    help = 'Builds javascript into one file for release.'

    def handle(self, *args, **options):
        scripts = list(settings.JAVASCRIPTS)
        JS_ROOT = os.path.join(limbo_root, 'js')
        CSS_ROOT = os.path.join(limbo_root, 'css')
        sheets = list(settings.STYLE_SHEETS)
        def compile_sheets(path, append = True):
            for f in os.listdir(path):
                if os.path.splitext(f)[-1].lower() == '.less':
                    name = os.path.splitext(f)[0] + '.css'
                    if name not in sheets and append:
                        sheets.append(name)
                    cmd = 'lessc %s > %s' %(os.path.join(path, f), os.path.join(path, name))
                    print cmd
                    os.system(cmd)
        compile_sheets(CSS_ROOT)

        css_args = []
        for sheet in sheets:
            css_args.append('--css_file=%s' %os.path.join(CSS_ROOT, sheet))
        css_args.append('--output_file=%s' %os.path.join(CSS_ROOT, 'limbo.min.css'))
        print css_args
        css_util.main(css_args)

        command = JS_COMPILER
        for script in scripts:
            command += ' --js %s' %os.path.join(JS_ROOT, script)
        command += ' --js_output_file %s' %os.path.join(JS_ROOT, "limbo.min.js")
        print command
        os.system(command)
