#!/usr/bin/env python3
"""Compare two 8086 COM images, accepting only equivalent short-form
encodings: MASM `op AX,imm16` (05/0D/15/1D/25/2D/35/3D iw) versus
JWasm `83 /r AX,simm8` (83 C0+r ib).  Same length, same semantics.
Also accepts the final EVEN pad byte (90h vs 00h)."""
import sys
a = open(sys.argv[1], 'rb').read()   # new build
b = open(sys.argv[2], 'rb').read()   # reference
if len(a) != len(b):
    sys.exit(f"size differs: {len(a)} vs {len(b)}")
i = n_equiv = 0
bad = []
while i < len(a):
    if a[i] == b[i]:
        i += 1
        continue
    # a: 83 C0+r ib   b: (r*8+5) iw   with ib sign-extended == iw
    if i == len(a) - 1 and a[i] == 0x00 and b[i] == 0x90:
        # trailing EVEN pad: MASM fills with NOP, JWasm with 0
        n_equiv += 1
        i += 1
        continue
    if (a[i] == 0x83 and (a[i+1] & 0xC7) == 0xC0 and
        b[i] == ((a[i+1] >> 3) & 7) * 8 + 5 and
        int.from_bytes(b[i+1:i+3], 'little') ==
        (a[i+2] | (0xFF00 if a[i+2] & 0x80 else 0))):
        n_equiv += 1
        i += 3
        continue
    bad.append(i)
    i += 1
print(f"equivalent-encoding sites: {n_equiv}, unexplained bytes: {len(bad)}")
for o in bad[:20]:
    print(f"  {o+0x100:05X}: new {a[o]:02X} ref {b[o]:02X}")
sys.exit(1 if bad else 0)
