#!/bin/sh
# Run files under PC-Engine 1.1 in the vaeg emulator, headless.
# usage: tools/va-run.sh <payload-dir> <input-script> <frame> <out.png> [extra vaeg args]
# env:   VAEG (emulator binary), VA_ROMS (ROM dir), PCENGINE_D88 (system disk)
# The files in <payload-dir> are copied into the root of a disposable
# vanilla copy of the system disk.
set -e
payload=$1 script=$2 frame=$3 png=$4
shift 4
disktool=${PCENGINE_DISK_PY:-$(dirname "$VAEG")/../../../tools/pc88va/pcengine_disk.py}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/payload/root"
cp "$payload"/* "$work/payload/root/"
python3 -I "$disktool" vanilla --source "$PCENGINE_D88" --output "$work/disk.d88" >/dev/null
python3 -I "$disktool" install --image "$work/disk.d88" --payload "$work/payload" >/dev/null
timeout 600 "$VAEG" --model va --no-cfg --no-bkupmem --roms "$VA_ROMS" \
  --fdd1 "$work/disk.d88" --nowait --headless-input-script "$script" \
  --screenshot "$frame:$png" "$@" >"$work/log" 2>&1 || { cat "$work/log"; exit 1; }
[ -n "$KEEP_DISK" ] && cp "$work/disk.d88" "$KEEP_DISK"
exit 0
