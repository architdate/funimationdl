import os
import re
import requests
import sys
import subprocess
from Crypto.Cipher import AES

def decrypt(data, key, iv):
    """Decrypt using AES CBC"""
    decryptor = AES.new(key, AES.MODE_CBC, iv=iv)
    return decryptor.decrypt(data)

def get_binary(url):
    """Get binary data from URL"""
    a = requests.get(url, stream=True)
    return a.content

def download_legacy(url, output_folder, epi_name='output', skip_ad=True):
    """Main"""
    base = url.rsplit('/', 1)[0]
    a = requests.get(url)
    data = a.text
    # make output folder
    os.makedirs(output_folder, exist_ok=True)
    # download and decrypt chunks
    parts = []
    for part_id, sub_data in enumerate(data.split('#UPLYNK-SEGMENT:')):
        # skip ad
        if skip_ad:
            if re.findall('#UPLYNK-SEGMENT:.*,.*,ad', '#UPLYNK-SEGMENT:' + sub_data):
                continue
        # get key, iv and data
        chunks = re.findall('#EXT-X-KEY:METHOD=AES-128,URI="(.*)",IV=(.*)\s.*\s(.*)', sub_data)
        for chunk in chunks:
            key_url = chunk[0]
            iv_val = chunk[1][2:]
            data_url = chunk[2]
            file_name = os.path.basename(data_url).split('?')[0]
            print('Processing "%s"' % file_name)
            # download key and data
            key = get_binary(base + '/' + key_url)
            enc_data = get_binary(base + '/' + data_url)
            iv = bytearray.fromhex(iv_val)
            # save decrypted data to file
            out_file = os.path.join(output_folder, '%s' % file_name)
            with open(out_file, 'wb') as f:
                dec_data = decrypt(enc_data, key, iv)
                f.write(dec_data)
                parts.append(out_file)
    if os.path.exists(os.path.join(output_folder, epi_name + 'ts')):
        os.remove(os.path.join(output_folder, epi_name + 'ts'))
    with open(os.path.join(output_folder, epi_name + 'ts'), 'ab') as f:
        for i in parts:
            with open(i, 'rb') as f2:
                f.write(f2.read())
    for i in parts:
        os.remove(i)

def download(url, output_folder, epi_name='output', skip_ad=True):
    cmd = ['streamlink', '--force', url, 'live', '-o', os.path.join(output_folder, epi_name+'.ts')]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = p.communicate()
    print(out.decode('utf-8'))