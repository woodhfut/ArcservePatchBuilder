from channels.generic.websocket import WebsocketConsumer
import json
from django.conf import settings
import os
import shutil
from . import utils

from multiprocessing.pool import Pool, ThreadPool

class ASBUStatusConsumer(WebsocketConsumer):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self._version = None
        self._email = None
        self._name = None
        self._uploadFinished = False

    def connect(self):
        print('channel name: ' + self.channel_name)
        self.accept()
    
    def disconnect(self, close_code):
        pass
    

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            text_data_json = json.loads(text_data)
            receiver = text_data_json.get('receiver',None)

            if receiver == 'version':
                self._version = text_data_json['data']
                print('version: ' + self._version )
                self.send(json.dumps({
                    'msgType': 'PatchStatus',
                    'message': 'received patch version: ' + self._version
                }))
            elif receiver == 'email':
                self._email = text_data_json['data']
                print('email: ' + self._email)
                self.send(json.dumps({
                    'msgType': 'PatchStatus',
                    'message' : 'received email: ' + self._email
                }))
            elif receiver == 'patch':
                if 'name' in text_data_json:
                    print('name:' + text_data_json['name'])
                    idx = text_data_json['name'].rindex('\\')
                    self._name = text_data_json['name'][idx+1:]
                    self.send(json.dumps({
                        'msgType': 'PatchStatus',
                        'message': 'received patch name : ' + self._name
                    }))
                    patchpath = os.path.join(settings.PATCH_ROOT_URL, self._name)
                    if os.path.exists(patchpath):
                        os.remove(patchpath)
                elif 'uploadFinished' in text_data_json and text_data_json['uploadFinished']:
                    self._uploadFinished = True
                    self._unzip_patchfile()
                    #self._create_patch(self._name)
            else:
                print('unknown receiver.')
        if bytes_data:
            #print('received file data size...' + str(len(bytes_data)))
            # self.send(json.dumps({
            #     'msgType': 'PatchStatus',
            #     'message' : 'start uploading patch: ' + self._name
            # }))
            self._handle_patch_data(bytes_data)
                
    def _create_patch(self, name):
        self.send(json.dumps({
            'msgType': 'PatchStatus',
            'message': 'start creating patch...'
        }))
        if name.find('.') == -1:
            fixname = name
        else:
            fixname = name[:name.find('.')]
        
        fixpath = os.path.join(settings.PATCH_ROOT_URL, fixname)
        print('fixpath is {}'.format(fixpath))
        results = []
        if os.path.exists(fixpath):
            files = []
            for (dirpath, _, filenames) in os.walk(fixpath):
                for f in filenames:
                    if not f.lower() == fixname.lower()+'.exe': #ignore the created patch file, in case we run the same patch multiple times.
                        files.append(os.path.join(dirpath, f))
            
            print(files)
            if any(f.lower().endswith(fixname.lower() + '.txt') for f in files):
                print('{} exists, good to go. '.format(fixname+ '.txt'))
            else:
                print('{} is not included, invalid patch zip.'.format(fixname + '.txt'))
                self.send('{} is not included, invalid patch zip.'.format(fixname + '.txt'))
                self.close()
                return
            
            pool = ThreadPool(processes=len(files))
            for f in files:
                if not f.lower().endswith('.txt'):# and not utils.isBinarySigned(f):
                    print('trying to sign file ' + f)
                    ar = pool.apply_async(utils.signBinary, (f,))
                    results.append(ar)
            
            pool.close()
            pool.join()
        else:
            print('fix path {} doesnot exists... maybe something wrong when unzip the patch. '.format(fixpath))
            self.send(json.dumps({
                'msgType': 'Error',
                'message': 'fix path {} doesnot exists... maybe something wrong when unzip the patch. '.format(fixpath)
            }))
            self.close()
            return
        if len(results)==0 or all([x.get()[1] for x in results]):
            print('all binaries get signed successfully...')
            self.send(json.dumps({
                'msgType': 'PatchStatus',
                'message': 'all binaries get signed successfully...'
            }))
            print('start to create .caz file.')
        else:
            for ar in results:
                r = ar.get()
                if not r[1]:
                    print('problem during sign binary {}'.format(r[0]))
            self.close()
            return

    def _handle_patch_data(self,data):
        if not self._uploadFinished:
            patchpath = os.path.join(settings.PATCH_ROOT_URL, self._name)

            with open(patchpath, 'ab') as patch:
                patch.write(data)
            self.send(json.dumps({
                'msgType': 'UploadStatus',
                'message': 'progress'
            }))
        else:
            self.send(json.dumps({
                'msgType' : 'UploadStatus',
                'message' : 'Done'
            }))
    
    def _unzip_patchfile(self):
        self.send(json.dumps({
            'msgType': 'PatchStatus',
            'message': 'start unzip patch ' + self._name
        }))
        try:
            if os.path.getsize(os.path.join(settings.PATCH_ROOT_URL, self._name)) > settings.ZIP_FILE_THRESHOLD:
                utils.unzipBigPatchFile(os.path.join(settings.PATCH_ROOT_URL, self._name), settings.PATCH_ROOT_URL, self)
            else:
                shutil.unpack_archive(os.path.join(settings.PATCH_ROOT_URL, self._name), extract_dir=settings.PATCH_ROOT_URL)
        except Exception as ex:
            self.send(json.dumps({
                'msgType' : 'Error',
                'message' : 'Failed to unzip the patch {}, exit!\n {}'.format(self._name, ex)
            }))
            self.close()
            return
        self.send(json.dumps({
            'msgType' : 'PatchStatus',
            'message' : 'patch {} unzipped successfully.'.format(self._name)
        }))
