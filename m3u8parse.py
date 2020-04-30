def parse_playlist(plist):
    l = plist.split('\n')
    playlist = []
    i = 0
    while i < len(l):
        if l[i].startswith('#EXT-X-STREAM-INF:'):
            url = l[i+1]
            res = l[i].rsplit('x', 1)[1] + 'p'
            bandwidth = int(l[i].split('BANDWIDTH=')[1].split(',')[0])//1024
            playlist.append({'url': url, 'res': res, 'bandwidth': bandwidth})
        i+=1
    return playlist