from limbo.apps.changelog.models import Change
from limbo import forms

class ChangeForm(forms.ModelForm):
    description = forms.CharField(widget=forms.AutoResizeTextarea())
    class Meta:
        model = Change
        exclude = ('created', 'modified',)
        prepopulated_fields = {"slug": ("title",)}
        