#!/bin/sh
# Build VZ Editor with JWasm + JWlink on a Unix host.
# usage: tools/build.sh <target>   target: 98 | VA
# env:   JWASM_BIN, JWLINK_BIN  (paths to the binaries; JWASM itself is
#        read by jwasm as an option variable, so it is not used here)
set -e
target=${1:-98}
top=$(cd "$(dirname "$0")/.." && pwd)
JWASM_BIN=${JWASM_BIN:-jwasm}
JWLINK_BIN=${JWLINK_BIN:-jwlink}
case $target in
  98) def=-DPC98; out=VZ.COM ;;
  VA) def=-DPC88VA; out=VZVA.COM ;;
  *)  echo "unknown target $target" >&2; exit 2 ;;
esac
bld=$top/build/$target
rm -rf "$bld"; mkdir -p "$bld"; cd "$bld"
# sources include each other in lower case; DOS is case-insensitive
for f in "$top"/SRC/*; do ln -s "$f" "$(basename "$f" | tr A-Z a-z)"; done
mods=$(tr -d '+\r\032' < vz.lnk | sed '/^$/d')
objs=
for m in $mods; do
  "$JWASM_BIN" -q -Zm -Cp $def -Fo=$m.obj -Fl=$m.lst $m.asm || exit 1
  objs=$objs${objs:+,}$m.obj
done
# zero-size stubs for EXTRNs that no module defines nor references
names=$(python3 "$top/tools/omfext.py" $(echo $objs | tr , ' '))
{
  echo "_undefs segment byte public 'TAIL'"
  for n in $names; do printf '\tpublic\t%s\n%s\tlabel\tbyte\n' $n $n; done
  echo "_undefs ends"
  printf '\tend\n'
} > undefs.asm
"$JWASM_BIN" -q -Cp -Foundefs.obj undefs.asm
"$JWLINK_BIN" format dos com file $objs,undefs.obj name vz.bin \
  option map=vz.map,quiet >link.log 2>&1 || { cat link.log; exit 1; }
# JWlink keeps the 100h bytes in front of ORG 100h; strip them like EXE2BIN
tail -c +257 vz.bin > $out
ls -l "$bld/$out"
