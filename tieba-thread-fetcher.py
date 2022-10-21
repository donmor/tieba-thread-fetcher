#!/usr/bin/env python3

import os
import sys
import argparse
import requests
import json
import time
import base64
import mimetypes

def res2b64(src, fallback='application/octet-stream'):
    try:
        req = requests.get(src)
        if req.status_code == 200:
            mt = mimetypes.guess_type(src.split('?')[0])[0]
            if mt == None:
                mt = fallback
            print(mt, file=sys.stderr)
            return 'data:%s;base64,%s' % (mt, base64.b64encode(req.content).decode('utf-8'))
    except:
        pass
    return src

def res2local(src, fn, parent='', cat=''):
    if len(fn) == 0:
        return src
    dirname = '%s.html_files' % (fn)
    pathname = os.path.join(parent, dirname, cat)
    os.makedirs(pathname, exist_ok=True)
    filename = os.path.basename(src.split('?')[0])
    content = None
    try:
        req = requests.get(src)
        if req.status_code == 200:
            content = req.content
        else:
            print(src)
            raise Exception('Server reported %d' % (req.status_code))
    except Exception as e:
        print('\033[1;31mE: %s\033[0m' % (e), file=sys.stderr)
        return src
    try:
        with open(os.path.join(pathname, filename), 'wb') as f:
            f.write(content)
        return os.path.join(dirname, cat, filename)
    except Exception as e:
        print('\033[1;31mE: %s\033[0m' % (e), file=sys.stderr)
    return src

def get_subs(remote, thread, post, page=1):
    try:
        req = requests.get(remote + '/subpost_detail', params={'tid': thread, 'pid': post, 'page': str(page)})
        sc = req.status_code
        if sc == 200:
            return req.content
    except:
        pass
    return None

def get_json(remote, thread, page=1):
    #jsons = {}
    #i = 0
    #total = len(threads)
    #for thread in threads:
    try:
            #print('....Fetching thread %s (%d/%d)...' % (thread, i + 1, total), end='', file=sys.stderr)
        req = requests.get(remote + '/post_detail', params={'tid': thread, 'page': str(page)})
        sc = req.status_code
        if sc == 200:
                #print('\033[1;32mSUCCESS\033[0m', file=sys.stderr)
                #jsons[thread] = req.content
            return req.content
    except:
        pass
            #print('\033[1;31mFAILED\033[0m', file=sys.stderr)
    #print('%d thread%s successfully fetched.' % (len(jsons), 's' if len(jsons) > 1 else ''), file=sys.stderr)
    #return jsons
    return ''

def get_author(data, uid):
    try:
        for user in data['user_list']:
            if uid == user['id']:
                try:
                    return [user['name_show'], user['portrait']]
                except:
                    return [user['name'], user['portrait']]
    except:
        pass
    return ['', '']

def get_content_html(contents, sub=False, embed=False, nomedia=False, fn='', output=''):
    buf = '<html>'
    buf += '<head>'
    buf += '</head>'
    buf += '<body>'
    first = True
    last = ''
    #print(contents, file=sys.stderr)
    for content in contents:
        #print(content, file=sys.stderr)
        c_type = content['type']
        if not c_type in ('0', '3', '2', '4','1','5','11'):
            print('Find type %s' % (c_type), file=sys.stderr)
            print(content, file=sys.stderr)
        # if c_type in ('0', '3', '5'):
        #     if first:
        #         first = False
        #     elif not sub:
        #         buf += '<br/>'
        if (last in ('0') and c_type in ('0', '3', '5', '11') or last in ('3', '5', '11')) and not sub:
            buf += '<br/>'
        if c_type == '0':
            # Plain text
            text = content['text']
            buf += text
        elif c_type == '1':
            # Link
            text = content['text']
            link = content['link']
            buf += '<a href="%s">%s</a>' % (link, text)
        elif c_type == '2':
            # Emoticon
            text = content['text']
            alt = content['c']
            print(contents)
            src = 'https://cdn.jsdelivr.net/gh/microlong666/tieba_mobile_emotions/%s.png' % (text)
            buf += '<img class="BDE_Smiley" pic_type="1" width="30" height="30" src="%s" alt="%s"/>' % (src if nomedia else res2b64(src, 'image/png') if embed else res2local(src, fn, output, 'emoticon'), alt)
        elif c_type == '3':
            # Picture
            #print(content, file=sys.stderr)
            src = ''
            size = ['', '']
            try:
                size = content['bsize'].split(sep=',')
            except:
                pass
            try:
                src = content['origin_src']
            except:
                try:
                    src = content['cdn_src']
                except:
                    try:
                        src = content['big_cdn_src']
                    except:
                        try:
                            src = content['cdn_src_archive']
                        except:
                            pass
            buf += '<img class="BDE_Image" pic_type="0" width="%s" height="%s" src="%s"/>' % (size[0], size[1], src if nomedia else res2b64(src, 'image/jpeg') if embed else res2local(src, fn, output, 'image'))
        elif c_type == '4':
            # Username (As plain text)
            text = content['text']
            buf += text
        elif c_type == '5':
            # Video (Embedded or link)
            text = content['text']
            link = None
            src = None
            size = None
            try:
                link = content['link']
                src = content['src']
                size = [content['width'], content['height']]
            except:
                pass
            if link == None:
                buf += '<a href="%s">%s</a>' % (text, text)
            else:
                buf += '<video width="%s" height="%s" poster="%s" src="%s" controls/><br/><a href="%s">贴吧视频</a>' % (size[0], size[1], src if nomedia else res2b64(src, 'image/jpeg') if embed else res2local(src, fn, output, 'poster'), link if nomedia else res2b64(link, 'video/mp4') if embed else res2local(link, fn, output, 'video'), text)
        elif c_type == '9':
            # Number (As plain text)
            text = content['text']
            buf += text
        elif c_type == '11':
            # Big emoticon
            #print(content, file=sys.stderr)
            src = ''
            size = ['', '']
            fb = 'image/png'
            try:
                size = [content['width'], content['height']]
            except:
                pass
            try:
                src = content['dynamic']
                fb = 'image/gif'
            except:
                try:
                    src = content['static']
                except:
                    pass
            buf += '<img class="BDE_Smiley" pic_type="0" width="%s" height="%s" src="%s"/>' % (size[0], size[1], src if nomedia else res2b64(src, fb) if embed else res2local(src, fn, output, 'big_emoticon'))
        last = c_type
    buf += '</body>'
    buf += '</html>'
    return buf

