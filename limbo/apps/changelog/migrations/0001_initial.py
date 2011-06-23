# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Change'
        db.create_table('changelog_change', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100, db_index=True)),
            ('version', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=10, db_index=True)),
        ))
        db.send_create_signal('changelog', ['Change'])


    def backwards(self, orm):
        
        # Deleting model 'Change'
        db.delete_table('changelog_change')


    models = {
        'changelog.change': {
            'Meta': {'ordering': "('-created', '-title')", 'object_name': 'Change'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '10', 'db_index': 'True'})
        }
    }

    complete_apps = ['changelog']
