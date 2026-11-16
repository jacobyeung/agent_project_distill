K=/scratch/jjyeung/geo_bakeoff_kit
ls -la $K/assets/da3 $K/assets/moge2 $K/assets/pi3x; du -sh $K/runtime/base/* | sort -h | tail -6; du -sh $K/runtime/base/lib/python3*/site-packages/* 2>/dev/null | sort -h | tail -8
grep -n "da3\|DA3" $K/work/geo_bakeoff/backends.py | head -20
