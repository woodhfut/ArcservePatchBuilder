from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from .forms import UploadPatchForm

def index(request):
    if request.method =='POST':
        form = UploadPatchForm(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponse('valid form')
        else:
            return HttpResponse('invalid form')
    else:
        return render(request, 'ASBU/index.html', {})
