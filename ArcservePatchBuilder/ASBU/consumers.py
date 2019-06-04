from channels.generic.websocket import WebsocketConsumer
import json
from django.conf import settings
import os
import shutil
from . import utils
import subprocess
import time
import threading

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
                    self._create_patch(self._name)
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
            
            #print(files)
            if any(f.lower().endswith(fixname.lower() + '.txt') for f in files):
                print('{} exists, good to go. '.format(fixname+ '.txt'))
            else:
                print('{} is not included, invalid patch zip.'.format(fixname + '.txt'))
                self.send(json.dumps({
                    'msgType': 'Error',
                    'message': '{} is not included, invalid patch zip.'.format(fixname + '.txt')
                }))
                self.close()
                return
            
            pool = ThreadPool(processes=len(files))
            for f in files:
                if not f.lower().endswith('.txt') and not utils.isBinarySigned(f):
                    print('trying to sign file ' + f)
                    ar = pool.apply_async(utils.signBinary, (f,))
                    results.append(ar)
            
            pool.close()
            pool.join()
            self.send(json.dumps({
                'msgType': 'PatchStatus',
                'message': 'start signing the binaries...'
            }))
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

            cazname = fixname + '.caz'
            cazpath = os.path.join(settings.PATCH_ROOT_URL, cazname)
            cazipxp = os.path.join(settings.PATCH_ROOT_URL, 'cazipxp.exe')

            self.send(json.dumps({
                'msgType': 'PatchStatus',
                'message': 'all binaries get signed successfully...'
            }))
            print('start to create {} file...'.format(cazname))
            self.send(json.dumps({
                'msgType': 'PatchStatus',
                'message': 'start creating {} file...'.format(cazname)
            }))
            curdir = os.getcwd()
            print('current dir {}'.format(curdir))
            os.chdir(settings.PATCH_ROOT_URL)
            cmd = '{} -w {}'.format(cazipxp, ' '.join(filter(lambda x : not x.lower().endswith(fixname.lower() + '.exe'),files)) + ' '  + cazname)
            print(cmd)
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as ex:
                print('Error create .caz file, exit.')
                self.send(json.dumps({
                'msgType': 'Error',
                'message': 'Error creating .caz file... {}'.format(ex)
                }))
                self.close()
                return

            if os.path.isfile(cazpath):
                print('caz created successfully...')
                self.send(json.dumps({
                'msgType': 'PatchStatus',
                'message': '{} created successfully.'.format(cazname)
                }))
            else:
                print('failed to create caz file, exit.')
                self.send(json.dumps({
                'msgType': 'Error',
                'message': 'Failed in creating {}...'.format(cazname)
                }))
                self.close()
                return

            apm = os.path.join(settings.PATCH_ROOT_URL, settings.APM_VERSION_PATH[self._version])
            print('copy {} to apm folder {}'.format(cazname, apm))
            shutil.move(cazpath, os.path.join(apm, cazname))

            if os.path.exists(os.path.join(apm,fixname)):    
                #shutil.rmtree(os.path.join(apm, fixname), onerror=remove_readonly)
                subprocess.run('cmd /c rd /S /Q ' + os.path.join(apm,fixname))

            createpatch = os.path.join(apm, 'CreatePatch.exe')
            print('start creating {}.exe'.format(fixname))

            #below code is added to notify GUI.
            lck = utils.Lock_obj.locked()
            if lck:
                self.send(json.dumps({
                    'msgType': 'PatchStatus',
                    'message': 'Another patch is creating, pending...',
                    }))
            while lck:
                self.send(json.dumps({
                    'msgType': 'PatchStatus',
                    'message': 'Pending',
                    }))
                time.sleep(5)
                lck = utils.Lock_obj.locked()
            with utils.Lock_obj:
                ca_apm = utils.getEnvVar(settings.PATCH_CA_APM)
                if  ca_apm and  ca_apm.lower() != apm.lower():
                    #needed by createpatch.exe, which need CA_APM be set in system vairable, this will require administrator previlege.
                    subprocess.run('setx CA_APM {} /M'.format(apm))

                cmd = '{} -p {} {}'.format(createpatch, os.path.join(apm,cazname), fixname)
                print(cmd)
                self.send(json.dumps({
                    'msgType': 'PatchStatus',
                    'message': 'Start running command: {}.'.format(cmd)
                    }))
                ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stderr = ret.stderr.decode('utf-8')
            stdout = ret.stdout.decode('utf-8')
            if len(stderr)> 0 or 'Failed' in stdout:
                self.send(json.dumps({
                    'msgType': 'Error',
                    'message': stdout + '#####' + stderr
                    }))
            exepath = os.path.join(apm,fixname+'\\MQA\\Build.000\\'+fixname+'.exe')
            if os.path.isfile(exepath):
                print('.exe file created successfully.')
                self.send(json.dumps({
                'msgType': 'PatchStatus',
                'message': '{} created successfully.'.format(fixname+'.exe')
                }))
                patch = os.path.join(fixpath, fixname+'.exe')
                shutil.copy(exepath, patch)
                self.send(json.dumps({
                'msgType': 'PatchStatus',
                'message': 'Start signing {}...'.format(fixname+'.exe')
                }))
                rst = utils.signBinary(patch)
                if rst[1]:
                    print('all good....')
                    self.send(json.dumps({
                        'msgType': 'PatchStatus',
                        'message': '{} signed successfully.'.format(rst[0])
                    }))
                    self.send(json.dumps({
                        'msgType': 'PatchSuccess',
                        'message': os.path.basename(rst[0])
                    }))
                else:
                    self.send(json.dumps({
                        'msgType': 'Error',
                        'message': 'Errror when sign {}.'.format(rst[0])
                        }))
                    self.close()
                    return
            else:
                print('failed to create the exe file, exit.')
                self.send(json.dumps({
                        'msgType': 'Error',
                        'message': 'Failed to create {}.'.format(fixname+ '.exe')
                        }))
                self.close()
                return
        else:
            for ar in results:
                r = ar.get()
                if not r[1]:
                    print('problem during sign binary {}'.format(r[0]))
                    self.send(json.dumps({
                    'msgType': 'Error',
                    'message': 'Error occurred when sign binary {}'.format(r[0])
                }))
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
            tmp = self._name[0:-4]
            tmppath = os.path.join(settings.PATCH_ROOT_URL, tmp)
            if os.path.exists(tmppath):
                subprocess.run('cmd /c rd /S /Q ' + tmppath)
            os.makedirs(tmppath, exist_ok=True)

            if self._name.endswith('.zip'):
                if os.path.getsize(os.path.join(settings.PATCH_ROOT_URL, self._name)) > settings.ZIP_FILE_THRESHOLD:
                    utils.unzipBigPatchFile(os.path.join(settings.PATCH_ROOT_URL, self._name), tmppath, self)
                else:
                    shutil.unpack_archive(os.path.join(settings.PATCH_ROOT_URL, self._name), extract_dir=tmppath)
            elif self._name.endswith('.caz'):
                curdir = os.getcwd()
                os.chdir(tmppath)
                cazpath = os.path.join(settings.PATCH_ROOT_URL, 'cazipxp.exe')
                patchpath = os.path.join(settings.PATCH_ROOT_URL, self._name)
                cmd = '{} -u {}'.format(cazpath, patchpath)
                subprocess.run(cmd)
                os.chdir(curdir)
        except Exception as ex:
            self.send(json.dumps({
                'msgType' : 'Error',
                'message' : 'Failed to unzip the patch {}, please refresh and try again later!\n {}'.format(self._name, ex)
            }))
            self.close()
            return
        self.send(json.dumps({
            'msgType' : 'PatchStatus',
            'message' : 'patch {} unzipped successfully.'.format(self._name)
        }))

    