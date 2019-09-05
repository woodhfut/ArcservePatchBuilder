from django.shortcuts import render
import os
from wsgiref.util import FileWrapper
from django.http import HttpResponse
from django.conf import settings
# Create your views here.
def index(request):
    return render(request, 'UDP/index.html', {})

def Share_patch(request, patch):
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