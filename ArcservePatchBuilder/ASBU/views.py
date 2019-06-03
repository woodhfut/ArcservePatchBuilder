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
    # if request.method =='POST':
    #     form = UploadPatchForm(request.POST, request.FILES)
    #     if form.is_valid():
    #         patchname = form.cleaned_data['patch'].name
    #         #threading.Thread(target=handle_uploaded_patch, args=(request.FILES['patch'], patchname)).start()
    #         handle_uploaded_patch(request.FILES['patch'], patchname)
    #         return render(request, 'ASBU/index.html', {
    #             'version': form.cleaned_data['version'],
    #             'email': form.cleaned_data['email'],
    #             'patch': patchname,
    #             'result': True,
    #         })
            
    #     else:
    #         return HttpResponse('invalid form')
    # else:
    return render(request, 'ASBU/index.html', {})


def handle_uploaded_patch(f,name):
    patchpath = os.path.join(settings.PATCH_ROOT_URL, name)
    with open(patchpath, 'wb') as patch:
        for chunk in f.chunks():
            patch.write(chunk)


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