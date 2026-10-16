"""Red Alert game data for kampvogn.dk/redalert: local first, archive.org as fallback.

nginx serves files that exist in the data directory; requests for missing
files come here. Each file is described in the manifest as segments: inline
bytes (our own small MIX header) or byte ranges in one of the CD images on
archive.org. The file is streamed to the client while it is written to the
data directory; it is only kept if its SHA-1 matches, so the next request is
served locally by nginx.
"""

import base64
import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DATA = os.environ.get('DATA_DIR', '/data')
MANIFEST = json.load(open(os.environ.get('MANIFEST', '/manifest.json')))
SOURCES = {
    # 2048-byte sectors: offsets map directly
    'cd1': {'url': 'https://archive.org/download/cd-2-soviet/CD1_Allies.iso', 'raw': False},
    # Raw 2352-byte sectors (redump .bin, mode 1): 16-byte header, 2048 data bytes
    'cd2': {'url': 'https://archive.org/download/redump-id-9854/'
                   'Command%20%26%20Conquer%20-%20Red%20Alert%20%28USA%29%20%28Soviet%20Disc%29%20%28Rerelease%29.bin',
            'raw': True},
}
CHUNK = 8 << 20
writing = set()
lock = threading.Lock()


def fetch(url, start, end, tries=4):
    # archive.org now and then answers 5xx or cuts a response short: retry
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end - 1}',
                                                       'User-Agent': 'kampvogn-redalert-data/1'})
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status != 206:
                    raise IOError(f'expected 206 from {url}, got {r.status}')
                data = r.read()
            if len(data) != end - start:
                raise IOError(f'short read from {url}')
            return data
        except (OSError, urllib.error.URLError) as e:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)


def read_range(src, offset, length):
    """Bytes [offset, offset+length) of the image's 2048-byte data space."""
    s = SOURCES[src]
    if not s['raw']:
        return fetch(s['url'], offset, offset + length)
    first, last = offset // 2048, (offset + length - 1) // 2048
    raw = fetch(s['url'], first * 2352, (last + 1) * 2352)
    data = b''.join(raw[i + 16:i + 16 + 2048] for i in range(0, len(raw), 2352))
    skip = offset - first * 2048
    return data[skip:skip + length]


def chunks(entry):
    for seg in entry['segments']:
        if 'inline' in seg:
            yield base64.b64decode(seg['inline'])
            continue
        done = 0
        while done < seg['length']:
            n = min(CHUNK, seg['length'] - done)
            yield read_range(seg['src'], seg['offset'] + done, n)
            done += n


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.handle_request(body=False)

    def do_GET(self):
        self.handle_request(body=True)

    def handle_request(self, body):
        name = self.path.split('?')[0].rsplit('/', 1)[-1]
        entry = MANIFEST.get(name)
        if not entry:
            self.send_error(404)
            return
        path = os.path.join(DATA, name)
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(entry['size']))
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('X-Red-Alert-Data', 'local' if os.path.exists(path) else 'archive.org')
        self.end_headers()
        if not body:
            return
        if os.path.exists(path):
            with open(path, 'rb') as f:
                while block := f.read(1 << 20):
                    self.wfile.write(block)
            return
        with lock:
            write = name not in writing
            if write:
                writing.add(name)
        part = path + '.part'
        out = open(part, 'wb') if write else None
        sha = hashlib.sha1()
        try:
            for block in chunks(entry):
                sha.update(block)
                if out:
                    out.write(block)
                self.wfile.write(block)
            if out:
                out.close()
                if sha.hexdigest() == entry['sha1']:
                    os.replace(part, path)
                    self.log_message('cached %s from archive.org', name)
                else:
                    self.log_message('SHA-1 mismatch for %s, not kept', name)
        except (BrokenPipeError, ConnectionResetError):
            self.log_message('client left during %s', name)
        finally:
            if out:
                out.close()
                if os.path.exists(part):
                    os.remove(part)
                with lock:
                    writing.discard(name)


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
