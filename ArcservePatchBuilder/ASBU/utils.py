import subprocess
import os
import shutil
import requests
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
from django.conf import settings
import zipfile
import errno
import channels
import channels.layers
from asgiref.sync import async_to_sync
import json
import threading

Lock_obj = threading.Lock()

def unzipBigPatchFile(zipsrc, extract_dst, consumer):
    #print('channel name in utils: ' + channel_name)
    with open(zipsrc,'rb') as src:
        zfile = zipfile.ZipFile(src)
        
        filecount = len([f for f in zfile.infolist() if not f.filename.endswith('/')])
        count = 0
        for member in zfile.infolist():
            dst = os.path.join(extract_dst, member.filename)
            #print('unzip dst : ' + dst)
            if dst.endswith('/'):
                try:
                    os.makedirs(dst)
                except (OSError, IOError) as err:
                    if err.errno != errno.EEXIST:
                        raise
                continue
            with open(dst, 'wb') as outfile, zfile.open(member) as infile:
                shutil.copyfileobj(infile, outfile)
            count +=1
            # async_to_sync(ch.send)(channel_name,{
            #     'msgType': 'UnzipStatus',
            #     'message': str(count)+'/' + str(filecount)
            # })
            if consumer:
                consumer.send(json.dumps({
                    'msgType': 'UnzipStatus',
                    'message': str(count)+'/' + str(filecount)
                }))

def getEnvVar(name):
    if name in os.environ:
        return os.environ[name]
    else:
        return None

def IsProcessRunning(proName):
    cmd = 'tasklist /FI "imagename eq {}"'.format(proName)
    output = subprocess.check_output(cmd)
    if proName in output.decode('utf-8'):
        return True
    else:
        return False

def isBinarySigned(bin):
    cmd = os.path.join(settings.PATCH_ROOT_URL,'sigcheck.exe') +' ' + bin
    ret = subprocess.run(cmd, stdout = subprocess.PIPE)

    result = ret.stdout.decode('utf-8')
    signed_output = 'Verified:\tSigned'
    if signed_output in result:
        return True
    else:
        return False

def getRealBinaryName(binname):
    #bin is like T00009527\ntagent.dll.2003.2008.2008R2
    #or  C:\Projects\ArcservePatchBuilder\ArcservePatchBuilder\ArcservePatchBuilder\T00009527\CA.ARCserve.CommunicationFoundation.Impl.dll.gdb
    #or  C:\Projects\ArcservePatchBuilder\ArcservePatchBuilder\ArcservePatchBuilder\T00009527\tree.dll
    print('binname: ', binname)
    binname = binname.split('\\')[-1]
    idx = binname.lower().find('.dll')
    if idx == -1:
        idx = binname.lower().find('.exe')
        if idx == -1:
            raise Exception('not supported binary: {}'.format(binname))
    
    return binname[0:idx+4]


def signBinary(bin):
    result = False
    patches = 'Patches'
    idx = bin.rfind('\\'+patches)
    idx_name = idx+ len(patches)+1

    binname = getRealBinaryName(bin)
    
    temp_folder = os.path.join(bin[:idx_name], bin[idx_name:].replace('\\','_'))
    print('temp_folder: ' + temp_folder)
    
    print('copy and rename binary {}.'.format(bin[idx_name:]))
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    binname_dst = os.path.join(temp_folder, binname)
    shutil.copy(bin,binname_dst)

    print('start signing file {}'.format(bin[idx_name:]))
    headers = {
        #'Host': 'rmdm-bldvm-l901:8000',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    }
    s = requests.Session()
    s.auth =HttpNtlmAuth(settings.SIGN_ACCOUNT,settings.SIGN_PASSWORD)
    try:
        r = s.get(settings.SIGN_URL,headers = headers )
        print('get status code for {} is {}'.format(bin, r.status_code))
        if r.status_code == 200:
            soup =  BeautifulSoup(r.text,'html.parser')

            vs = soup.find(id='__VIEWSTATE')['value']
            ev = soup.find(id='__EVENTVALIDATION')['value']
            with open(binname_dst,'rb') as f:
                files = {'FileUpload1': f,}
                data = {
                    '__VIEWSTATE': vs,
                    '__EVENTVALIDATION':ev,       
                    'Button1':'Upload File',
                }
                r = s.post(settings.SIGN_URL,files = files, data=data)
            print(r.status_code)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                links = soup.find_all('a',text='Download')
                print('links:{}'.format(links))
                if links and len(links) > 0:
                    link = links[0].get('href')
                    #sometimes the link is incorrect due to extra space before port number. 
                    link = link.replace(': ',':')
                    print(link)

                    with s.get(link, headers=headers, stream=True) as rd:
                        total_size = 0
                        try:
                            total_size = int(rd.headers.get('content-length'))
                            print('file total size of {}: {}'.format(bin,total_size))
                            
                        except TypeError:
                            print('content-type is not exist, ignore the progressbar.')
                            
                        count = 0  
                        chunk_size = 1024  
                        downloaded_size = 0
                        with open(binname_dst,'wb') as f:
                            for chunk in rd.iter_content(chunk_size):
                                if chunk: 
                                    f.write(chunk)
                                    if total_size != 0:
                                        if len(chunk) == chunk_size:
                                            count +=1
                                            downloaded_size = count* chunk_size
                                        else:#last chunk
                                            downloaded_size += len(chunk)
                        if total_size != 0:
                            print('{}: {} of {} downloaded... '.format(bin,downloaded_size, total_size))

                    result = True
                    #r.close()
                else:
                    print('failed to get the download link for signed binary {}.'.format(bin))
                    print(r.text)
                    #exit()
                    shutil.rmtree(temp_folder)
                    return (temp_folder, result)

                print('move signed binary back to fix path {}'.format(bin))
                shutil.move(binname_dst, bin)
                #shutil.rmtree(temp_folder)
            else:
                print('failed to post data, ret={}'.format(r.status_code))
        else:
            print('failed to get from {}, ret ={}'.format(settings.SIGN_URL, r.status_code))
    except Exception as ex:
        print('error occurred: {}'.format(ex))
    finally:
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
            
    return (binname, result)


