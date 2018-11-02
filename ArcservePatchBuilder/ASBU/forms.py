from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import re

class UploadPatchForm(forms.Form):
    version = forms.CharField()
    email = forms.EmailField(required=False)
    patch = forms.FileField()

    def clean_version(self):
        ver = self.cleaned_data.get('version', None)
        if not ver or ver not in settings.PATCH_SUPPORTED_VERSIONS:
            raise forms.ValidationError(_('Unsupported version'), code=_('Unsupported_version'))
        return ver
    
    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        if email and  not email.lower().endswith('arcserve.com'):
            raise forms.ValidationError(_('Not Arcserve.com email'), code=_('Unsupported_email'))
        return email

    def clean_patch(self):
        patch = self.cleaned_data.get('patch', None)
        if not patch:
            raise forms.ValidationError(_('Patch needed'), code=_('Patch_needed'))
        else:
            try:
                idx = patch.name.rindex('.')
                ext = patch.name[idx+1:].lower()
                name = patch.name[:idx].lower()
                if not ext in settings.PATCH_SUPPORTED_EXTENSIONS:
                    raise forms.ValidationError(_('Unsupported patch extension'), code=_('Unsupported_patchext'))
                elif not re.match(r'^[tp]\d{8}$', name):
                    raise forms.ValidationError(_('Unsupported patch name'), code=_('unsupported_patchname'))     
            except ValueError:
                raise forms.ValidationError(_('Unsupported patch name'), code=_('Unsupported_patchname'))
        return patch