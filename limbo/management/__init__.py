from django.core.exceptions import ObjectDoesNotExist

__author__ = 'gdoermann'

from optparse import make_option
from django.core.management.base import BaseCommand
import logging


class LimboCommand(BaseCommand):
    subcommand = ''
    option_list = BaseCommand.option_list + (
        make_option('--log_level',
            type='int',
            dest='log_level',
            default=20,
            help='Python logging level'),
        )

    def __init__(self):
        self.log = logging.getLogger(self.subcommand or __file__)
        super(LimboCommand, self).__init__()

    def setup(self, *args, **options):
        self.log.setLevel(options['log_level'])

    def _runtime_error(self, msg):
        self.log.error(msg)
        self.print_help()
        exit(1)

    def print_help(self, prog_name='./manage.py', subcommand = None):
        subcommand = subcommand or self.subcommand
        super(LimboCommand, self).print_help(prog_name, subcommand)
