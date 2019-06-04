from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadPatchForm
from django.conf import settings
import os
import threading
from .tasks import add
from wsgiref.util import FileWrapper
from django.http import HttpResponse

def index(request):
    return render(request, 'ASBU/index.html', {})


def Share_patch(self, patch):
    try:
        patchpath = os.path.join(settings.PATCH_ROOT_URL, patch)
        patchexepath = os.path.join(patchpath, patch+'.exe')
        wrapper     = FileWrapper(open(patchexepath, 'rb'))

    except IOError as ex:
        return HttpResponse(ex)
    response    = HttpResponse(wrapper,content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename={}.exe'.format(patch)
    response['Content-Length']      = os.path.getsize(patchexepath)
    return response