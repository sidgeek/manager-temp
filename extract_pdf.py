# -*- coding: utf-8 -*-
"""Minimal PDF text extractor with ToUnicode CMap support (no third-party deps)."""
import re, zlib, sys, os, glob

def load(path):
    data = open(path, 'rb').read()
    objs = {}
    for m in re.finditer(rb'(?<![0-9])(\d+)\s+(\d+)\s+obj\b', data):
        num = int(m.group(1))
        start = m.end()
        end = data.find(b'endobj', start)
        if end < 0:
            continue
        body = data[start:end]
        sm = re.search(rb'stream\r?\n', body)
        if sm:
            raw = body[sm.end():]
            raw = raw[:raw.rfind(b'endstream')]
            head = body[:sm.start()]
            if b'FlateDecode' in head:
                try:
                    raw = zlib.decompress(raw)
                except Exception:
                    try:
                        raw = zlib.decompressobj().decompress(raw)
                    except Exception:
                        pass
            objs[num] = {'head': head, 'stream': raw}
        else:
            objs[num] = {'head': body, 'stream': None}
    # expand object streams
    for num in list(objs.keys()):
        o = objs[num]
        if not re.search(rb'/Type\s*/ObjStm', o['head']) or not o['stream']:
            continue
        fm = re.search(rb'/First\s+(\d+)', o['head'])
        nm = re.search(rb'/N\s+(\d+)', o['head'])
        if not fm or not nm:
            continue
        first, n = int(fm.group(1)), int(nm.group(1))
        s = o['stream']
        hdr = s[:first].split()
        for i in range(n):
            if 2 * i + 1 >= len(hdr):
                break
            onum = int(hdr[2 * i]); off = int(hdr[2 * i + 1])
            body = s[first + off:]
            nxt = None
            for j in range(i + 1, n):
                if 2 * j + 1 < len(hdr):
                    nxt = first + int(hdr[2 * j + 1])
                    break
            if nxt:
                body = s[first + off:nxt]
            # trim trailing endstream/endobj
            body = body.strip()
            if body.endswith(b'endobj'):
                body = body[:-6]
            objs.setdefault(onum, {'head': body, 'stream': None})
    return data, objs

def get_ref(body, key):
    m = re.search(key + rb'\s+(\d+)\s+\d+\s+R', body)
    return int(m.group(1)) if m else None

def page_order(objs):
    pages = []
    catalog = None
    for n, o in objs.items():
        if b'/Type' in o['head'] and re.search(rb'/Type\s*/Catalog', o['head']):
            catalog = n
            break
    if catalog is None:
        for n, o in objs.items():
            if re.search(rb'/Type\s*/Page[^s]', o['head']):
                pages.append(n)
        return sorted(pages)
    root = get_ref(objs[catalog]['head'], rb'/Pages')
    stack = [root]
    seen = set()
    while stack:
        n = stack.pop(0)
        if n is None or n in seen or n not in objs:
            continue
        seen.add(n)
        head = objs[n]['head']
        if re.search(rb'/Type\s*/Pages', head):
            km = re.search(rb'/Kids\s*\[(.*?)\]', head, re.S)
            if km:
                for x in re.finditer(rb'(\d+)\s+\d+\s+R', km.group(1)):
                    stack.append(int(x.group(1)))
        elif re.search(rb'/Type\s*/Page[^s]', head):
            pages.append(n)
    pages.sort(key=lambda p: p)
    # try to keep original order by Kids sequence
    return pages