def main():
    # Get args
    parser = argparse.ArgumentParser(description='Fetch threads from tieba using remotely hosted HibiAPI')
    parser.add_argument('-r, --remote', dest='remote', type=str, default='https://api.obfs.dev/api/tieba', help='Specify a remote hosting the HibiAPI daemon, "https://api.obfs.dev/api/tieba" by default')
    parser.add_argument('-a, --no-media', action='store_true', dest='nomedia', default=False, help='Do not fetch media files')
    parser.add_argument('-p, --no-subposts', action='store_true', dest='nosub', default=False, help='Do not fetch subposts')
    parser.add_argument('-e, --embed-media', action='store_true', dest='embed', default=False, help='Embed media files into html')
    parser.add_argument('-o, --output', dest='output', type=str, default='', help='Specify a directory where the fetched files go. Uses working directory if not specified')
    parser.add_argument('-s, --stdout', action='store_true', dest='sout', default=False, help='Write to stdout')
    parser.add_argument(dest='threads', type=str, nargs='+', help='Threads to be fetched, in the format "tid"')
    args = parser.parse_args()
    if sys.version_info < (3, 6):
        print('\033[33mW: Running on python(<3.6) may cause error. Consider upgrading it.\033[0m', file=sys.stderr)
    remote = args.remote
    nomedia = args.nomedia
    nosub = args.nosub
    embed = args.embed
    output = args.output
    sout = args.sout
    threads = args.threads
    online = False
    # Determine if remote daemon is to be used
    print('Connecting to remote HibiAPI daemon...', end='', file=sys.stderr)
    try:
        req = requests.get(remote)
        sc = req.status_code
        if sc == 422:
            print('\033[1;32mSUCCESS\033[0m', file=sys.stderr)
        else:
            raise AttributeError('Invalid remote daemon')
    except Exception as e:
        print('\033[1;31mFAILED\033[0m', file=sys.stderr)
        print('\033[1;31mE: %s\033[0m' % (e), file=sys.stderr)
        exit(1)
    # Parse jsons
    print('Fetching %d thread%s....' % (len(threads), 's' if len(threads) > 1 else ''), file=sys.stderr)
    #jsons = get_jsons(remote, threads)
    #print('Processing %d thread%s....' % (len(jsons), 's' if len(jsons) > 1 else ''), file=sys.stderr)
    i = 0
    #for thread, js in jsons.items():
    for thread in threads:
        #print('....Processing thread %s (%d/%d)...' % (thread, i + 1, len(jsons)), file=sys.stderr)
        print('    Processing thread %s (%d/%d)...' % (thread, i + 1, len(threads)), file=sys.stderr)
        try:
            #meta = json.loads(js[0])
            data = json.loads(get_json(remote, thread))
            if type(data) != dict:
                raise TypeError('Invalid data type, abandoned')
            # Common data
            thread_title = data['thread']['thread_info']['title']
            thread_link = 'https://tieba.baidu.com/p/%s' % thread
            #intab = ('[', '?', '*', '"', '/', '\\', '|', ':', '>', '<', ']', ' ', '%')
            intab = '[<\\\'|/"?*%>] '
            thread_fn = ''.join([c for c in thread_title if c not in intab])
            #for c in intab:
                #thread_fn = thread_fn.replace(c, '_')
            # Generate html
            buf = '<!DOCTYPE html>\n'
            buf += '<html lang="zh">\n'
            buf += '\n'
            buf += '<head>\n'
            buf += '  <title>%s</title>\n' % (thread_title)
            buf += '  <meta charset="UTF-8">\n'
            buf += '  <script>\n'
            buf += '    function toggleLzl(thread_id) {\n'
            buf += '      let x = document.getElementById(\'lzl\' + thread_id);\n'
            buf += '      if (x.style.display === \'none\') {\n'
            buf += '        x.style.display = \'block\';\n'
            buf += '      } else {\n'
            buf += '        x.style.display = \'none\';\n'
            buf += '      }\n'
            buf += '    }\n'
            buf += '  </script>\n'
            buf += '  <style>\n'
            buf += '    .lzl {\n'
            buf += '      border-style: solid;\n'
            buf += '      border-width: thin;\n'
            buf += '      border-color: #000000;\n'
            buf += '    }\n'
            buf += '    .usr {\n'
            buf += '      text-decoration: none;\n'
            buf += '      color: #000000;\n'
            buf += '    }\n'
            buf += '  </style>\n'
            buf += '</head>\n'
            buf += '\n'
            buf += '<body>\n'
            print(thread_title, file=sys.stderr)
            buf += '  <h1>%s</h1>\n' % (thread_title)
            buf += '  <div><a href="%s">%s</a></div>\n' % (thread_link, thread_link)
            buf += '  <hr />\n'
            buf += '  \n'
            is_last = False
            max_floor = 0
            cp = 1
            while not is_last:
                #data = json.loads(get_json(remote, thread, cp))
                #if type(data) != dict:
                    #raise TypeError('Invalid data type, abandoned')
                for post in data['post_list']:
                    #print(post, file=sys.stderr)
                    floor = int(post['floor'])
                    if floor <= max_floor:
                        is_last = True
                        break
                    print('Reached floor %d in page %d' % (floor, cp), file=sys.stderr)
                    max_floor = floor
                    author = get_author(data, post['author_id'])
                    th_time = 0
                    try:
                        th_time = int(post['time'])
                    except:
                        pass
                    buf += '  <div>\n'
                    buf += '    <div>\n'
                    buf += '      <div>%s #%d: <b><a href="https://tieba.baidu.com/home/main?id=%s" class="usr">%s</a></b></div>\n' % (time.strftime('%Y-%m-%d %H:%M', time.localtime(th_time)), floor, author[1], author[0])
                    buf += '      <div>%s</div>\n' % (get_content_html(post['content'], embed=embed, nomedia=nomedia, fn=thread_fn, output=output))
                    buf += '    </div>\n'
                    buf += '    \n'
                    sdt = None
                    #print('Fetching subposts...', end='', file=sys.stderr)
                    try:
                        sdt = json.loads(get_subs(remote, thread, post['id']))['subpost_list']
                    except:
                        pass
                    #print('%d found' % (len(sdt) if type(sdt) == list else 0), file=sys.stderr)
                    if type(sdt) == list and len(sdt) > 0:
                        buf += '    <button onclick="toggleLzl( %s )">收起回复</button>\n' % (post['id'])
                        buf += '    <div id="lzl%s" class="lzl">\n' % (post['id'])
                        buf += '      \n'
                        buf += '      \n'
                        cp_s = 1
                        ii = 0 
                        #while not is_last_s:
                        while len(sdt) > 0:
                            for subpost in sdt:
                                st_time = 0
                                try:
                                    st_time = int(subpost['time'])
                                except:
                                    pass
                                au_po_s = subpost['author']['portrait']
                                au_name_s = ''
                                try:
                                    au_name_s = subpost['author']['name_show']
                                except:
                                    try:
                                        au_name_s = subpost['author']['name']
                                    except:
                                        pass
                                buf += '      <div>%s <b><a href="https://tieba.baidu.com/home/main?id=%s" class="usr">%s</a></b>: %s</div>\n' % (time.strftime('%Y-%m-%d %H:%M', time.localtime(st_time)), au_po_s, au_name_s, get_content_html(subpost['content'], sub=True, embed=embed, nomedia=nomedia, fn=thread_fn, output=output))
                                buf += '      \n'
                                ii += 1
                                print('P%dS%d' % (cp_s, ii), file=sys.stderr)
                            cp_s += 1
                            sdt = json.loads(get_subs(remote, thread, post['id'], cp_s))['subpost_list']
                        buf += '    </div>\n'
                        buf += '    \n'
                    buf += '    <hr />\n'
                    buf += '  </div>\n'
                    buf += '  \n'
                cp += 1
                data = json.loads(get_json(remote, thread, cp))
                if type(data) != dict:
                    raise TypeError('Invalid data type, abandoned')
            buf += '</body>\n'
            buf += '\n'
            buf += '</html>'
            if sout:
                print(buf)
            else:
                with open(os.path.join(output, '%s.html' % (thread_fn)), 'w') as f:
                    f.write(buf)
        except Exception as e:
            print('\033[1;31mE: %s\033[0m' % (e), file=sys.stderr)
        i += 1
    print('Complete.', file=sys.stderr)
    #print(data['user_list'], file=sys.stderr)

if __name__ == "__main__":
	main()
