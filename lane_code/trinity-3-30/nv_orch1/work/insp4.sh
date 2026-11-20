cd /project/community/jjyeung/b9ef552934627
tar tzvf 0.tgz | head -40
tar xzf 0.tgz -O 9.json 2>/dev/null | head -c 3000; echo
tar xzf 0.tgz -O 8.py 2>/dev/null | grep -n -i "frame\|/project\|tgz\|tar\|d/f" | head -40
cat a/export.json | head -c 1500; echo
