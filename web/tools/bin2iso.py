# Raw CD image (2352-byte sectors, mode 1 or mode 2 form 1) -> 2048-byte ISO
import sys
src, dst = sys.argv[1], sys.argv[2]
with open(src, 'rb') as f, open(dst, 'wb') as o:
    n = 0
    while True:
        s = f.read(2352)
        if len(s) < 2352:
            break
        mode = s[15]
        o.write(s[16:16 + 2048] if mode == 1 else s[24:24 + 2048])
        n += 1
print(n, 'sectors')
