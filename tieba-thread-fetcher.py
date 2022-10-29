#!/usr/bin/env python3

import os
import sys
import argparse
import requests
import json
import time
import base64
import mimetypes
from urllib import parse
from contextlib import closing

try:
	from tqdm import tqdm
except ImportError:
	print('I: Install <tqdm> to have progress bars')
	no_progress = True
	tqdm = None

TIEBA_HOME_PREFIX = 'https://tieba.baidu.com/home/main?id='
TIEBA_FORUM_PREFIX = 'https://tieba.baidu.com/f?kw='
TIME_STR = '%Y-%m-%d %H:%M'
BUF_SIZE = 4096
REQ_TIMEOUT = 15

g_quiet = False
interval = 0
tries = 1


def res2b64(src, fallback='application/octet-stream', quiet=False, size=0):
	if src[:2] == '//':
		src = 'http:' + src
	buf = b''
	for i in range(tries):
		if i > 0:
			print('\033[33mW: Retry: %d\033[0m' % i, file=sys.stderr)
		try:
			if interval > 0:
				time.sleep(interval)
			with closing(requests.get(src, stream=True)) as req:
				sc = req.status_code
				if sc == 200:
					if size == 0:
						try:
							size = int(req.headers['content_length'])
						except KeyError:
							pass
					if quiet or tqdm is None:
						for cb in req.iter_content(chunk_size=BUF_SIZE):
							if cb[:23] == b'app:tiebaclient;type:0':
								cb = cb[23:]
							buf += cb
					else:
						with tqdm(
								iterable=req.iter_content(chunk_size=BUF_SIZE),
								desc='            GET', total=size, unit='B', unit_scale=True, unit_divisor=1024
						) as progress:
							for cb in progress.iterable:
								if cb[:23] == b'app:tiebaclient;type:0':
									cb = cb[23:]
								buf += cb
								progress.update(len(cb))
					mt = mimetypes.guess_type(src.split('?')[0])[0]
					if mt is None:
						mt = fallback
					return 'data:%s;base64,%s' % (mt, base64.b64encode(buf).decode('utf-8'))
				elif sc == 404:
					print('\033[1;31mE: Server reported 404 at %s\033[0m' % src, file=sys.stderr)
					return src
				else:
					raise Exception('Server reported %d at %s' % (req.status_code, src))
		except Exception as e:
			print('\033[1;31mE: %s\033[0m' % e, file=sys.stderr)
	return src


def res2local(src, fn, parent='', cat='', overwrite=True, size=0, quiet=False):
	if src[:2] == '//':
		src = 'http:' + src
	if len(fn) == 0:
		return src
	dirname = '%s.html_files' % fn
	pathname = os.path.join(parent, dirname, cat)
	os.makedirs(pathname, exist_ok=True)
	filename = os.path.basename(src.split('?')[0])
	file = os.path.join(pathname, filename)
	if not overwrite and os.path.isfile(file):
		return parse.quote(os.path.join(dirname, cat, filename))
	for i in range(tries):
		if i > 0:
			print('\033[33mW: Retry: %d\033[0m' % i, file=sys.stderr)
		try:
			if interval > 0:
				time.sleep(interval)
			with closing(requests.get(src, stream=True, timeout=REQ_TIMEOUT)) as req:
				sc = req.status_code
				if sc == 200:
					if size == 0:
						try:
							size = int(req.headers['content_length'])
						except KeyError:
							pass
					with open(file, 'wb') as f:
						if quiet or tqdm is None:
							for cb in req.iter_content(chunk_size=BUF_SIZE):
								if cb[:23] == b'app:tiebaclient;type:0':
									cb = cb[23:]
								f.write(cb)
						else:
							with tqdm(
									iterable=req.iter_content(chunk_size=BUF_SIZE),
									desc='            GET', total=size, unit='B', unit_scale=True, unit_divisor=1024
							) as progress:
								for cb in progress.iterable:
									if cb[:23] == b'app:tiebaclient;type:0':
										cb = cb[23:]
									s = f.write(cb)
									progress.update(s)
					return parse.quote(os.path.join(dirname, cat, filename))
				elif sc == 404:
					print('\033[1;31mE: Server reported 404 at %s\033[0m' % src, file=sys.stderr)
					return parse.quote(os.path.join(dirname, cat, filename)) if os.path.isfile(file) else src
				else:
					raise Exception('Server reported %d at %s' % (req.status_code, src))
		except Exception as e:
			print('\033[1;31mE: %s\033[0m' % e, file=sys.stderr)
	return parse.quote(os.path.join(dirname, cat, filename)) if os.path.isfile(file) else src


