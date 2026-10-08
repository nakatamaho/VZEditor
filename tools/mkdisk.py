#!/usr/bin/env python3
"""Make a PC-98 MS-DOS format 2HD D88 image (1024 bytes x 8 sectors x
2 heads x 77 cylinders, FAT12) holding the given files in its root.

The image is built from scratch, so it contains no system files and its
boot sector only holds a BPB.  PC-Engine reads this format.

usage: mkdisk.py output.d88 label file...
"""
import struct
import sys
import os

SECTOR = 1024
SECTORS = 8
HEADS = 2
CYLINDERS = 77
TOTAL = SECTORS * HEADS * CYLINDERS        # 1232
FAT_SECTORS = 2
ROOT_ENTRIES = 192
ROOT_SECTORS = ROOT_ENTRIES * 32 // SECTOR
DATA_START = 1 + 2 * FAT_SECTORS + ROOT_SECTORS
CLUSTERS = TOTAL - DATA_START
DATE = ((2026 - 1980) << 9) | (10 << 5) | 8   # fixed: reproducible image
TIME = 0


def boot_sector(label):
    b = bytearray(SECTOR)
    b[0:3] = b'\xeb\x1c\x90'
    b[3:11] = label.encode('ascii')[:8].ljust(8)
    struct.pack_into('<HBHBHHBHHHL', b, 11, SECTOR, 1, 1, 2, ROOT_ENTRIES,
                     TOTAL, 0xFE, FAT_SECTORS, SECTORS, HEADS, 0)
    b[0x1E:0x20] = b'\xeb\xfe'                # not bootable: stop
    return b


def short_name(path):
    base, _, ext = os.path.basename(path).upper().partition('.')
    if not base or len(base) > 8 or len(ext) > 3:
        sys.exit(f'not an 8.3 name: {path}')
    return (base.ljust(8) + ext.ljust(3)).encode('ascii')


def main(out, label, files):
    data = bytearray(TOTAL * SECTOR)
    data[0:SECTOR] = boot_sector(label)
    fat = [0] * (CLUSTERS + 2)
    fat[0], fat[1] = 0xFFE, 0xFFF
    root = bytearray(ROOT_SECTORS * SECTOR)
    vol = label.encode('ascii')[:11].ljust(11)
    root[0:32] = vol + bytes([0x08]) + bytes(10) + struct.pack('<HHHL', TIME, DATE, 0, 0)
    cluster = 2
    for i, path in enumerate(files, 1):
        body = open(path, 'rb').read()
        n = (len(body) + SECTOR - 1) // SECTOR
        if cluster + n > CLUSTERS + 2:
            sys.exit('disk full')
        first = cluster if n else 0
        for k in range(n):
            fat[cluster + k] = cluster + k + 1 if k < n - 1 else 0xFFF
            lba = DATA_START + cluster + k - 2
            chunk = body[k * SECTOR:(k + 1) * SECTOR]
            data[lba * SECTOR:lba * SECTOR + len(chunk)] = chunk
        cluster += n
        root[i * 32:i * 32 + 32] = (short_name(path) + bytes([0x20]) + bytes(10)
                                    + struct.pack('<HHHL', TIME, DATE, first, len(body)))
    packed = bytearray(FAT_SECTORS * SECTOR)
    for c in range(0, len(fat) - 1, 2):
        v = fat[c] | fat[c + 1] << 12
        packed[c * 3 // 2:c * 3 // 2 + 3] = v.to_bytes(3, 'little')
    for f in range(2):
        o = (1 + f * FAT_SECTORS) * SECTOR
        data[o:o + len(packed)] = packed
    o = (1 + 2 * FAT_SECTORS) * SECTOR
    data[o:o + len(root)] = root

    # D88 container
    tracks = CYLINDERS * HEADS
    header = bytearray(0x2B0)
    header[0:17] = label.encode('ascii')[:16].ljust(17, b'\0')
    header[0x1B] = 0x20                       # 2HD
    pos = 0x2B0
    body = bytearray()
    for t in range(tracks):
        struct.pack_into('<L', header, 0x20 + 4 * t, pos + len(body))
        c, h = divmod(t, HEADS)
        for r in range(1, SECTORS + 1):
            body += struct.pack('<BBBBHBBB5xH', c, h, r, 3, SECTORS, 0, 0, 0, SECTOR)
            lba = t * SECTORS + r - 1
            body += data[lba * SECTOR:(lba + 1) * SECTOR]
    struct.pack_into('<L', header, 0x1C, 0x2B0 + len(body))
    open(out, 'wb').write(header + body)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
