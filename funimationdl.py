import requests, json, os, sys, downloader, m3u8parse, pycaption, io
from urllib.parse import urlencode

API_ENDPOINT = 'https://prod-api-funimationnow.dadcdigital.com/api'

def dump_log(x):
    with open('log', 'w') as f:
        f.write(json.dumps(x, indent=4))

def authenticate(username, password):
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as f:
            f.write('{}')
    with open('config.json', 'r') as f:
        config = json.load(f)
    token = login(username, password)
    if token:
        config['token'] = token
        with open('config.json', 'w') as f:
            f.write(json.dumps(config, indent=4))

def login(username, password):
    body = {'username': username, 'password': password}
    url = API_ENDPOINT + '/auth/login/'
    r = requests.post(url, data=body).json()
    if 'token' in r:
        return r['token']
    return None

def get_show(token, id):
    x = api_request({'baseUrl': API_ENDPOINT, 'url': f'/source/catalog/title/{id}', 'token': token})
    if 'status' in x:
        print(f'[ERROR] Error #{x["status"]}: {x["data"]["errors"][0]["detail"]}')
    elif 'items' not in x:
        print('[ERROR] Show not found!')
    elif len(x['items']) < 1:
        print('[ERROR] No items after search!')
    show = x['items'][0]
    print(f'[#{show["id"]}] {show["title"]} ({show["releaseYear"]})')
    qs = {'limit': '-1', 'sort': 'order', 'sort_direction': 'ASC', 'title_id': id}
    return api_request({'baseUrl': API_ENDPOINT, 'url': f'/funimation/episodes/', 'qs': qs, 'token': token})

def select_episode(show_data):
    if not show_data:
        return
    counter = 1
    for i in show_data['items']:
        e_num = i['item']['episodeNum']
        if e_num == '': e_num = i['item']['episodeId']
        print(f'{str(counter).zfill(3)}  [{e_num}] {i["item"]["episodeName"]}')
        counter += 1
    x = int(input("Enter episode index to download: "))
    epi = show_data['items'][x - 1]
    show_slug = epi['item']['titleSlug']
    epi_slug = epi['item']['episodeSlug']
    return (show_slug, epi_slug)

def get_episode(token, show_slug, epi_slug, output_folder):
    x = api_request({'baseUrl': API_ENDPOINT, 'url': f'/source/catalog/episode/{show_slug}/{epi_slug}', 'token': token})
    if not x:
        return
    x = x['items'][0]
    snum = enum = '?'
    if 'seasonNumber' in x['parent']:
        snum = x["parent"]["seasonNumber"]
    if 'number' in x:
        enum = x['number']
    ename = f'{x["parent"]["title"]} - S{snum}E{enum} - {x["title"]}'
    print(f'[INFO] {ename}')
    media = x['media']
    tracks = []
    uncut = {'Japanese': False, 'English': False}
    for m in media:
        if m['mediaType'] == 'experience':
            if 'uncut' in m['version'].lower():
                uncut[m['language']] = True
            tracks.append({'id': m['id'], 'language': m['language'], 'version': m['version'], 'type': m['experienceType'], 'subs': get_subs(m['mediaChildren'])})
    if tracks == []: return
    for i in tracks:
        print(f'{str(tracks.index(i) + 1).zfill(2)} [{i["id"]}] {i["language"]} - {i["version"]}')
    sel_id = tracks[int(input("Select which version you want to download: ")) - 1]
    sel_id['name'] = ename
    download_episode(token, sel_id, output_folder)

def download_episode(token, epi, output_folder):
    x = api_request({'baseUrl': API_ENDPOINT, 'url': f'/source/catalog/video/{epi["id"]}/signed', 'token': token, 'dinstid': 'Android Phone'})
    if not x:
        return
    if 'errors' in x:
        print(f'[ERROR] Error #{x["errors"][0]["code"]}: {x["errors"][0]["detail"]}')
        return
    vid_path = None
    for i in x["items"]:
        if i["videoType"] == 'm3u8':
            vid_path = i['src']
    if vid_path == None:
        return
    a = requests.get(vid_path)
    playlist = m3u8parse.parse_playlist(a.text)
    print('[INFO] Available qualities:')
    for i in range(len(playlist)):
        print(f'{str(i+1).zfill(2)} Resolution: {playlist[i]["res"]} [Bandwidth: {playlist[i]["bandwidth"]}KiB/s]')
    url = playlist[int(input("Select the stream to download: ")) - 1]['url']
    downloader.download(url, output_folder, epi_name=epi["name"])
    download_subs(epi['subs'], output_folder, epi["name"])

def get_subs(m):
    for i in m:
        fp = i['filePath']
        if fp.split('.')[-1] == 'dfxp': return fp
    return False

def download_subs(link, output_folder, name):
    x = requests.get(link, headers={ 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:70.0) Gecko/20100101 Firefox/70.0' })
    caption_set = pycaption.DFXPReader().read(x.text)
    results = pycaption.SRTWriter().write(caption_set)
    with io.open(os.path.join(output_folder, name + '.srt'), 'w', encoding='utf-8') as f:
        f.write(results)

def api_request(args):
    url = args['url']
    headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:70.0) Gecko/20100101 Firefox/70.0' }
    if 'baseUrl' in args:
        url = args['baseUrl'] + args['url']
    if 'qs' in args:
        url += '?' + urlencode(args['qs'])
    if 'dinstid' in args:
        headers['devicetype'] = args['dinstid']
    if 'token' in args:
        token = args['token']
        headers['Authorization'] = f'Token {token}'
    r = requests.get(url, headers=headers)
    try:
        x = r.json()
        return x
    except:
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Invalid usage: Use python {sys.argv[0]} <name/id> <path>")
        sys.exit(1)
    if sys.argv[1].isnumeric():
        show_id = int(sys.argv[1])
    else:
        r = requests.get(f'https://www.funimation.com/search/?{urlencode({"q": sys.argv[1]})}')
        show_id = int(r.text.split('data-id="')[1].split('"')[0])
    if not os.path.exists('config.json'):
        u = input("Enter Username: ")
        p = input("Enter Password: ")
        authenticate(u, p)
    with open('config.json') as f:
        cfg = json.load(f)
    show = get_show(cfg['token'], show_id)
    s, e = select_episode(show)
    get_episode(cfg['token'], s, e, sys.argv[2])