import subprocess
import os
import shutil
import requests
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
from django.conf import settings

apm_version_path = {
    '16.5.1' : r'APM\APMr16.5sp1\build7003',
    '17.0' : r'APM\APMr17\build7067',
    '17.5' : r'APM\APMr17.5\build7861',
    '17.5.1' : r'APM\APMr17.5SP1\build7903',
    '18.0': r'APM\APMr18\APMr18\build8001',
}

url = 'http://rmdm-bldvm-l901:8000/sign4dev.aspx'
account = 'qiang.liu@arcserve.com'
password ='godsaveme@123'

def isBinarySigned(bin):
    cmd = os.path.join(settings.PATCH_ROOT_URL,'sigcheck.exe') +' ' + bin
    ret = subprocess.run(cmd, stdout = subprocess.PIPE)

    result = ret.stdout.decode('utf-8')
    signed_output = 'Verified:\tSigned'
    if signed_output in result:
        return True
    else:
        return False

def signBinary(bin):
    result = False
    patches = 'Patches'
    idx = bin.rfind('\\'+patches)
    idx_name = idx+ len(patches)+1

    binname_ext = bin[bin.rindex('\\')+1 : ]
    names = binname_ext.split('.')
    binname = names[0] + '.' + names[1]
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
    s.auth =HttpNtlmAuth(account,password)
    try:
        r = s.get(url,headers = headers )
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
                r = s.post(url,files = files, data=data)
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
            print('failed to get from {}, ret ={}'.format(url, r.status_code))
    except Exception as ex:
        print('error occurred: {}'.format(ex))
    finally:
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
            
    return (temp_folder, result)
