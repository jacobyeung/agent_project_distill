set -u
echo "== k"; ls -la ~/okit/x/07ca49df/k/ | head -40
echo "== fm head"; zcat ~/okit/x/07ca49df/k/frame_map.jsonl.gz | head -c 1500; echo
echo "== fm lines"; zcat ~/okit/x/07ca49df/k/frame_map.jsonl.gz | wc -l
echo "== fp head"; zcat ~/okit/x/07ca49df/k/frame_plan.json.gz | head -c 2500; echo
echo "== cp4"; ls -la /project/community/jjyeung/cp4tk_fr/ | head -40
echo "== k6tk"; ls /project/community/jjyeung/cp4tk_fr/k6tk | head -20; ls -f /project/community/jjyeung/cp4tk_fr/k6tk | wc -l
echo "== venv"; ls /project/community/jjyeung/cp4tk_fr/venv/bin 2>/dev/null | head; /project/community/jjyeung/cp4tk_fr/venv/bin/python -c 'import cv2,numpy,sys;print(cv2.__version__,numpy.__version__,sys.version)' 2>&1 | tail -2
echo "== df"; df -h /project/community/jjyeung 2>&1 | tail -1
