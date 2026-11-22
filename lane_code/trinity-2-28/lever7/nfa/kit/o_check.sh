#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/c8b836b4ae536
test -e "$P/PACKAGE.json"
test ! -e "$P/2.json"
cd "$P" && /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00 > /dev/null
/usr/bin/python3 -I -s -B -c 'import json,sys;v=json.load(open(sys.argv[1]));print(v["passed"],v["gpus"],v["time"])' "$P/2.json"
