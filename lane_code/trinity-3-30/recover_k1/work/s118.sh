set -u
echo "host=$(hostname -s) $(date -u +%FT%TZ)" >&2
K=/scratch/jjyeung/orch_n30/k1_ops3/kc
S=/scratch/jjyeung/orch_cd/grd_selector/work/setsel
LISTV=""
for d in $K /scratch/jjyeung/orch_cd/grd_selector /scratch/jjyeung/orch_cd/devs1_masks /scratch/jjyeung/mask_recall_run /scratch/jjyeung/devs1_mask_run /scratch/jjyeung/k1 /scratch/jjyeung/own_ground_gpu /scratch/jjyeung/geo_bakeoff_kit /scratch/jjyeung/orch_n30/k1_ops3/work; do
  [ -d $d ] || { echo "MISSING $d" >&2; continue; }
  echo "== $d $(timeout 60 find $d -type f 2>/dev/null | wc -l) files" >&2
  timeout 90 find $d \( -iname 'MODELS*.json' -o -name 'setlib*.py' -o -iname '*.pkl' -o -iname '*.joblib' -o -iname 'requirements*' -o -iname '*sklearn*' -o -iname '*kit*.tar*' -o -iname 'DEPENDENCIES.json' -o -path '*refit*' -name '*.py' \) -type f -printf '%s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null | head -300 >&2
  LISTV="$LISTV$(timeout 90 find $d \( -iname 'MODELS*.json' -o -name 'setlib*.py' -o -iname '*.pkl' -o -iname 'requirements*' -o -iname 'DEPENDENCIES.json' -o -path '*refit*' -name '*.py' \) -type f -size -5M 2>/dev/null | head -100)
"
done
ls $S/ >&2
LISTV="$LISTV$S/build.py
$S/fit.py
$S/fit_pairs.py"
LISTV=$(printf '%s\n' "$LISTV" | sed '/^$/d' | sort -u)
echo "== sha256 of picked files" >&2
printf '%s\n' "$LISTV" | xargs -d '\n' sha256sum >&2
echo "== envs" >&2
for p in /scratch/jjyeung/envs/*/bin/python /scratch/jjyeung/*/env*/bin/python; do [ -x "$p" ] && echo "$p $(timeout 30 $p -c 'import sklearn;print(sklearn.__version__)' 2>&1 | tail -1)" >&2; done
printf '%s\n' "$LISTV" | tar cf - -T - 2>/dev/null
