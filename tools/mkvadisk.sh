#!/bin/sh
# Make the PC-88VA install disk FDImage/VZ_VA.D88 from build/VA/VZVA.COM.
set -e
top=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp "$top/build/VA/VZVA.COM" "$top/FDImage/VA/VZVA.DOC" "$work/"
sed 's/$/\r/' "$top/LICENSE" > "$work/LICENSE.TXT"
for f in VZ.DEF VZFL.DEF BLOCK.DEF CVTKEI.DEF GAME.DEF HELP.DEF KEISEN.DEF \
         KEISEN_J.DEF TOOL.DEF VZ16.DEF ZENHAN.DEF README.DOC VZ16.DOC MAC16.DOC; do
  cp "$top/VZ-PC98/$f" "$work/"
done
cd "$work"
python3 "$top/tools/mkdisk.py" "$top/FDImage/VZ_VA.D88" VZVA160 \
  VZVA.COM VZVA.DOC VZ.DEF VZFL.DEF BLOCK.DEF CVTKEI.DEF GAME.DEF HELP.DEF \
  KEISEN.DEF KEISEN_J.DEF TOOL.DEF VZ16.DEF ZENHAN.DEF \
  README.DOC VZ16.DOC MAC16.DOC LICENSE.TXT
ls -l "$top/FDImage/VZ_VA.D88"
