export TZ=UTC; date -u +%FT%TZ
squeue -u $USER -p general -h -o '%i %j %T %M %l %R'
squeue -u $USER -h -o '%i %j %P %T' | grep -E "^.* jjy_.* general" || true
/usr/bin/python3 -I -s -B -c "from pathlib import Path;print('POOL_MB',round(sum(p.stat().st_size for p in Path('/project/community/jjyeung/okh7/ae71c903').rglob('*') if p.is_file())/1e6,1))"
