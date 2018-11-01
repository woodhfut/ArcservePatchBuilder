from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

class UploadPatchForm(forms.Form):
    version = forms.CharField()
    email = forms.EmailField(required=False)
    patch = forms.FileField()

    def clean_version(self):
        ver = self.cleaned_data.get('version', None)
        if not ver or ver not in settings.SUPPORTED_VERSIONS:
            raise forms.ValidationError(_('Unsupported version'), code=_('Unsupported_version'))
        return ver
    
    # def clean_email(self):
    #     email = self.cleaned_data.get('email', None)
    #     if email and  not email.lower().endswith('arcserve.com'):
    #         raise forms.ValidationError(_('Not Arcserve.com email'), code=_('Unsupported_email'))
    #     return email
    