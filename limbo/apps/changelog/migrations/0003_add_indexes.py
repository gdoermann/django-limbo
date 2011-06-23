# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding index on 'Change', fields ['datetime_created']
        db.create_index('changelog_change', ['datetime_created'])

        # Adding index on 'Change', fields ['datetime_modified']
        db.create_index('changelog_change', ['datetime_modified'])


    def backwards(self, orm):
        
        # Removing index on 'Change', fields ['datetime_modified']
        db.delete_index('changelog_change', ['datetime_modified'])

        # Removing index on 'Change', fields ['datetime_created']
        db.delete_index('changelog_change', ['datetime_created'])


    models = {
        'changelog.change': {
            'Meta': {'ordering': "('-datetime_created', '-title')", 'object_name': 'Change'},
            'datetime_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'datetime_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {'default': 0, 'max_length': '10', 'db_index': 'True'})
        }
    }

    complete_apps = ['changelog']
