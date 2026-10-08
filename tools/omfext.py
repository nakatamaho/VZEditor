#!/usr/bin/env python3
"""Find EXTRN declarations that no module defines.

MASM 5.1 omits EXTDEF records for EXTRN symbols that a module never
references; JWasm emits them, so JWlink reports them as undefined.  This
script reads the OMF objects, and prints (one per line) the names that are
declared EXTRN somewhere, defined nowhere and never referenced by a fixup.
The build turns them into zero-size stubs.  An undefined symbol that *is*
referenced is a real error: it is reported on stderr and the exit status
is 1.

usage: omfext.py file.obj ...
"""
import sys


def records(data):
    pos = 0
    while pos + 3 <= len(data):
        rtype = data[pos]
        length = data[pos + 1] | data[pos + 2] << 8
        yield rtype, data[pos + 3:pos + 3 + length - 1]   # drop checksum
        pos += 3 + length


def index(buf, pos):
    if buf[pos] & 0x80:
        return (buf[pos] & 0x7F) << 8 | buf[pos + 1], pos + 2
    return buf[pos], pos + 1


def scan(path, publics):
    """Return (extdef names, set of referenced extdef indices)."""
    exts, used = [], set()
    data = open(path, 'rb').read()
    for rtype, rec in records(data):
        if rtype in (0x8C, 0xB4):                   # EXTDEF, LEXTDEF
            pos = 0
            while pos < len(rec):
                n = rec[pos]
                exts.append(rec[pos + 1:pos + 1 + n].decode('latin-1'))
                pos += 1 + n
                _, pos = index(rec, pos)            # type index
        elif rtype in (0x90, 0x91, 0xB6, 0xB7):     # PUBDEF, LPUBDEF
            wide = rtype & 1
            pos = 0
            _, pos = index(rec, pos)                # group
            seg, pos = index(rec, pos)
            if seg == 0:
                pos += 2                            # frame number
            while pos < len(rec):
                n = rec[pos]
                publics.add(rec[pos + 1:pos + 1 + n].decode('latin-1'))
                pos += 1 + n + (4 if wide else 2)
                _, pos = index(rec, pos)
        elif rtype in (0x9C, 0x9D):                 # FIXUPP
            wide = rtype & 1
            pos = 0
            while pos < len(rec):
                b = rec[pos]
                if not b & 0x80:                    # THREAD subrecord
                    method = (b >> 2) & 7
                    pos += 1
                    if b & 0x40:                    # frame thread
                        if method < 3:
                            idx, pos = index(rec, pos)
                            if method == 2:
                                used.add(idx)
                    else:                           # target thread
                        idx, pos = index(rec, pos)
                        if method & 3 == 2:
                            used.add(idx)
                    continue
                pos += 2                            # locat
                fixdat = rec[pos]
                pos += 1
                if not fixdat & 0x80:               # explicit frame
                    fmethod = (fixdat >> 4) & 7
                    if fmethod < 3:
                        idx, pos = index(rec, pos)
                        if fmethod == 2:
                            used.add(idx)
                if not fixdat & 0x08:               # explicit target
                    tmethod = fixdat & 3
                    idx, pos = index(rec, pos)
                    if tmethod == 2:
                        used.add(idx)
                if not fixdat & 0x04:               # displacement present
                    pos += 4 if wide else 2
        elif rtype in (0x8A, 0x8B) and rec and rec[0] & 0x40:   # MODEND
            fixdat = rec[1]
            pos = 2
            if not fixdat & 0x80 and ((fixdat >> 4) & 7) < 3:
                idx, pos = index(rec, pos)
                if ((fixdat >> 4) & 7) == 2:
                    used.add(idx)
            if not fixdat & 0x08:
                idx, pos = index(rec, pos)
                if fixdat & 3 == 2:
                    used.add(idx)
    return exts, used


def main(paths):
    publics = set()
    modules = [(p, *scan(p, publics)) for p in paths]
    stubs, bad = set(), []
    for path, exts, used in modules:
        for i, name in enumerate(exts, 1):
            if name in publics:
                continue
            if i in used:
                bad.append(f"{path}: undefined symbol {name}")
            else:
                stubs.add(name)
    for line in bad:
        print(line, file=sys.stderr)
    for name in sorted(stubs):
        print(name)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
