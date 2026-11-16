W=/scratch/jjyeung/orch_n30/k1_ops3
B=$W/work/partb/build
cd $B && du -sh evidence rh out payload inputs reference manifest_v2 packet 2>&1
du -sh $W/kc 2>&1
echo "--- grep msg in build py"
grep -n "Missing or changed pinned input" $B/*.py 2>&1 | head
echo "--- grep msg in kc"
grep -rn --include=*.py "Missing or changed pinned input" $W/kc 2>&1 | head
echo "--- grep step_400 in CONFIG"
grep -o '.\{200\}step_400/heads.json.\{300\}' $B/packet/CONFIG.json | head -5
echo "--- grep 97a6a3eb in CONFIG count"; grep -o '97a6a3eb[^"]*' $B/packet/CONFIG.json | sort | uniq -c | head -40
echo "--- bundle list grep"
tar tvf $B/packet/d6e92a81.tar | wc -l
tar tvf $B/packet/d6e92a81.tar | grep -i -e heads -e 97a6a3eb | head -20
echo "--- inputs"; ls -la $B/inputs $B/reference $B/manifest_v2 $B/out | head -60
echo "--- report6 head"; head -c 3000 $B/REPORT6.txt