def text2emoticon(text):
	src = ''
	# New
	if text[:14] == 'image_emoticon':
		src = 'https://tb2.bdstatic.com/tb/editor/images/client/%s.png' % (text if len(text) > 14 else text + '1')
	# face
	elif text[:3] == 'i_f' and str.isdecimal(text[3:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/face/%s.%s' % (text, 'gif' if int(text[3:]) > 50 else 'png')
	# jd
	elif text[:2] == 'j_' and str.isdecimal(text[2:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/jd/%s.png' % text
	# bearchildren
	elif text[:13] == 'bearchildren_' and str.isdecimal(text[13:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/bearchildren/%s.gif' % text
	# tiexing
	elif text[:8] == 'tiexing_' and str.isdecimal(text[8:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/tiexing/%s.gif' % text
	# ali
	elif text[:4] == 'ali_' and str.isdecimal(text[4:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/ali/%s.gif' % text
	# luoluobu
	elif text[:4] == 'llb_' and str.isdecimal(text[4:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/luoluobu/%s.gif' % text
	# qpx_n
	elif text[:1] == 'b' and str.isdecimal(text[1:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/qpx_n/%s.gif' % text
	# xyj
	elif text[:4] == 'xyj_' and str.isdecimal(text[4:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/xyj/%s.gif' % text
	# lt
	elif text[:4] == 'ltn_' and str.isdecimal(text[4:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/lt/%s.gif' % text
	# bfmn
	elif text[:5] == 'bfmn_' and str.isdecimal(text[5:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/bfmn/%s.gif' % text
	# pczxh
	elif text[:4] == 'zxh_' and str.isdecimal(text[4:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/pczxh/%s.gif' % text
	# tsj
	elif text[:2] == 't_' and str.isdecimal(text[2:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/tsj/%s.gif' % text
	# wdj
	elif text[:4] == 'wdj_' and str.isdecimal(text[4:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/wdj/%s.gif' % text
	# lxs
	elif text[:4] == 'lxs_' and str.isdecimal(text[4:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/lxs/%s.gif' % text
	# baodong
	elif text[:2] == 'b_' and str.isdecimal(text[2:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/baodong/%s.gif' % text
	# baodong_d
	elif text[:3] == 'bd_' and str.isdecimal(text[3:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/baodong_d/%s.gif' % text
	# bobo
	elif text[:2] == 'B_' and str.isdecimal(text[2:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/bobo/%s.gif' % text
	# shadow
	elif text[:3] == 'yz_' and str.isdecimal(text[3:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/shadow/%s.gif' % text
	# ldw
	elif text[:2] == 'w_' and str.isdecimal(text[2:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/ldw/%s.gif' % text
	# 10th
	elif text[:5] == '10th_' and str.isdecimal(text[5:]):
		src = 'https://tb2.bdstatic.com/tb/editor/images/10th/%s.gif' % text
	return src


def get_subs(remote, thread, post, page=1):
	for i in range(tries):
		if i > 0:
			print('\033[33mW: Retry: %d\033[0m' % i, file=sys.stderr)
		try:
			if interval > 0:
				time.sleep(interval)
			req = requests.get(remote + '/subpost_detail', params={'tid': thread, 'pid': post, 'page': str(page)})
			sc = req.status_code
			if sc == 200:
				return req.content
			elif sc == 404:
				break
		except requests.RequestException:
			pass
	return None


def get_json(remote, thread, page=1):
	for i in range(tries):
		if i > 0:
			print('\033[33mW: Retry: %d\033[0m' % i, file=sys.stderr)
		try:
			if interval > 0:
				time.sleep(interval)
			req = requests.get(remote + '/post_detail', params={'tid': thread, 'page': str(page)})
			sc = req.status_code
			if sc == 200:
				return req.content
			elif sc == 404:
				break
		except requests.RequestException:
			pass
	return ''


def get_author(remote, data, uid):
	try:
		for user in data['user_list']:
			if uid == user['id']:
				try:
					return [user['name_show'], user['portrait']]
				except KeyError:
					return [user['name'], user['portrait']]
	except KeyError:
		pass
	try:
		if interval > 0:
			time.sleep(interval)
		req = requests.get(remote + '/user_profile', params={'uid': uid})
		sc = req.status_code
		if sc == 200:
			d0 = json.loads(req.content)
			user = d0['user']
			try:
				return [user['name_show'], user['portrait']]
			except KeyError:
				return [user['name'], user['portrait']]
	except (KeyError, requests.RequestException):
		pass
	return None


def get_content_html(remote, data, contents, sub=False, embed=False, nomedia=False, fn='', output=''):
	html_buf = '<html>'
	html_buf += '<head>'
	html_buf += '</head>'
	html_buf += '<body>'
	last = -1
	i = 0
	for content in contents:
		i += 1
		if not g_quiet:
			print('          * Retrieving content blocks (%d/%d)... ' % (i, len(contents)), end='', file=sys.stderr)
		if type(content) != dict:
			if not g_quiet:
				print('NONE', file=sys.stderr)
			continue
		c_type = int(content['type'])
		if (last == 0 and c_type == 0 or last in (3, 5, 11) or last != -1 and c_type in (3, 5, 11)) and not sub:
			html_buf += '<br/>'
		if c_type == 0:
			# Plain text
			if not g_quiet:
				print('\033[36mTEXT\033[0m detected' % content, file=sys.stderr)
			text = str.replace(content['text'], '\n', '<br/>', -1)
			html_buf += text
		elif c_type == 1:
			# Link
			if not g_quiet:
				print('\033[36mLINK\033[0m detected' % content, file=sys.stderr)
			text = content['text']
			link = content['link']
			html_buf += '<a href="%s">%s</a>' % (link, text)
		elif c_type == 2:
			# Emoticon
			if not g_quiet:
				print('\033[36mEMOTICON\033[0m detected' % content, file=sys.stderr)
			text = content['text']
			alt = content['c']
			src = text2emoticon(text)
			if len(src) > 0:
				html_buf += '<img class="BDE_Smiley" pic_type="1" width="30" height="30" src="%s" alt="%s"/>' % (
					src if nomedia else res2b64(src, fallback='image/png', quiet=True) if embed else res2local(
						src, fn, parent=output, cat='emoticon', overwrite=False, quiet=True), alt)
		elif c_type == 3:
			# Image
			if not g_quiet:
				print('\033[36mIMAGE\033[0m detected' % content, file=sys.stderr)
			src = ''
			size = ['', '']
			length = 0
			try:
				size = content['bsize'].split(sep=',')
			except KeyError:
				pass
			try:
				src = content['origin_src']
			except KeyError:
				try:
					src = content['cdn_src']
					src = src[38 if src[5] == 's' else 37:].split('&')[0]
				except KeyError:
					try:
						src = content['cdn_src_active']
						src = src[39 if src[5] == 's' else 38:].split('&')[0]
					except KeyError:
						try:
							src = content['big_cdn_src']
							src = src[39 if src[5] == 's' else 38:].split('&')[0]
						except KeyError:
							pass
			try:
				length = int(content['size'])
			except (KeyError, ValueError):
				try:
					length = int(content['origin_size'])
				except (KeyError, ValueError):
					pass
			html_buf += '<img class="BDE_Image" pic_type="0" width="%s" height="%s" src="%s"/>' % (
				size[0], size[1],
				src if nomedia else res2b64(src, fallback='image/jpeg', size=length) if embed else res2local(
					src, fn, parent=output, cat='image', size=length))
		elif c_type == 4:
			# Username (As link)
			if not g_quiet:
				print('\033[36mUSERNAME\033[0m detected' % content, file=sys.stderr)
			text = content['text']
			uid = content['uid']
			try:
				author = get_author(remote, data, uid)
				r = '<a href="%s%s" class="usr">%s</a>' % (
					TIEBA_HOME_PREFIX, author[1], author[0]) if author is not None else text
			except KeyError:
				r = text
			html_buf += r
		elif c_type == 5:
			# Video (Embedded or link)
			if not g_quiet:
				print('\033[36mVIDEO\033[0m detected' % content, file=sys.stderr)
			text = content['text']
			link = None
			src = None
			size = None
			length = 0
			try:
				link = content['link']
				src = content['src']
				size = [content['width'], content['height']]
			except KeyError:
				pass
			try:
				length = int(content['size'])
			except (KeyError, ValueError):
				try:
					length = int(content['origin_size'])
				except (KeyError, ValueError):
					pass
			if link is None:
				html_buf += '<a href="%s">%s</a>' % (text, text)
			else:
				html_buf += '<video width="%s" height="%s" poster="%s" src="%s" controls/><br/><a href="%s">贴吧视频</a>' % (
					size[0], size[1],
					src if nomedia else res2b64(src, fallback='image/jpeg', size=length) if embed else res2local(
						src, fn, parent=output, cat='poster', size=length),
					link if nomedia else res2b64(link, fallback='video/mp4', size=length) if embed else res2local(
						link, fn, parent=output, cat='video', size=length),
					text)
		elif c_type == 7:
			# Line break
			if not g_quiet:
				print('\033[36mLINEBREAK\033[0m detected' % content, file=sys.stderr)
			text = '<br/>'
			html_buf += text
		elif c_type == 9:
			# Number (As plain text)
			if not g_quiet:
				print('\033[36mNUMBER\033[0m detected' % content, file=sys.stderr)
			text = content['text']
			html_buf += text
		elif c_type == 11:
			# Big emoticon
			if not g_quiet:
				print('\033[36mBIG EMOTICON\033[0m detected' % content, file=sys.stderr)
			src = ''
			size = ['', '']
			fb = 'image/png'
			try:
				size = [content['width'], content['height']]
			except KeyError:
				pass
			try:
				src = content['dynamic']
				fb = 'image/gif'
			except KeyError:
				try:
					src = content['static']
				except KeyError:
					pass
			html_buf += '<img class="BDE_Smiley" pic_type="0" width="%s" height="%s" src="%s"/>' % (
				size[0], size[1],
				src if nomedia else res2b64(src, fallback=fb, quiet=True) if embed else res2local(
					src, fn, parent=output, cat='big_emoticon', overwrite=False, quiet=True))
		elif c_type == 16:
			# Graffiti
			if not g_quiet:
				print('\033[36mGRAFFITI\033[0m detected' % content, file=sys.stderr)
			src = ''
			size = ['', '']
			length = 0
			try:
				size = content['bsize'].split(sep=',')
			except KeyError:
				pass
			try:
				src = content['graffiti_info']['url']
			except KeyError:
				try:
					src = content['cdn_src']
					src = src[38 if src[5] == 's' else 37:].split('&')[0]
				except KeyError:
					try:
						src = content['cdn_src_active']
						src = src[39 if src[5] == 's' else 38:].split('&')[0]
					except KeyError:
						try:
							src = content['big_cdn_src']
							src = src[39 if src[5] == 's' else 38:].split('&')[0]
						except KeyError:
							pass
			try:
				length = int(content['size'])
			except (KeyError, ValueError):
				try:
					length = int(content['origin_size'])
				except (KeyError, ValueError):
					pass
			html_buf += '<img class="BDE_Image" pic_type="0" width="%s" height="%s" src="%s"/>' % (
				size[0], size[1],
				src if nomedia else res2b64(src, fallback='image/jpeg', size=length) if embed else res2local(
					src, fn, parent=output, cat='image', size=length))
		elif c_type == 18:
			# Topic (As link)
			if not g_quiet:
				print('\033[36mTOPIC\033[0m detected' % content, file=sys.stderr)
			text = content['text']
			link = content['link']
			html_buf += '<a href="%s">%s</a>' % (link, text)
		elif c_type == 20:
			# Emoticon graph (Yet another)
			if not g_quiet:
				print('\033[36mEMOTICON GRAPH\033[0m detected' % content, file=sys.stderr)
			src = ''
			size = ['', '']
			fb = 'image/png'
			try:
				size = [content['width'], content['height']]
			except KeyError:
				pass
			try:
				src = content['src']
				fb = 'image/jpeg'
			except KeyError:
				pass
			html_buf += '<img class="BDE_Smiley" pic_type="0" width="%s" height="%s" src="%s"/>' % (
				size[0], size[1],
				src if nomedia else res2b64(src, fallback=fb, quiet=True) if embed else res2local(
					src, fn, parent=output, cat='big_emoticon', overwrite=False, quiet=True))
		else:
			# Not implemented
			if not g_quiet:
				print('\033[33mFAILED\033[0m' % content, file=sys.stderr)
			print('\033[33mW: Unimplemented content block: %s\033[0m' % content, file=sys.stderr)
			html_buf += '<span style="border: 1px solid red">%s</span>' % content
			pass
		last = c_type
	html_buf += '</body>'
	html_buf += '</html>'
	return html_buf


def main():
	# Get args
	parser = argparse.ArgumentParser(description='Fetch threads from tieba using remotely hosted HibiAPI')
	parser.add_argument(
		'-r', '--remote', dest='remote', type=str, default='https://api.obfs.dev/api/tieba',
		help='Specify a remote hosting the HibiAPI daemon, "https://api.obfs.dev/api/tieba" by default')
	parser.add_argument(
		'-w', '--wait', dest='interval', type=int, default=0,
		help='Wait for INTERVAL seconds in case there are anti-robot mechanisms')
	parser.add_argument(
		'-t', '--tries', dest='tries', type=int, default=1,
		help='Try TRIES times before giving up (except for 404 errors)')
	parser.add_argument(
		'-a', '--no-media', action='store_true', dest='no_media', default=False,
		help='Do not fetch media files')
	parser.add_argument(
		'-p', '--no-subposts', action='store_true', dest='no_sub', default=False,
		help='Do not fetch subposts')
	parser.add_argument(
		'-e', '--embed-media', action='store_true', dest='embed', default=False,
		help='Embed media files into html')
	parser.add_argument(
		'-o', '--output', dest='output', type=str, default='',
		help='Specify a directory where the fetched files go. Uses working directory if not specified')
	parser.add_argument(
		'-s', '--stdout', action='store_true', dest='s_out', default=False,
		help='Write to stdout')
	parser.add_argument(
		'-q', '--quiet', action='store_true', dest='g_quiet', default=False,
		help='Do not print messages (except warnings or errors')
	parser.add_argument(
		dest='threads', type=str, nargs='+',
		help='Threads to be fetched, in the format "tid"; Use "-" to use stdin and pass threads line by line')
	args = parser.parse_args()
	if sys.version_info < (3, 6):
		print('\033[33mW: Running on python(<3.6) may cause error. Consider upgrading\033[0m', file=sys.stderr)
	global g_quiet
	global tries
	global interval
	interval = args.interval
	tries = args.tries
	if tries < 1:
		tries = sys.maxsize
	remote = args.remote
	no_media = args.no_media
	no_sub = args.no_sub
	embed = args.embed
	output = args.output
	s_out = args.s_out
	g_quiet = args.g_quiet
	threads = args.threads
	s_in = '-' in threads
	if not g_quiet:
		print('Connecting to remote HibiAPI daemon... ', end='', file=sys.stderr)
	for i in range(tries):
		if i > 0:
			if g_quiet:
				print('\033[33mW: Retry: %d\033[0m' % i, file=sys.stderr)
			else:
				print('\033[33mW: Retry: %d\033[0m ... ' % i, end='', file=sys.stderr)
		try:
			if interval > 0:
				time.sleep(interval)
			req = requests.get(remote)
			sc = req.status_code
			if sc == 422:
				if not g_quiet:
					print('\033[1;32mSUCCESS\033[0m', file=sys.stderr)
				break
			else:
				if sc == 404:
					if not g_quiet:
						print('\033[1;31mFAILED\033[0m', file=sys.stderr)
					print('\033[1;31mE: Server reported 404 at %s\033[0m' % remote, file=sys.stderr)
					exit(1)
				raise AttributeError('Invalid remote daemon')
		except Exception as e:
			if not g_quiet:
				print('\033[1;31mFAILED\033[0m', file=sys.stderr)
			print('\033[1;31mE: %s\033[0m' % e, file=sys.stderr)
			if i == tries - 1:
				exit(1)
	# Parse jsons
	if s_in:
		if not g_quiet:
			print('Accepting threads...', file=sys.stderr)
	else:
		if not g_quiet:
			print('Fetching %d thread%s....' % (len(threads), 's' if len(threads) > 1 else ''), file=sys.stderr)
	i = 0
	for thread in (sys.stdin if s_in else threads):
		thread = thread.rstrip()
		if not thread.isdecimal():
			print('\033[1;31mE: Illegal thread %s\033[0m' % thread, file=sys.stderr)
			continue
		if s_in:
			if thread == '':
				break
			if not g_quiet:
				print('  * Processing thread %s (%d)...' % (thread, i + 1), file=sys.stderr)
		else:
			if not g_quiet:
				print('  * Processing thread %s (%d/%d)...' % (thread, i + 1, len(threads)), file=sys.stderr)
		try:
			data = json.loads(get_json(remote, thread))
			if type(data) != dict:
				raise TypeError('Invalid data type, abandoned')
			# Common data
			try:
				thread_title = data['thread']['thread_info']['title']
			except KeyError:
				raise Exception('Thread not accessible, abandoned')
			thread_link = 'https://tieba.baidu.com/p/%s' % thread
			ich = '[<\\\'|/"?*%>] '
			thread_fn = ''.join([c for c in thread_title if c not in ich])
			forum = None
			try:
				forum = data['forum']['name']
			except KeyError:
				pass
			if not g_quiet:
				print('    Title is "%s"' % thread_title, file=sys.stderr)
			# Generate html
			buf = '<!DOCTYPE html>\n'
			buf += '<html lang="zh">\n'
			buf += '\n'
			buf += '<head>\n'
			buf += '  <title>%s</title>\n' % thread_title
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
			buf += '  <h1>%s</h1>\n' % thread_title
			if forum is not None:
				buf += '  <div><a href="%s%s">%s吧</a> - <a href="%s">%s</a></div>\n' % (
					TIEBA_FORUM_PREFIX, forum, forum, thread_link, thread_link)
			else:
				buf += '  <div><a href="%s">%s</a></div>\n' % (thread_link, thread_link)
			buf += '  <hr />\n'
			buf += '  \n'
			is_last = False
			max_floor = 0
			cp = 1
			while not is_last:
				pl = data['post_list']
				if len(pl) == 0:
					break
				for post in pl:
					floor = int(post['floor'])
					if floor <= max_floor:
						is_last = True
						break
					if not g_quiet:
						print('      - Reached floor %d in page %d' % (floor, cp), file=sys.stderr)
					max_floor = floor
					author = None
					an = '贴吧用户'
					try:
						an = post['author_id']
						author = get_author(remote, data, an)
					except KeyError:
						pass
					th_time = 0
					try:
						th_time = int(post['time'])
					except KeyError:
						pass
					buf += '  <div>\n'
					buf += '    <div>\n'
					buf += '      <div>%s #%d: <b>%s</b></div>\n' % (
						time.strftime(TIME_STR, time.localtime(th_time)),
						floor, '<a href="%s%s" class="usr">%s</a>' % (
							TIEBA_HOME_PREFIX, author[1], author[0]) if author is not None else an)
					buf += '      <div>%s</div>\n' % (
						get_content_html(remote, data, post['content'], embed=embed, nomedia=no_media, fn=thread_fn,
										 output=output))
					buf += '    </div>\n'
					buf += '    \n'
					sdt = None
					if not no_sub:
						try:
							sdt = json.loads(get_subs(remote, thread, post['id']))['subpost_list']
						except (ValueError, KeyError):
							pass
					if type(sdt) == list and len(sdt) > 0:
						if not g_quiet:
							print('        Subposts detected in floor %d' % floor, file=sys.stderr)
						buf += '    <button onclick="toggleLzl( %s )">收起回复</button>\n' % (post['id'])
						buf += '    <div id="lzl%s" class="lzl">\n' % (post['id'])
						buf += '      \n'
						buf += '      \n'
						cp_s = 1
						ii = 0
						while len(sdt) > 0:
							for subpost in sdt:
								st_time = 0
								try:
									st_time = int(subpost['time'])
								except KeyError:
									pass
								au_po_s = subpost['author']['portrait']
								au_name_s = ''
								try:
									au_name_s = subpost['author']['name_show']
								except KeyError:
									try:
										au_name_s = subpost['author']['name']
									except KeyError:
										pass
								buf += '      <div>%s <b><a href="%s%s" class="usr">%s</a></b>: %s</div>\n' % (
									time.strftime(TIME_STR, time.localtime(st_time)), TIEBA_HOME_PREFIX, au_po_s,
									au_name_s, get_content_html(
										remote, data, subpost['content'], sub=True, embed=embed,
										nomedia=no_media, fn=thread_fn, output=output))
								buf += '      \n'
								ii += 1
							cp_s += 1
							try:
								sdt = json.loads(get_subs(remote, thread, post['id'], cp_s))['subpost_list']
							except (ValueError, KeyError):
								pass
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
			if s_out:
				print(buf)
			else:
				with open(os.path.join(output, '%s.html' % thread_fn), 'w') as f:
					f.write(buf)
					sys.stdout.flush()
			if not g_quiet:
				print('    Thread %s successfully fetched' % thread, file=sys.stderr)
		except Exception as e:
			print('\033[1;31mE: %s\033[0m' % e, file=sys.stderr)
		i += 1
	if not g_quiet:
		print('Complete.', file=sys.stderr)


if __name__ == "__main__":
	main()
