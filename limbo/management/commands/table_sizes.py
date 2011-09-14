from optparse import make_option
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import get_models, get_app
from limbo.formatting import str_size_to_bytes, formatted_bytes

class DBTable:
    def __init__(self, model, result):
        self.model = model
        self.result = result
        if not isinstance(result, basestring):
            result = result[0]
        self.raw_size = result

    @property
    def model_name(self):
        if isinstance(self.model, basestring):
            return self.model
        return self.model.__name__

    @property
    def app_label(self):
        if isinstance(self.model, basestring):
                return self.model
        return self.model._meta.app_label

    @property
    def size(self):
        """ Return size in bytes
        """
        return str_size_to_bytes(self.raw_size)

    @property
    def formatted_size(self):
        return formatted_bytes(self.size)

    def __cmp__(self, other):
        return cmp(other.size, self.size)

    def __str__(self):
        if isinstance(self.model, basestring):
            name = self.model
        else:
            name = '%s.%s' %(self.app_label, self.model_name)
        name += ' '*(40 - len(name))
        return '%s%s' %(name, self.formatted_size)

class Command(BaseCommand):
    args = '<app app ...>'
    help = 'Table sizes for specified apps, or all apps if no args are specified.  Sorted by order, biggest to smallest.'
    option_list = BaseCommand.option_list +  (
        make_option('-m', '--max-tables', action='store', dest='max', default=None,
            type='int', help='Max number of tables to output.'),
    )

    STATEMENT = """SELECT pg_total_relation_size('%s');"""
    DB_STATEMENT = """SELECT pg_database_size('%s');"""
    def handle(self, *args, **options):
        if not args:
            apps = []
            for model in get_models():
                try:
                    apps.append(get_app(model._meta.app_label))
                except ImproperlyConfigured:
                    pass
        else:
            apps = []
            for arg in args:
                apps.append(get_app(arg))
        
        table_dict = {}
        cursor = connection.cursor()
        
        for app in apps:
            for model in get_models(app):
                key = '%s.%s' %(model._meta.app_label, model.__name__)
                if table_dict.has_key(key):
                    continue
                tbl = model._meta.db_table
                sql = self.STATEMENT % tbl
                cursor.execute(sql)
                row = cursor.fetchone()
                dbtbl = DBTable(model, row)
                table_dict[key] = dbtbl

        tables = table_dict.values()
        tables.sort()
        max = options['max']
        print '\n', '-'*75
        print 'Table Sizes:'
        print '-'*75
        for i, table in enumerate(tables):
            if max and i >= max:
                break
            print str(table)

        db_dict = {}
        for name, dbsettings in settings.DATABASES.items():
            sql = self.DB_STATEMENT % dbsettings['NAME']
            cursor.execute(sql)
            row = cursor.fetchone()
            dbtbl = DBTable(name, row)
            db_dict[name]  = dbtbl

        databases = db_dict.values()
        databases.sort()
        print '\n', '-'*75
        print 'Database Sizes:'
        print '-'*75
        for db in databases:
            print str(db)