def parse_cmap(stream):
    cmap = {}
    for m in re.finditer(rb'beginbfchar(.*?)endbfchar', stream, re.S):
        for mm in re.finditer(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', m.group(1)):
            src = int(mm.group(1), 16)
            dst = bytes.fromhex(mm.group(2).decode())
            cmap[src] = dst.decode('utf-16-be', 'ignore')
    for m in re.finditer(rb'beginbfrange(.*?)endbfrange', stream, re.S):
        blk = m.group(1)
        for mm in re.finditer(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<([0-9A-Fa-f]+)>|\[(.*?)\])', blk, re.S):
            lo = int(mm.group(1), 16); hi = int(mm.group(2), 16)
            if mm.group(4):
                base = int(mm.group(4), 16)
                for i in range(hi - lo + 1):
                    cmap[lo + i] = chr(base + i) if base + i < 0x110000 else ''
            else:
                items = re.findall(rb'<([0-9A-Fa-f]+)>', mm.group(5) or b'')
                for i, h in enumerate(items):
                    if lo + i > hi:
                        break
                    cmap[lo + i] = bytes.fromhex(h.decode()).decode('utf-16-be', 'ignore')
    return cmap

def font_cmaps_inline(objs, head):
    m = re.search(rb'/Resources\s*<<', head)
    if not m:
        return {}
    # find matching >> for Resources
    start = m.end() - 2
    depth = 0
    end = None
    for i in range(start, len(head)):
        if head[i:i + 2] == b'<<':
            depth += 1
        elif head[i:i + 2] == b'>>':
            depth -= 1
            if depth == 0:
                end = i + 2
                break
    if end is None:
        return {}
    fm = re.search(rb'/Font\s*<<', head[start:end])
    if not fm:
        return {}
    fstart = start + fm.end() - 2
    depth = 0
    fend = None
    for i in range(fstart, len(head)):
        if head[i:i + 2] == b'<<':
            depth += 1
        elif head[i:i + 2] == b'>>':
            depth -= 1
            if depth == 0:
                fend = i + 2
                break
    out = {}
    for mm in re.finditer(rb'/([A-Za-z0-9_#\.\-\+]+)\s+(\d+)\s+\d+\s+R', head[fstart:fend]):
        name = mm.group(1).decode('latin-1')
        fnum = int(mm.group(2))
        out[name] = _cmap_of(objs, fnum)
    return out

def _cmap_of(objs, fnum):
    if fnum not in objs:
        return {}
    fhead = objs[fnum]['head']
    tu = get_ref(fhead, rb'/ToUnicode')
    if tu is None:
        for dm in re.finditer(rb'/DescendantFonts\s*\[\s*(\d+)\s+\d+\s+R', fhead):
            dn = int(dm.group(1))
            if dn in objs:
                tu = get_ref(objs[dn]['head'], rb'/ToUnicode')
                if tu:
                    break
    if tu and tu in objs and objs[tu]['stream']:
        return parse_cmap(objs[tu]['stream'])
    return {}

def font_cmaps(objs, resnum):
    """resnum: object number of /Resources dict"""
    fonts = {}
    if resnum is None or resnum not in objs:
        return fonts
    head = objs[resnum]['head']
    fm = re.search(rb'/Font\s*<<(.*?)>>', head, re.S)
    if not fm:
        fm = re.search(rb'/Font\s*(\d+)\s+\d+\s+R', head)
        if fm:
            r = int(fm.group(1))
            if r in objs:
                fm = re.search(rb'<<(.*)>>', objs[r]['head'], re.S)
            else:
                fm = None
        else:
            fm = None
    if not fm:
        return fonts
    body = fm.group(1) if fm.lastindex else fm.group(0)
    for m in re.finditer(rb'/([A-Za-z0-9_#\.\-\+]+)\s+(\d+)\s+\d+\s+R', body):
        name = m.group(1).decode('latin-1')
        fnum = int(m.group(2))
        cmap = {}
        if fnum in objs:
            fhead = objs[fnum]['head']
            tu = get_ref(fhead, rb'/ToUnicode')
            if tu is None:
                for dm in re.finditer(rb'/DescendantFonts\s*\[\s*(\d+)\s+\d+\s+R', fhead):
                    dn = int(dm.group(1))
                    if dn in objs:
                        tu = get_ref(objs[dn]['head'], rb'/ToUnicode')
                        if tu:
                            break
            if tu and tu in objs and objs[tu]['stream']:
                cmap = parse_cmap(objs[tu]['stream'])
        fonts[name] = cmap
    return fonts

TOKEN = re.compile(rb'''
    (?P<str>\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]*>)
  | (?P<arr>\[|\])
  | (?P<name>/[A-Za-z0-9#\.\-\+]*)
  | (?P<num>-?\d+\.?\d*)
  | (?P<op>[A-Za-z'"]+)
''', re.X | re.S)

def unescape(b):
    b = re.sub(rb'\\([nrtbf])', lambda x: {b'n': b'\n', b'r': b'\r', b't': b'\t', b'b': b'', b'f': b''}[x.group(1)], b)
    return b.replace(b'\\(', b'(').replace(b'\\)', b')').replace(b'\\\\', b'\\')

def decode_string(tok, cmap):
    if tok.startswith(b'('):
        raw = unescape(tok[1:-1])
        if cmap:
            out = []
            for i in range(0, len(raw), 2):
                code = (raw[i] << 8) | raw[i + 1] if i + 1 < len(raw) else raw[i]
                out.append(cmap.get(code, ''))
            s = ''.join(out)
            if s.strip():
                return s
        return raw.decode('latin-1')
    hx = re.sub(rb'\s', b'', tok[1:-1])
    raw = bytes.fromhex(hx.decode('latin-1'))
    if cmap:
        out = []
        for i in range(0, len(raw) - 1, 2):
            out.append(cmap.get((raw[i] << 8) | raw[i + 1], ''))
        return ''.join(out)
    try:
        return raw.decode('utf-16-be')
    except Exception:
        return raw.decode('latin-1', 'ignore')

def content_stream(objs, pnum):
    head = objs[pnum]['head']
    cm = get_ref(head, rb'/Contents')
    out = b''
    if cm:
        if cm in objs and objs[cm]['stream']:
            out += objs[cm]['stream']
        elif cm in objs and re.search(rb'/Type\s*/ObjStm', objs[cm]['head']):
            pass
    am = re.search(rb'/Contents\s*\[(.*?)\]', head, re.S)
    if am:
        for x in re.finditer(rb'(\d+)\s+\d+\s+R', am.group(1)):
            n = int(x.group(1))
            if n in objs and objs[n]['stream']:
                out += objs[n]['stream'] + b'\n'
    return out

def extract_page(objs, pnum):
    head = objs[pnum]['head']
    res = get_ref(head, rb'/Resources')
    if res is None:
        fonts = font_cmaps_inline(objs, head)
    else:
        fonts = font_cmaps(objs, res)
    cs = content_stream(objs, pnum)
    lines = []
    cur = []
    stack = []
    curfont = None
    lasty = None
    for m in TOKEN.finditer(cs):
        kind = m.lastgroup
        tok = m.group(0)
        if kind == 'str':
            s = decode_string(tok, fonts.get(curfont, {}))
            cur.append(s)
        elif kind == 'num':
            stack.append(float(tok))
        elif kind == 'name':
            stack.append(tok[1:].decode('latin-1'))
        elif kind == 'op':
            op = tok.decode('latin-1')
            if op == 'Tf':
                if len(stack) >= 2:
                    curfont = stack[-2]
            elif op == 'Tj':
                pass
            elif op == 'TJ':
                pass
            elif op in ('Td', 'TD', 'Tm', 'T*', 'ET', 'BT', "'", '"', 'TL'):
                if op in ('Td', 'TD', 'Tm', 'T*'):
                    y = None
                    if op == 'Tm' and len(stack) >= 6 and isinstance(stack[-1], float):
                        y = stack[-1]
                    elif op in ('Td', 'TD') and len(stack) >= 2 and isinstance(stack[-1], float):
                        y = stack[-1]
                    if y is not None:
                        if lasty is None or abs(y - lasty) > 2:
                            if cur:
                                lines.append(''.join(cur)); cur = []
                        lasty = y
                    else:
                        if cur:
                            lines.append(''.join(cur)); cur = []
                elif op == 'ET':
                    if cur:
                        lines.append(''.join(cur)); cur = []
                    lasty = None
                stack = []
                if op == 'BT':
                    lasty = None
            else:
                stack = []
        elif kind == 'arr':
            pass
    if cur:
        lines.append(''.join(cur))
    return [l.strip() for l in lines if l.strip()]

def main():
    d = sys.argv[1]
    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    files = sorted(glob.glob(os.path.join(d, '*.pdf')))
    path = files[idx]
    print('USING:', os.path.basename(path))
    data, objs = load(path)
    pages = page_order(objs)
    print('pages:', len(pages))
    out = []
    for i, p in enumerate(pages):
        try:
            lines = extract_page(objs, p)
        except Exception as e:
            lines = ['[ERR %s]' % e]
        out.append('===== PAGE %d =====' % (i + 1))
        out.extend(lines)
    text = '\n'.join(out)
    op = os.path.join(d, 'extract_%d.txt' % idx)
    open(op, 'w', encoding='utf-8').write(text)
    print('written', op, len(text))
    print(text[:2500])

if __name__ == '__main__':
    main()
