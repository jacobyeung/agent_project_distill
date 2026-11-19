S=/project/community/jjyeung/cp4tk_fr/k6tk
ls $S | head -6; ls $S | wc -l
ls -la $S/54/5434c2265b166c943c3a67b94fcecce2ac913e7349f99409826c7cf959dc177f.png $S/7f/7f8b99bfd9565ec8a1b8fad3450c21ee4f62be29c14b5118e55764b53bc739b0.png $S/f2/f25faedce4622416aed654d13ed347ed2a3b1ea0928a5674a80169324c6888cc.png 2>&1 | cut -c1-200
for p in /home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3 /usr/bin/python3; do [ -x $p ] && $p -c "import sys; print(sys.version.split()[0]); import PIL; print('PIL', PIL.__version__)" 2>&1 | tail -2; done
ls /project/community/jjyeung | head -30
ls -d /home/jyeung/*env* /home/jyeung/.venv* /project/community/jjyeung/*env* 2>/dev/null | head
df -h /tmp 2>/dev/null | tail -1
