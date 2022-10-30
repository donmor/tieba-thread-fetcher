# tieba-thread-fetcher
A script that fetches threads from tieba, powered by [HibiAPI](https://github.com/mixmoe/HibiAPI).

### Usage
The script requires python 3.6+. run `pip install -r requirements.txt` to install requirements.
```
usage: tieba-thread-fetcher.py [-h] [-r REMOTE] [-w INTERVAL] [-t TRIES] [-a] [-p] [-e] [-o OUTPUT] [-s] [-j] [-q] threads [threads ...]

Fetch threads from tieba using remotely hosted HibiAPI

positional arguments:
  threads               Threads to be fetched, in the format "tid"; Use "-" to use stdin and pass threads line by line

optional arguments:
  -h, --help            show this help message and exit
  -r REMOTE, --remote REMOTE
                        Specify a remote hosting the HibiAPI daemon, "https://api.obfs.dev/api/tieba" by default
  -w INTERVAL, --wait INTERVAL
                        Wait for INTERVAL seconds in case there are anti-robot mechanisms
  -t TRIES, --tries TRIES
                        Try TRIES times before giving up (except for 404 errors)
  -a, --no-media        Do not fetch media files
  -p, --no-subposts     Do not fetch subposts
  -e, --embed-media     Embed media files into html
  -o OUTPUT, --output OUTPUT
                        Specify a directory where the fetched files go. Uses working directory if not specified
  -s, --stdout          Write to stdout
  -j, --dump-jsons      Do not print messages (except warnings or errors
  -q, --quiet           Do not print messages (except warnings or errors
```
To make it run faster you can [host HibiAPI on your local machine](https://github.com/mixmoe/HibiAPI/wiki/Deployment).
