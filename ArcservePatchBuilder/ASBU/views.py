from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadPatchForm
from django.conf import settings
import os
import threading
from .tasks import add

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