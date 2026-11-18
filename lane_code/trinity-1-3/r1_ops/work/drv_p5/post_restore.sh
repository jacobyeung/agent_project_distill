export TZ=UTC
set -euo pipefail
KH=/project/community/jjyeung/okh7/x_69d2930d
[[ "$(sha256sum $KH/k/4.json | cut -d' ' -f1)" == 2f450bfaa65e6ae0dcfbd1c790fdeb374b9356a9d2b48f5f4ba9835f127d2353 ]] || { echo 'REFUSED: authority not restored'; exit 3; }
[[ ! -e $KH/b/__pycache__ ]] || { echo 'REFUSED: pycache present in KH/b'; exit 3; }
find $KH/b -name __pycache__ | grep -q . && { echo 'REFUSED: nested pycache'; exit 3; } || true
chmod 700 $KH/b; find $KH/b -type d -exec chmod 700 {} +
stat -c '%a %n' $KH/b
cd $KH && /usr/bin/python3 -B b/a.py "$KH" && echo 'PASS a.py inventory'
[[ ! -e $KH/b/__pycache__ ]] && echo 'PASS no pycache after a.py'
scontrol release 171356; echo release rc=$?
squeue -h -j 171356 -o '%i|%T|%R'
