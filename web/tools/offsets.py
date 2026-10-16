# Build the data manifest: where every served file's bytes live inside the
# CD images (offsets in 2048-byte ISO space), verified byte for byte.
import mmap, json, hashlib, struct, sys, base64
import os
W = os.environ.get('ISO_DIR', 'iso') + '/'   # CD1_Allies.iso, soviet.iso (bin2iso.py) and mainx/ (MAIN.MIX unpacked)
D = os.environ.get('DATA_DIR', 'data') + '/'  # the files to describe
imgs = {'cd1': W + 'CD1_Allies.iso', 'cd2': W + 'soviet.iso'}
files = {k: open(v, 'rb') for k, v in imgs.items()}
maps = {k: mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) for k, f in files.items()}

def locate(data):
    for k, m in maps.items():
        at = m.find(data[:65536])
        while at >= 0:
            if m[at:at + len(data)] == data:
                return k, at
            at = m.find(data[:65536], at + 1)
    raise SystemExit('not found')

manifest = {}
for name in ['REDALERT.MIX', 'SCORES.MIX', 'MOVIES1.MIX', 'MOVIES2.MIX']:
    data = open(D + name, 'rb').read()
    k, at = locate(data)
    manifest[name] = {'size': len(data), 'sha1': hashlib.sha1(data).hexdigest(), 'segments': [{'src': k, 'offset': at, 'length': len(data)}]}

# The slim MAIN.MIX = our header (CRC/offset table only) + the inner files
inner_dir = W + 'mainx/'
main = open(D + 'MAIN.MIX', 'rb').read()
segs, pos = [], None
# find the body start: the first inner file in the slim file
names = ['allies.mix', 'conquer.mix', 'general.mix', 'interior.mix', 'russian.mix', 'snow.mix', 'sounds.mix', 'temperat.mix']
bodies = {n: open(inner_dir + n, 'rb').read() for n in names}
placed = sorted(((main.find(b[:65536]), n) for n, b in bodies.items()))
hdr_len = placed[0][0]
segs.append({'inline': base64.b64encode(main[:hdr_len]).decode()})
cur = hdr_len
for at, n in placed:
    assert at == cur, (n, at, cur)
    b = bodies[n]
    assert main[at:at + len(b)] == b
    k, off = locate(b)
    segs.append({'src': k, 'offset': off, 'length': len(b), 'name': n})
    cur += len(b)
tail = main[cur:]
if tail:
    segs.append({'inline': base64.b64encode(tail).decode()})
manifest['MAIN.MIX'] = {'size': len(main), 'sha1': hashlib.sha1(main).hexdigest(), 'segments': segs}
print(json.dumps(manifest, indent=1))
