export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep -E "d1efc29326c7" && { echo QUEUED; exit 1; }
python3 -c "import json;[print(k, {a:b for a,b in json.load(open(\"$X/\"+k+\"/k/a.json\")).items() if \"go\" in a.lower()}) for k in (\"q\",\"n\",\"qd\")]"
cd $X/qd && [ "$(sha256sum SHA256SUMS.txt | cut -c1-16)" = 259c14de1ff04938 ] && [ "$(sha256sum $X/rcj/rcj.sh | cut -c1-8)" = "f97837e4" ] && [ "$(sha256sum $X/rcj/x.py | cut -c1-8)" = "16be8a21" ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && [ -z "$(find . -name __pycache__)" ] && sbatch --job-name=a15_cot_apd1efc29326c7 $X/rcj/rcj.sh; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %.12b %R"
