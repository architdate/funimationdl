# funimationdl

A simple python script to download shows from funimation (.ts format) along with srt subtitles

## Pre Requisites
All the necessary libraries can be installed using the following command
```
$ pip install -r requirements.txt
```

## Usage:

```bash
$ python funimationdl.py <show id/show name> <output path>
```
On first usage, you will have to provide your funimation credentials. You will not have to keep providing these credentials again and again unless you delete the `config.json` file

Please be patient with the download. This is not yet multiprocessed.

## TODO:
- [ ] proxy support
- [ ] automatic mkv conversion using ffmpeg
- [ ] automatic sub muxing
- [ ] future integration with crunchydl for automated duals
